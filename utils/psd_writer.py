"""
psd_writer.py
─────────────────────────────────────────────────────────────────
Adobe PSD 포맷을 psd-tools 없이 순수 Python으로 직접 생성.

PSD 구조:
  1. File Header Section
  2. Color Mode Data Section
  3. Image Resources Section
  4. Layer and Mask Information Section
  5. Image Data Section

각 레이어는 독립적인 픽셀 데이터를 가지며
포토샵에서 열면 레이어 패널에 구분되어 표시됨.
"""

import struct
import zlib
import io
from PIL import Image


# ───────────────────────────────────────────────
# 저수준 바이너리 헬퍼
# ───────────────────────────────────────────────

def _pack_str(s: str, length: int) -> bytes:
    """Pascal 문자열 패딩"""
    encoded = s.encode("ascii", errors="replace")[:length]
    return encoded.ljust(length, b"\x00")


def _pascal_string(s: str, pad_to: int = 4) -> bytes:
    """Pascal 문자열 (1바이트 길이 + 데이터 + 패딩)"""
    encoded = s.encode("ascii", errors="replace")[:255]
    length = len(encoded)
    data = bytes([length]) + encoded
    total = len(data)
    remainder = total % pad_to
    if remainder:
        data += b"\x00" * (pad_to - remainder)
    return data


def _compress_rle(row_bytes: bytes) -> bytes:
    """PackBits RLE 압축 (PSD 표준)"""
    src = list(row_bytes)
    out = []
    i = 0
    n = len(src)
    while i < n:
        # 연속 동일 바이트 확인
        if i + 1 < n and src[i] == src[i + 1]:
            j = i + 1
            while j < n - 1 and src[j] == src[j + 1] and j - i < 127:
                j += 1
            count = j - i + 1
            out.append(struct.pack("b", -(count - 1)))
            out.append(bytes([src[i]]))
            i = j + 1
        else:
            j = i
            while j < n - 1 and (j == i or src[j] != src[j + 1]) and j - i < 127:
                j += 1
            if j < n - 1:
                pass
            else:
                j = n - 1
            count = j - i + 1
            out.append(struct.pack("B", count - 1))
            out.append(bytes(src[i:j + 1]))
            i = j + 1
    return b"".join(out)


# ───────────────────────────────────────────────
# PSD 섹션 빌더
# ───────────────────────────────────────────────

def _build_file_header(width: int, height: int, num_channels: int = 3) -> bytes:
    """섹션1: File Header"""
    return struct.pack(">4sHHIHH",
        b"8BPS",   # 시그니처
        1,          # 버전 (1=PSD, 2=PSB)
        0,          # 예약 (6바이트이지만 struct로 2바이트만 — 나머지 별도)
        0,          # 예약 4바이트
        num_channels,
        height,
    ) + struct.pack(">IHH",
        width,      # 주의: 앞서 height, 이후 width 순서
        8,          # bits per channel
        3,          # color mode: RGB
    )
    # 올바른 순서로 재작성


def _build_header(width: int, height: int) -> bytes:
    """PSD File Header Block (26 bytes)"""
    buf = io.BytesIO()
    buf.write(b"8BPS")           # 시그니처
    buf.write(struct.pack(">H", 1))   # 버전
    buf.write(b"\x00" * 6)       # 예약
    buf.write(struct.pack(">H", 3))   # 채널수 (RGB)
    buf.write(struct.pack(">I", height))
    buf.write(struct.pack(">I", width))
    buf.write(struct.pack(">H", 8))   # 채널당 비트
    buf.write(struct.pack(">H", 3))   # 컬러모드: RGB
    return buf.getvalue()


def _build_color_mode_data() -> bytes:
    """섹션2: Color Mode Data (RGB는 0바이트)"""
    return struct.pack(">I", 0)


def _build_image_resources() -> bytes:
    """섹션3: Image Resources (최소 구성)"""
    # 빈 리소스 블록
    return struct.pack(">I", 0)


