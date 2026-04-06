"""
psd_parser.py
─────────────
PSD 파일을 파싱하여 레이어 정보 추출.
psd-tools 없이 순수 Python으로 구현.
"""

import struct, io, base64
from PIL import Image


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _read_pascal_str(data, pos, pad=4):
    length = data[pos]; pos += 1
    name_b = data[pos:pos+length]; pos += length
    total = 1 + length
    rem = total % pad
    if rem: pos += pad - rem
    for enc in ['utf-8','cp949','latin-1']:
        try: return name_b.decode(enc), pos
        except: pass
    return name_b.decode('latin-1','replace'), pos


def _extract_text_from_tysh(data, tysh_offset):
    """TySh 블록 오프셋에서 텍스트 추출."""
    block_len = struct.unpack('>I', data[tysh_offset-4:tysh_offset])[0]
    block = data[tysh_offset:tysh_offset+block_len]
    marker = b'/Text ('
    ti = block.find(marker)
    if ti < 0:
        return ''
    p = ti + len(marker)
    if block[p:p+2] != b'\xfe\xff':
        return ''
    p += 2
    chars = []
    while p + 1 < len(block):
        hi, lo = block[p], block[p+1]
        code = (hi << 8) | lo
        if code == 0x0029: break          # ')'
        if code == 0x000D: chars.append('\n')
        elif 0x0020 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD:
            c = chr(code)
            if c.isprintable() or c == '\n':
                chars.append(c)
        p += 2
    text = ''.join(chars).strip()
    # 첫 줄이 너무 짧거나 깨지면 빈 문자열
    first = text.split('\n')[0]
    if len(first) < 1 or len(first) > 300:
        return ''
    # 깨진 문자(non-CJK/latin 이외) 비율 체크
    clean_chars = [c for c in first if c.isalpha() or c.isdigit() or c in ' .,!?-_()[]']
    if len(clean_chars) < len(first) * 0.3 and len(first) > 5:
        return ''
    return text


def _decode_rle_row(data, pos, width):
    """PackBits RLE 한 행 디코딩."""
    result = []
    while len(result) < width:
        if pos >= len(data): break
        header = struct.unpack('b', data[pos:pos+1])[0]; pos += 1
        if header >= 0:
            n = header + 1
            result.extend(data[pos:pos+n]); pos += n
        elif header != -128:
            n = 1 - header
            val = data[pos]; pos += 1
            result.extend([val] * n)
    return bytes(result[:width]), pos


def _extract_layer_thumbnail(data, layer_info, psd_data):
    """
    레이어 픽셀 데이터를 PIL Image로 추출.
    레이어 섹션 내 픽셀 데이터 오프셋 필요 → layer_info에 pixel_data_offset 포함.
    """
    if layer_info.get('pixel_data_offset') is None:
        return None
    try:
        W = layer_info['w']
        H = layer_info['h']
        if W <= 0 or H <= 0 or W * H > 4000 * 4000:
            return None

        pos = layer_info['pixel_data_offset']
        num_ch = layer_info['num_channels']

        channels = {}
        for ch_id, ch_len in layer_info['channel_info']:
            if pos + ch_len > len(psd_data): break
            ch_data = psd_data[pos:pos+ch_len]; pos += ch_len
            compression = struct.unpack('>H', ch_data[0:2])[0]
            if compression == 0:  # Raw
                pixels = ch_data[2:2+W*H]
            elif compression == 1:  # RLE
                row_counts = []
                p2 = 2
                for _ in range(H):
                    row_counts.append(struct.unpack('>H', ch_data[p2:p2+2])[0])
                    p2 += 2
                pixels = bytearray()
                for rc in row_counts:
                    row, p2 = _decode_rle_row(ch_data, p2, W)
                    pixels.extend(row)
            else:
                continue
            channels[ch_id] = bytes(pixels[:W*H])

        if 0 in channels and 1 in channels and 2 in channels:
            r = Image.frombytes('L', (W,H), channels[0])
            g = Image.frombytes('L', (W,H), channels[1])
            b = Image.frombytes('L', (W,H), channels[2])
            img = Image.merge('RGB', (r,g,b))
            if -1 in channels:
                a = Image.frombytes('L', (W,H), channels[-1])
                img.putalpha(a)
            return img
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────

