"""
composer.py
- 미리보기 JPG 합성
- 포토샵 JSX 스크립트 생성 (CS5~CC 전버전 호환)
- ZIP 패키지 생성
"""

import io, os, json, zipfile, base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


# ── 유틸 ──────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2]-bbox[0] > max_w and cur:
            lines.append(cur); cur = ch
        else:
            cur = test
    if cur: lines.append(cur)
    return lines or [text]


# ── 미리보기 JPG 합성 ─────────────────────────────────────

def compose_preview(
    source_bytes: bytes,
    zones: list,
    bg_color: str,
    inputs: dict,
    show_guides: bool = True,
) -> bytes:
    src = Image.open(io.BytesIO(source_bytes)).convert("RGBA")
    W, H = src.size
    canvas = Image.new("RGBA", (W, H), hex_to_rgb(bg_color) + (255,))
    canvas.alpha_composite(src)
    draw = ImageDraw.Draw(canvas)

    for i, zone in enumerate(zones):
        inp  = inputs.get(i, {})
        zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
        ztype = zone["type"]

        if ztype == "image" and inp.get("value"):
            try:
                ui = Image.open(io.BytesIO(inp["value"])).convert("RGBA")
                ui = ui.resize((zw, zh), Image.LANCZOS)
                canvas.alpha_composite(ui, (zx, zy))
            except Exception:
                _draw_guide(draw, zx, zy, zw, zh, zone["label"], "#FF5555")
        elif ztype == "text" and inp.get("value"):
            text     = inp["value"]
            fs       = int(inp.get("font_size", zone.get("font_size", 36)))
            color    = inp.get("text_color", zone.get("text_color", "#222222"))
            align    = inp.get("align", zone.get("align", "center"))
            font     = _get_font(fs)
            rgb      = hex_to_rgb(color)
            lines    = _wrap_text(draw, text, font, zw - 20)
            line_h   = fs + 6
            total_h  = len(lines) * line_h
            sy       = zy + max(0, (zh - total_h) // 2)
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=font)
                tw   = bbox[2] - bbox[0]
                tx   = (zx + (zw-tw)//2) if align=="center" else (zx+zw-tw-10 if align=="right" else zx+10)
                draw.text((tx, sy), line, font=font, fill=rgb)
                sy  += line_h
        elif show_guides:
            if ztype == "image":
                _draw_guide(draw, zx, zy, zw, zh, zone["label"], "#C8A876")
            else:
                _draw_guide(draw, zx, zy, zw, zh, zone["label"], "#78a8f0")

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _draw_guide(draw, x, y, w, h, label, color_hex):
    r, g, b = hex_to_rgb(color_hex)
    fill    = (r, g, b, 40)
    outline = (r, g, b, 180)
    overlay = Image.new("RGBA", (w, h), fill)
    # 직접 그리기 (투명 지원)
    draw.rectangle([x, y, x+w-1, y+h-1], outline=outline, width=2)
    draw.text((x+8, y+8), label, fill=outline)


# ── 포토샵 JSX 스크립트 생성 (CS5~CC 완전 호환) ──────────

def _img_to_b64_jpeg(img_bytes: bytes, resize_to: tuple = None) -> str:
    """이미지를 base64 JPEG로 변환 (JSX 스크립트 내 임베딩용)"""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if resize_to:
        img = img.resize(resize_to, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def build_jsx_script(
    template_meta: dict,
    source_bytes: bytes,
    inputs: dict,
    output_jpg_filename: str,
) -> str:
    """
    포토샵 CS5~CC 완전 호환 JSX 스크립트.
    실행하면:
    1. 캔버스 생성
    2. 배경색 레이어
    3. 템플릿 원본 이미지 레이어 (base64 임베딩 → 임시파일 경유)
    4. 각 존별 이미지/텍스트 레이어
    """
    W, H   = template_meta["canvas_size"]
    zones  = template_meta["zones"]
    bg     = template_meta.get("bg_color", "#FFFFFF")
    name   = template_meta["name"]
    bg_rgb = hex_to_rgb(bg)

    lines = []
    lines.append("// =================================================")
    lines.append(f"// 미샵 템플릿 OS - 포토샵 자동 레이어 생성 스크립트")
    lines.append(f"// 템플릿: {name}")
    lines.append(f"// 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("// 포토샵 CS5 이상 호환 | Made by MISHARP COMPANY")
    lines.append("// =================================================")
    lines.append("#target photoshop")
    lines.append("")
    lines.append("function decodeBase64ToFile(b64str, filePath) {")
    lines.append("    var binaryStr = '';")
    lines.append("    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';")
    lines.append("    var len = b64str.length;")
    lines.append("    var i = 0;")
    lines.append("    var bytes = [];")
    lines.append("    b64str = b64str.replace(/[^A-Za-z0-9+\\/]/g, '');")
    lines.append("    while (i < b64str.length) {")
    lines.append("        var b0=chars.indexOf(b64str[i++]),b1=chars.indexOf(b64str[i++]);")
    lines.append("        var b2=chars.indexOf(b64str[i++]),b3=chars.indexOf(b64str[i++]);")
    lines.append("        bytes.push((b0<<2)|(b1>>4));")
    lines.append("        if(b2!==64){bytes.push(((b1&0xF)<<4)|(b2>>2));}")
    lines.append("        if(b3!==64){bytes.push(((b2&0x3)<<6)|b3);}")
    lines.append("    }")
    lines.append("    var f = new File(filePath);")
    lines.append("    f.open('w'); f.encoding = 'BINARY';")
    lines.append("    for(var j=0;j<bytes.length;j++){f.write(String.fromCharCode(bytes[j]));}")
    lines.append("    f.close();")
    lines.append("    return f;")
    lines.append("}")
    lines.append("")
    lines.append("function main() {")
    lines.append(f"    var W = {W}, H = {H};")
    lines.append(f"    var doc = app.documents.add(W, H, 72, '{name}', NewDocumentMode.RGB, DocumentFill.TRANSPARENT);")
    lines.append("    app.activeDocument = doc;")
    lines.append("    var tmpDir = Folder.temp.fsName;")
    lines.append("")

    # 배경색 레이어
    lines.append("    // --- 배경색 레이어 ---")
    lines.append("    var bgLayer = doc.artLayers.add();")
    lines.append("    bgLayer.name = 'Background';")
    lines.append(f"    var bgColor = new SolidColor();")
    lines.append(f"    bgColor.rgb.red={bg_rgb[0]}; bgColor.rgb.green={bg_rgb[1]}; bgColor.rgb.blue={bg_rgb[2]};")
    lines.append("    doc.selection.selectAll();")
    lines.append("    doc.selection.fill(bgColor);")
    lines.append("    doc.selection.deselect();")
    lines.append("")

    # 원본 템플릿 이미지 레이어 (축소해서 임베딩)
    src_img = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    # 용량이 크면 축소 (JSX 파일 크기 제한 고려)
    src_w, src_h = src_img.size
    if src_w * src_h > 900 * 5000:
        ratio = (900 * 5000 / (src_w * src_h)) ** 0.5
        src_img = src_img.resize((int(src_w*ratio), int(src_h*ratio)), Image.LANCZOS)
    src_buf = io.BytesIO()
    src_img.save(src_buf, "JPEG", quality=80)
    src_b64 = base64.b64encode(src_buf.getvalue()).decode()

    lines.append("    // --- 템플릿 원본 이미지 레이어 ---")
    lines.append(f"    var srcB64 = '{src_b64}';")
    lines.append("    var srcFile = decodeBase64ToFile(srcB64, tmpDir + '/misharp_src.jpg');")
    lines.append("    app.load(srcFile);")
    lines.append("    var srcDoc = app.activeDocument;")
    lines.append("    srcDoc.selection.selectAll();")
    lines.append("    srcDoc.selection.copy();")
    lines.append("    srcDoc.close(SaveOptions.DONOTSAVECHANGES);")
    lines.append("    app.activeDocument = doc;")
    lines.append("    var srcLayer = doc.artLayers.add();")
    lines.append("    srcLayer.name = 'Template_Original';")
    lines.append("    doc.paste();")
    lines.append("    var pastedSrc = doc.activeLayer;")
    lines.append("    pastedSrc.name = 'Template_Original';")
    lines.append(f"    pastedSrc.resize({W/src_img.width*100:.1f}, {H/src_img.height*100:.1f}, AnchorPosition.TOPLEFT);")
    lines.append("    pastedSrc.translate(-pastedSrc.bounds[0], -pastedSrc.bounds[1]);")
    lines.append("")

    # 각 존별 레이어
    for i, zone in enumerate(zones):
        inp    = inputs.get(i, {})
        zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
        label  = zone["label"].replace("'", "_")
        ztype  = zone["type"]

        lines.append(f"    // --- 존: {label} ({ztype}) ---")

        if ztype == "image":
            if inp.get("value"):
                # 사용자 이미지 임베딩
                ui     = Image.open(io.BytesIO(inp["value"])).convert("RGB")
                ui     = ui.resize((zw, zh), Image.LANCZOS)
                ui_buf = io.BytesIO()
                ui.save(ui_buf, "JPEG", quality=88)
                ui_b64 = base64.b64encode(ui_buf.getvalue()).decode()
                safe   = label.replace(" ","_")[:20]

                lines.append(f"    var img{i}B64 = '{ui_b64}';")
                lines.append(f"    var img{i}File = decodeBase64ToFile(img{i}B64, tmpDir+'/misharp_zone{i}.jpg');")
                lines.append(f"    app.load(img{i}File);")
                lines.append(f"    var img{i}Doc = app.activeDocument;")
                lines.append(f"    img{i}Doc.selection.selectAll(); img{i}Doc.selection.copy();")
                lines.append(f"    img{i}Doc.close(SaveOptions.DONOTSAVECHANGES);")
                lines.append(f"    app.activeDocument = doc;")
                lines.append(f"    doc.paste();")
                lines.append(f"    var zone{i}Layer = doc.activeLayer;")
                lines.append(f"    zone{i}Layer.name = 'IMG_{safe}';")
                lines.append(f"    zone{i}Layer.resize(100,100,AnchorPosition.TOPLEFT);")
                lines.append(f"    zone{i}Layer.translate({zx}-zone{i}Layer.bounds[0], {zy}-zone{i}Layer.bounds[1]);")
            else:
                # 빈 이미지 존 — 가이드 레이어
                lines.append(f"    var empty{i} = doc.artLayers.add();")
                lines.append(f"    empty{i}.name = '[IMG_REPLACE]_{label}';")
                lines.append(f"    var gc{i} = new SolidColor(); gc{i}.rgb.red=200; gc{i}.rgb.green=168; gc{i}.rgb.blue=118;")
                lines.append(f"    doc.selection.setRectangular({zy},{zx},{zy+zh},{zx+zw});")
                lines.append(f"    doc.selection.fill(gc{i},ColorBlendMode.NORMAL,30,false);")
                lines.append(f"    doc.selection.deselect();")

        elif ztype == "text":
            text     = inp.get("value") or zone.get("default_text", label)
            text     = text.replace("'", "\\'").replace("\n", "\\n")
            fs       = int(inp.get("font_size", zone.get("font_size", 36)))
            color    = inp.get("text_color", zone.get("text_color", "#222222"))
            align_v  = inp.get("align", zone.get("align", "center"))
            rgb      = hex_to_rgb(color)
            js_align = {"center":"Justification.CENTER","left":"Justification.LEFT","right":"Justification.RIGHT"}.get(align_v,"Justification.CENTER")

            lines.append(f"    var txt{i} = doc.artLayers.add();")
            lines.append(f"    txt{i}.kind = LayerKind.TEXT;")
            lines.append(f"    txt{i}.name = 'TXT_{label[:20]}';")
            lines.append(f"    var ti{i} = txt{i}.textItem;")
            lines.append(f"    ti{i}.contents = '{text}';")
            lines.append(f"    ti{i}.size = new UnitValue({fs},'px');")
            lines.append(f"    ti{i}.position = [new UnitValue({zx+zw//2},'px'), new UnitValue({zy+zh//2},'px')];")
            lines.append(f"    ti{i}.justification = {js_align};")
            lines.append(f"    var tc{i} = new SolidColor(); tc{i}.rgb.red={rgb[0]}; tc{i}.rgb.green={rgb[1]}; tc{i}.rgb.blue={rgb[2]};")
            lines.append(f"    ti{i}.color = tc{i};")

        lines.append("")

    lines.append("    alert('미샵 템플릿 OS: 레이어 생성 완료!\\n\\n레이어 패널에서 각 레이어를 확인하고\\n[IMG_REPLACE] 레이어에 실제 이미지를 배치하세요.');")
    lines.append("}")
    lines.append("")
    lines.append("try { main(); } catch(e) { alert('오류: ' + e.message); }")

    return "\n".join(lines)


# ── ZIP 패키지 생성 ──────────────────────────────────────

def build_output_zip(
    template_meta: dict,
    source_bytes: bytes,
    inputs: dict,
) -> bytes:
    safe = template_meta["name"].replace(" ","_").replace("/","_")[:40]
    now  = datetime.now().strftime("%Y%m%d_%H%M")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # 1. 완성본 JPG (합성 결과)
        jpg = compose_preview(source_bytes, template_meta["zones"],
                              template_meta.get("bg_color","#FFFFFF"), inputs, show_guides=False)
        zf.writestr(f"{safe}_완성본_{now}.jpg", jpg)

        # 2. 포토샵 JSX 스크립트 (CS5~CC 호환)
        jpg_fname = f"{safe}_완성본_{now}.jpg"
        try:
            jsx = build_jsx_script(template_meta, source_bytes, inputs, jpg_fname)
            zf.writestr(f"{safe}_포토샵레이어_{now}.jsx", jsx.encode("utf-8"))
            jsx_note = f"{safe}_포토샵레이어_{now}.jsx"
        except Exception as e:
            jsx_note = f"JSX 생성 오류: {e}"

        # 3. README
        readme = f"""미샵 템플릿 OS — 출력 패키지
================================
템플릿: {template_meta['name']}
생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
캔버스: {template_meta['canvas_size'][0]}×{template_meta['canvas_size'][1]}px

포함 파일
---------
• {safe}_완성본_{now}.jpg   — 즉시 사용 가능한 최종 JPG
• {jsx_note}  — 포토샵 레이어 자동생성 스크립트

포토샵 레이어 사용법 (CS5~CC 전버전 지원)
-----------------------------------------
1. 포토샵 실행
2. File > Scripts > Browse 클릭
3. {jsx_note} 선택 후 실행
4. 레이어 패널에 자동으로 레이어 생성됨
5. [IMG_REPLACE] 레이어에 고화질 이미지 배치
6. 텍스트 레이어 더블클릭으로 내용 수정
7. File > Save As로 PSD 저장

존 구성
-------
{chr(10).join(f"  [{z['type'].upper()}] {z['label']}  ({z['x']},{z['y']}) {z['w']}×{z['h']}px" for z in template_meta['zones'])}

────────────────────────────────
made by MISHARP COMPANY, MIYAWA, 2026
이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.
"""
        zf.writestr("README.txt", readme.encode("utf-8"))

    return buf.getvalue()