def _encode_layer_pixels_raw(img_rgba: Image.Image) -> tuple:
    """
    레이어 픽셀을 RLE(PackBits) 압축하여 반환.
    반환: (compression=1, byte_counts_per_row, compressed_data)
    PSD는 RGBA 채널을 R, G, B, A 순서로 분리해서 저장.
    """
    w, h = img_rgba.size
    channels = [
        img_rgba.getchannel("R"),
        img_rgba.getchannel("G"),
        img_rgba.getchannel("B"),
        img_rgba.getchannel("A"),
    ]

    row_counts = []  # 각 (채널, 행)별 압축 바이트 수
    compressed_rows = []

    for ch in channels:
        ch_bytes = ch.tobytes()
        for row_idx in range(h):
            row = ch_bytes[row_idx * w:(row_idx + 1) * w]
            compressed = _compress_rle(row)
            row_counts.append(len(compressed))
            compressed_rows.append(compressed)

    return row_counts, compressed_rows


def _build_layer_record(
    name: str,
    top: int, left: int, bottom: int, right: int,
    is_group: bool = False,
) -> bytes:
    """레이어 레코드 헤더 (픽셀 데이터 제외)"""
    buf = io.BytesIO()

    # Bounding rect (top, left, bottom, right)
    buf.write(struct.pack(">iiii", top, left, bottom, right))

    # 채널 정보: 4채널 (R, G, B, A)
    num_channels = 4
    buf.write(struct.pack(">H", num_channels))
    # channel_id: 0=R, 1=G, 2=B, -1=Alpha
    channel_ids = [0, 1, 2, -1]
    for cid in channel_ids:
        buf.write(struct.pack(">hI", cid, 0))  # length placeholder

    # Blend mode signature + mode
    buf.write(b"8BIM")
    buf.write(b"norm")  # normal blending

    # Opacity, Clipping, Flags, Filler
    buf.write(struct.pack(">BBBB", 255, 0, 0, 0))

    # Extra data
    extra = _build_layer_extra(name, is_group)
    buf.write(struct.pack(">I", len(extra)))
    buf.write(extra)

    return buf.getvalue()


def _build_layer_extra(name: str, is_group: bool) -> bytes:
    """레이어 추가 데이터 (마스크, 블렌딩, 이름 등)"""
    buf = io.BytesIO()

    # Layer mask data (0 = 없음)
    buf.write(struct.pack(">I", 0))

    # Layer blending ranges (0 = 없음)
    buf.write(struct.pack(">I", 0))

    # Layer name (Pascal string, 4바이트 패딩)
    pname = _pascal_string(name, 4)
    buf.write(pname)

    return buf.getvalue()


# ───────────────────────────────────────────────
# 공개 API: PSD 생성
# ───────────────────────────────────────────────

class PSDLayer:
    """PSD에 추가할 레이어 정보"""
    def __init__(self, name: str, image: Image.Image, x: int = 0, y: int = 0):
        self.name = name[:31]  # PSD 레이어명 최대 31자
        self.image = image.convert("RGBA")
        self.x = x
        self.y = y
        self.w = image.width
        self.h = image.height


def build_psd(canvas_width: int, canvas_height: int, layers: list) -> bytes:
    """
    완전한 PSD 파일 바이너리를 생성한다.

    layers: PSDLayer 객체 리스트 (아래 레이어 → 위 레이어 순서)
    반환: PSD 파일 bytes (파일로 저장하거나 직접 다운로드 가능)
    """
    buf = io.BytesIO()

    # ── 섹션 1: 파일 헤더 ──────────────────────
    buf.write(_build_header(canvas_width, canvas_height))

    # ── 섹션 2: 컬러 모드 데이터 ───────────────
    buf.write(_build_color_mode_data())

    # ── 섹션 3: 이미지 리소스 ──────────────────
    buf.write(_build_image_resources())

    # ── 섹션 4: 레이어 & 마스크 정보 ───────────
    layer_section = _build_layer_section(canvas_width, canvas_height, layers)
    buf.write(struct.pack(">I", len(layer_section)))
    buf.write(layer_section)

    # ── 섹션 5: 병합 이미지 데이터 ─────────────
    buf.write(_build_merged_image(canvas_width, canvas_height, layers))

    return buf.getvalue()


def _build_layer_section(canvas_w: int, canvas_h: int, layers: list) -> bytes:
    """섹션4 전체 (Layer Info + Global Mask)"""
    layer_info = _build_layer_info(canvas_w, canvas_h, layers)

    sec_buf = io.BytesIO()
    # Layer info 길이
    sec_buf.write(struct.pack(">I", len(layer_info)))
    sec_buf.write(layer_info)

    # Global layer mask info (0 = 없음)
    sec_buf.write(struct.pack(">I", 0))

    return sec_buf.getvalue()