def parse_psd(psd_bytes: bytes) -> dict:
    """
    PSD 바이너리를 파싱하여 레이어 구조 반환.

    반환:
    {
      'width': int, 'height': int, 'depth': int, 'color_mode': str,
      'layers': [
        {
          'idx': int,
          'name': str,
          'type': 'pixel' | 'text' | 'group_open' | 'group_close',
          'rect': (top, left, bottom, right),
          'w': int, 'h': int,
          'opacity': int (0-255),
          'visible': bool,
          'text': str (텍스트 레이어만),
          'channel_info': [(ch_id, ch_len), ...],
          'pixel_data_offset': int (픽셀 레이어),
        }, ...
      ],
      'raw': bytes  # 원본 바이너리 (교체용)
    }
    """
    data = psd_bytes
    pos = 0

    # 헤더
    assert data[0:4] == b'8BPS', "PSD 파일이 아닙니다"
    version = struct.unpack('>H', data[4:6])[0]
    n_ch    = struct.unpack('>H', data[12:14])[0]
    height  = struct.unpack('>I', data[14:18])[0]
    width   = struct.unpack('>I', data[18:22])[0]
    depth   = struct.unpack('>H', data[22:24])[0]
    mode    = struct.unpack('>H', data[24:26])[0]
    mode_name = {1:'Grayscale',3:'RGB',4:'CMYK',9:'Lab'}.get(mode, f'Unknown({mode})')
    pos = 26

    color_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+color_len
    res_len   = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+res_len

    layer_sec_start_outer = pos
    layer_sec_len  = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4
    layer_info_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4
    layer_info_start = pos

    num_layers_raw = struct.unpack('>h', data[pos:pos+2])[0]; pos += 2
    num_layers = abs(num_layers_raw)

    layers = []
    for li in range(num_layers):
        top    = struct.unpack('>i', data[pos:pos+4])[0]; pos += 4
        left   = struct.unpack('>i', data[pos:pos+4])[0]; pos += 4
        bottom = struct.unpack('>i', data[pos:pos+4])[0]; pos += 4
        right  = struct.unpack('>i', data[pos:pos+4])[0]; pos += 4
        num_ch = struct.unpack('>H', data[pos:pos+2])[0]; pos += 2

        ch_info = []
        for _ in range(num_ch):
            ch_id  = struct.unpack('>h', data[pos:pos+2])[0]
            ch_len = struct.unpack('>I', data[pos+2:pos+6])[0]
            ch_info.append((ch_id, ch_len)); pos += 6

        pos += 4  # blend sig
        blend_mode = data[pos:pos+4].decode('ascii','replace'); pos += 4
        opacity = data[pos]; pos += 1
        clipping = data[pos]; pos += 1
        flags = data[pos]; pos += 1
        pos += 1  # filler

        extra_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4
        extra_start = pos

        mask_len  = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+mask_len
        blend_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+blend_len
        layer_name, pos = _read_pascal_str(data, pos, 4)

        layer_type  = 'pixel'
        tysh_offset = None
        unicode_name = None
        text_content = ''

        extra_end = extra_start + extra_len
        while pos < extra_end - 7:
            if data[pos:pos+4] not in (b'8BIM', b'8B64'): break
            pos += 4
            key = data[pos:pos+4]; pos += 4
            add_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4

            if key == b'TySh':
                layer_type  = 'text'
                tysh_offset = pos
                text_content = _extract_text_from_tysh(data, pos)
            elif key == b'lsct':
                st = struct.unpack('>I', data[pos:pos+4])[0] if add_len >= 4 else 0
                layer_type = 'group_open' if st in (1,2) else ('group_close' if st==3 else layer_type)
            elif key == b'luni':
                ulen = struct.unpack('>I', data[pos:pos+4])[0]
                try: unicode_name = data[pos+4:pos+4+ulen*2].decode('utf-16-be')
                except: pass

            pos += add_len
            if add_len % 4: pos += 4 - (add_len%4)
        pos = extra_end

        name = unicode_name or layer_name
        layers.append({
            'idx': li, 'name': name, 'type': layer_type,
            'rect': (top, left, bottom, right),
            'w': right-left, 'h': bottom-top,
            'opacity': opacity, 'visible': not bool(flags & 2),
            'blend_mode': blend_mode,
            'text': text_content,
            'channel_info': ch_info,
            'num_channels': num_ch,
            'tysh_offset': tysh_offset,
            'pixel_data_offset': None,  # 아래에서 채움
        })

    # 픽셀 데이터 오프셋 계산 (레코드 끝 = 픽셀 데이터 시작)
    pixel_data_pos = pos  # 현재 pos = 레코드 끝, 픽셀 데이터 시작
    for layer in layers:
        layer['pixel_data_offset'] = pixel_data_pos
        for ch_id, ch_len in layer['channel_info']:
            pixel_data_pos += ch_len

    return {
        'width': width, 'height': height, 'depth': depth,
        'color_mode': mode_name, 'num_layers': num_layers,
        'layers': layers, 'raw': psd_bytes,
        'layer_info_start': layer_info_start,
        'layer_info_len': layer_info_len,
    }


