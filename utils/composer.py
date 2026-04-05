"""
composer.py
───────────
- 템플릿 + 사용자 입력 → 미리보기 JPG 합성
- 템플릿 + 사용자 입력 → PSD 파일 생성
"""

import io
import os
import json
import zipfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from .psd_writer import build_psd, PSDLayer


# ──────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/AppleGothic.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """텍스트를 max_w 픽셀 너비에 맞게 줄바꿈."""
    lines, current = [], ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_w and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [text]


def _draw_text_on(canvas: Image.Image, zone: dict, text: str,
                  font_size: int, color: str, align: str):
    draw = ImageDraw.Draw(canvas)
    font = _get_font(font_size)
    rgb = hex_to_rgb(color)
    zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]

    lines = _wrap_text(draw, text, font, zw - 20)
    line_h = font_size + 6
    total_h = len(lines) * line_h
    start_y = zy + max(0, (zh - total_h) // 2)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        if align == "center":
            tx = zx + (zw - tw) // 2
        elif align == "right":
            tx = zx + zw - tw - 10
        else:
            tx = zx + 10
        draw.text((tx, start_y), line, font=font, fill=rgb)
        start_y += line_h


# ──────────────────────────────────────────────────────────
# 미리보기 JPG 합성
# ──────────────────────────────────────────────────────────

def compose_preview(
    source_bytes: bytes,
    zones: list,
    bg_color: str,
    inputs: dict,           # {zone_index: {"value": bytes|str, "font_size": int, ...}}
    show_guides: bool = True,
) -> bytes:
    """
    템플릿 원본 위에 사용자 입력을 합성하여 미리보기 JPG 반환.
    show_guides=True 이면 빈 존에 안내선 표시.
    """
    src = Image.open(io.BytesIO(source_bytes)).convert("RGBA")
    W, H = src.size

    # 배경
    bg_rgb = hex_to_rgb(bg_color)
    canvas = Image.new("RGBA", (W, H), bg_rgb + (255,))
    canvas.alpha_composite(src)

    draw = ImageDraw.Draw(canvas)

    for i, zone in enumerate(zones):
        inp = inputs.get(i, {})
        zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
        ztype = zone["type"]
        has_input = bool(inp.get("value"))

        if ztype == "image" and has_input:
            try:
                user_img = Image.open(io.BytesIO(inp["value"])).convert("RGBA")
                user_img = user_img.resize((zw, zh), Image.LANCZOS)
                canvas.alpha_composite(user_img, (zx, zy))
            except Exception:
                _draw_empty_guide(draw, zx, zy, zw, zh, zone["label"], "이미지 오류")

        elif ztype == "text" and has_input:
            text = inp["value"]
            font_size = inp.get("font_size", zone.get("font_size", 36))
            color = inp.get("text_color", zone.get("text_color", "#222222"))
            align = inp.get("align", zone.get("align", "center"))
            _draw_text_on(canvas.convert("RGB").convert("RGBA"), zone, text, font_size, color, align)
            # PIL 직접 그리기
            draw2 = ImageDraw.Draw(canvas)
            font = _get_font(font_size)
            rgb = hex_to_rgb(color)
            lines = _wrap_text(draw2, text, font, zw - 20)
            line_h = font_size + 6
            total_h = len(lines) * line_h
            sy = zy + max(0, (zh - total_h) // 2)
            for line in lines:
                bbox = draw2.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]
                tx = (zx + (zw - tw) // 2) if align == "center" else (
                    zx + zw - tw - 10 if align == "right" else zx + 10)
                draw2.text((tx, sy), line, font=font, fill=rgb)
                sy += line_h

        elif show_guides:
            # 안내선 표시
            color_guide = (200, 168, 118, 60) if ztype == "image" else (100, 160, 230, 60)
            outline_color = (200, 168, 118, 140) if ztype == "image" else (100, 160, 230, 140)
            overlay = Image.new("RGBA", (zw, zh), color_guide)
            canvas.alpha_composite(overlay, (zx, zy))
            draw.rectangle([zx, zy, zx+zw-1, zy+zh-1], outline=outline_color, width=2)
            icon = "🖼" if ztype == "image" else "T"
            label_text = f"{icon} {zone['label']}"
            draw.text((zx + 8, zy + 8), label_text, fill=(255, 255, 255, 180))

    result = canvas.convert("RGB")
    buf = io.BytesIO()
    result.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _draw_empty_guide(draw, x, y, w, h, label, note=""):
    draw.rectangle([x, y, x+w, y+h], outline=(200, 100, 100, 180), width=2)
    draw.text((x+8, y+8), f"⚠ {label} {note}", fill=(200, 100, 100))


# ──────────────────────────────────────────────────────────
# PSD 생성
# ──────────────────────────────────────────────────────────

def build_output_psd(
    template_meta: dict,
    source_bytes: bytes,
    inputs: dict,
) -> bytes:
    """
    PSD 파일 생성.
    레이어 구조:
      - 배경 (원본 이미지 또는 배경색)
      - 각 존별 레이어 (이미지 존 / 텍스트 존)
    """
    W, H = template_meta["canvas_size"]
    bg_color = template_meta.get("bg_color", "#FFFFFF")
    zones = template_meta["zones"]

    psd_layers = []

    # ── 레이어 1: 배경색 ──────────────────────
    bg_rgb = hex_to_rgb(bg_color)
    bg_img = Image.new("RGBA", (W, H), bg_rgb + (255,))
    psd_layers.append(PSDLayer("배경색", bg_img, 0, 0))

    # ── 레이어 2: 원본 템플릿 이미지 ──────────
    src_img = Image.open(io.BytesIO(source_bytes)).convert("RGBA")
    if src_img.size != (W, H):
        src_img = src_img.resize((W, H), Image.LANCZOS)
    psd_layers.append(PSDLayer("템플릿_원본", src_img, 0, 0))

    # ── 레이어 3~: 각 존 ──────────────────────
    for i, zone in enumerate(zones):
        inp = inputs.get(i, {})
        zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
        label = zone["label"]
        ztype = zone["type"]

        if ztype == "image":
            if inp.get("value"):
                try:
                    user_img = Image.open(io.BytesIO(inp["value"])).convert("RGBA")
                    user_img = user_img.resize((zw, zh), Image.LANCZOS)
                    psd_layers.append(PSDLayer(f"이미지_{label}", user_img, zx, zy))
                    continue
                except Exception:
                    pass
            # 빈 이미지 존: 투명 플레이스홀더
            placeholder = Image.new("RGBA", (zw, zh), (200, 168, 118, 40))
            psd_layers.append(PSDLayer(f"[이미지_교체]_{label}", placeholder, zx, zy))

        elif ztype == "text":
            text = inp.get("value") or zone.get("default_text", label)
            font_size = inp.get("font_size", zone.get("font_size", 36))
            color = inp.get("text_color", zone.get("text_color", "#222222"))
            align = inp.get("align", zone.get("align", "center"))

            # 텍스트를 RGBA 레이어로 렌더링
            txt_layer = Image.new("RGBA", (zw, zh), (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)
            font = _get_font(font_size)
            rgb = hex_to_rgb(color)

            lines = _wrap_text(draw, text, font, zw - 20)
            line_h = font_size + 6
            total_h = len(lines) * line_h
            sy = max(0, (zh - total_h) // 2)

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]
                tx = ((zw - tw) // 2) if align == "center" else (
                    zw - tw - 10 if align == "right" else 10)
                draw.text((tx, sy), line, font=font, fill=rgb + (255,))
                sy += line_h

            psd_layers.append(PSDLayer(f"텍스트_{label}", txt_layer, zx, zy))

    return build_psd(W, H, psd_layers)


# ──────────────────────────────────────────────────────────
# 최종 출력 ZIP
# ──────────────────────────────────────────────────────────

def build_output_zip(
    template_meta: dict,
    source_bytes: bytes,
    inputs: dict,
) -> bytes:
    """JPG 미리보기 + PSD + README를 ZIP으로 묶어 반환."""
    safe_name = template_meta["name"].replace(" ", "_").replace("/", "_")[:40]
    now = datetime.now().strftime("%Y%m%d_%H%M")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # 1. 미리보기 JPG
        jpg = compose_preview(source_bytes, template_meta["zones"],
                              template_meta["bg_color"], inputs, show_guides=False)
        zf.writestr(f"{safe_name}_preview_{now}.jpg", jpg)

        # 2. PSD
        try:
            psd = build_output_psd(template_meta, source_bytes, inputs)
            zf.writestr(f"{safe_name}_{now}.psd", psd)
            psd_note = f"{safe_name}_{now}.psd"
        except Exception as e:
            psd_note = f"PSD 생성 오류: {e}"

        # 3. README
        readme = f"""미샵 템플릿 OS — 출력 패키지
================================
템플릿: {template_meta['name']}
생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
캔버스: {template_meta['canvas_size'][0]}×{template_meta['canvas_size'][1]}px

포함 파일
---------
• {safe_name}_preview_{now}.jpg  — 최종 미리보기 JPG
• {psd_note}           — 포토샵 레이어 파일

포토샵 사용 방법
----------------
1. .psd 파일을 포토샵으로 열기
2. 레이어 패널에서 [이미지_교체] 레이어에 새 이미지 배치
3. 텍스트 레이어 더블클릭 → 내용 수정
4. 마무리 편집 후 JPG/PNG로 저장

존 구성
-------
""" + "\n".join(
    f"  [{z['type'].upper()}] {z['label']}  ({z['x']},{z['y']}) {z['w']}×{z['h']}px"
    for z in template_meta["zones"]
) + f"""

────────────────────────────────
made by MISHARP COMPANY, MIYAWA, 2026
이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.
"""
        zf.writestr("README.txt", readme.encode("utf-8"))

    return buf.getvalue()