def _build_layer_info(canvas_w: int, canvas_h: int, layers: list) -> bytes:
    """레이어 정보 블록"""
    if not layers:
        return struct.pack(">H", 0)

    records_buf = io.BytesIO()
    pixel_data_buf = io.BytesIO()

    num_layers = len(layers)
    # 음수 = 병합 알파 채널 있음 표시
    records_buf.write(struct.pack(">h", -num_layers))

    # 각 레이어 레코드 + 픽셀 데이터 준비
    layer_pixel_data = []
    for layer in layers:
        top = layer.y
        left = layer.x
        bottom = layer.y + layer.h
        right = layer.x + layer.w

        img_rgba = layer.image

        # 채널별 RLE 압축
        row_counts, compressed_rows = _encode_layer_pixels_raw(img_rgba)

        layer_pixel_data.append((row_counts, compressed_rows, layer.h))

        # 레이어 레코드
        rec = io.BytesIO()
        rec.write(struct.pack(">iiii", top, left, bottom, right))

        # 채널 수 = 4 (R,G,B,Alpha)
        rec.write(struct.pack(">H", 4))
        channel_ids = [0, 1, 2, -1]

        # 채널별 데이터 길이 계산
        # compression(2) + row_count_table(2*h per channel) + compressed_data
        h = layer.h
        for ch_idx, cid in enumerate(channel_ids):
            ch_rows = compressed_rows[ch_idx * h:(ch_idx + 1) * h]
            ch_counts = row_counts[ch_idx * h:(ch_idx + 1) * h]
            data_len = 2 + h * 2 + sum(ch_counts)  # compression flag + row count table + data
            rec.write(struct.pack(">hI", cid, data_len))

        # 블렌드 모드
        rec.write(b"8BIM")
        rec.write(b"norm")
        rec.write(struct.pack(">BBBB", 255, 0, 0, 0))

        # 추가 데이터
        extra = _build_layer_extra(layer.name, False)
        rec.write(struct.pack(">I", len(extra)))
        rec.write(extra)

        records_buf.write(rec.getvalue())

    # 픽셀 데이터 작성 (레코드 다음에 연속으로)
    for (row_counts, compressed_rows, h), layer in zip(layer_pixel_data, layers):
        channel_ids = [0, 1, 2, -1]
        for ch_idx in range(4):
            ch_rows = compressed_rows[ch_idx * h:(ch_idx + 1) * h]
            ch_counts = row_counts[ch_idx * h:(ch_idx + 1) * h]

            # 압축 방식: 1 = PackBits RLE
            pixel_data_buf.write(struct.pack(">H", 1))
            # 행별 바이트 수 테이블
            for cnt in ch_counts:
                pixel_data_buf.write(struct.pack(">H", cnt))
            # 실제 압축 데이터
            for row_data in ch_rows:
                pixel_data_buf.write(row_data)

    records_data = records_buf.getvalue()
    pixel_data = pixel_data_buf.getvalue()

    # 전체 길이 = 2(레이어수) + records + pixel_data (4바이트 패딩)
    combined = records_data + pixel_data
    # 4바이트 배수로 패딩
    if len(combined) % 4:
        combined += b"\x00" * (4 - len(combined) % 4)

    info_buf = io.BytesIO()
    info_buf.write(combined)
    return info_buf.getvalue()


def _build_merged_image(canvas_w: int, canvas_h: int, layers: list) -> bytes:
    """섹션5: 병합된 최종 이미지 (Raw, 무압축)"""
    # 캔버스에 모든 레이어 합성
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    for layer in layers:
        if layer.image.mode == "RGBA":
            canvas.paste(layer.image, (layer.x, layer.y), layer.image.getchannel("A"))
        else:
            canvas.paste(layer.image, (layer.x, layer.y))

    # 압축 방식 0 = Raw
    img_buf = io.BytesIO()
    img_buf.write(struct.pack(">H", 0))  # no compression

    # R 채널 전체, G 채널 전체, B 채널 전체 순서로
    r, g, b = canvas.split()
    for ch in [r, g, b]:
        img_buf.write(ch.tobytes())

    return img_buf.getvalue()