def get_layer_thumbnail(psd_info: dict, layer_idx: int, max_size: int = 300) -> bytes | None:
    """레이어 픽셀 데이터를 썸네일 JPEG로 반환."""
    layer = next((l for l in psd_info['layers'] if l['idx'] == layer_idx), None)
    if not layer or layer['type'] != 'pixel': return None
    img = _extract_layer_thumbnail(None, layer, psd_info['raw'])
    if img is None: return None
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert('RGB').save(buf, 'JPEG', quality=82)
    return buf.getvalue()


def replace_text_in_psd(psd_bytes: bytes, replacements: dict) -> bytes:
    """
    텍스트 레이어 내용 교체.
    replacements: {layer_idx: new_text}
    방식: /Text (원본) → /Text (새텍스트) 바이트 교체
    """
    data = bytearray(psd_bytes)

    for layer_idx, new_text in replacements.items():
        # /Text ( 위치 찾기 (레이어 순서대로)
        marker = b'/Text ('
        search_start = 0
        occurrence = 0
        target_occurrence = layer_idx  # 대략적 인덱스

        pos = 0
        found_positions = []
        while pos < len(data) - 8:
            if bytes(data[pos:pos+7]) == marker and data[pos+7:pos+9] == b'\xfe\xff':
                found_positions.append(pos)
            pos += 1

        if layer_idx >= len(found_positions):
            continue

        fp = found_positions[layer_idx]
        p  = fp + 7  # marker 이후
        # BOM 건너뜀
        p += 2  # \xfe\xff

        # 원본 텍스트 끝 찾기
        end = p
        while end + 1 < len(data):
            code = (data[end] << 8) | data[end+1]
            if code == 0x0029: break  # ')'
            end += 2

        # 새 텍스트 UTF-16BE 인코딩
        new_utf16 = new_text.encode('utf-16-be')
        # 줄바꿈 \n → \x00\x0D
        new_utf16 = new_utf16.replace(b'\x00\n', b'\x00\x0D')

        # 교체: BOM(2) + 원본 → BOM(2) + 새텍스트
        old_seg = bytes(data[fp+7:end])  # BOM + 원본
        new_seg = b'\xfe\xff' + new_utf16

        # 데이터 교체
        data[fp+7:end] = new_seg

        # TySh 블록 길이 재조정 필요
        # (단순화: 텍스트가 짧으면 패딩, 길면 확장 - 레이어섹션 재계산)
        # → 이 부분은 복잡하므로 JSX 방식 병행

    return bytes(data)


def psd_to_preview_jpg(psd_bytes: bytes, max_width: int = 800) -> bytes:
    """PSD 병합 이미지(섹션5)를 JPG로 추출."""
    data = psd_bytes
    pos = 26
    color_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+color_len
    res_len   = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+res_len
    layer_sec_len = struct.unpack('>I', data[pos:pos+4])[0]; pos += 4+layer_sec_len
    # 이제 pos = 섹션5(병합 이미지 데이터) 시작
    compression = struct.unpack('>H', data[pos:pos+2])[0]

    W = struct.unpack('>I', data[18:22])[0]
    H = struct.unpack('>I', data[14:18])[0]
    n_ch = struct.unpack('>H', data[12:14])[0]
    depth = struct.unpack('>H', data[22:24])[0]

    if compression == 0:  # Raw
        pos += 2
        ch_size = W * H
        channels = []
        for c in range(min(n_ch, 3)):
            channels.append(data[pos+c*ch_size:pos+(c+1)*ch_size])
        r = Image.frombytes('L', (W,H), channels[0])
        g = Image.frombytes('L', (W,H), channels[1])
        b = Image.frombytes('L', (W,H), channels[2])
        img = Image.merge('RGB', (r,g,b))
    elif compression == 1:  # RLE
        pos += 2
        row_counts = []
        for _ in range(H * n_ch):
            row_counts.append(struct.unpack('>H', data[pos:pos+2])[0]); pos += 2
        channels = [bytearray() for _ in range(n_ch)]
        for c in range(n_ch):
            for row_i in range(H):
                rc = row_counts[c*H + row_i]
                row, pos = _decode_rle_row(data, pos, W)
                channels[c].extend(row)
        r = Image.frombytes('L', (W,H), bytes(channels[0]))
        g = Image.frombytes('L', (W,H), bytes(channels[1]))
        b = Image.frombytes('L', (W,H), bytes(channels[2]))
        img = Image.merge('RGB', (r,g,b))
    else:
        raise ValueError(f"지원하지 않는 압축방식: {compression}")

    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height*ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=88)
    return buf.getvalue()
