"""
psd_jsx_builder.py
──────────────────
PSD 원본을 기반으로 텍스트/이미지를 교체하는
포토샵 JSX 스크립트 생성.

CS5~CC 전버전 호환.
실행 방법: 포토샵 > File > Scripts > Browse > .jsx 선택
"""

import base64, io, os
from datetime import datetime
from PIL import Image


def build_psd_edit_jsx(
    psd_filename: str,
    psd_info: dict,
    text_replacements: dict,   # {layer_idx: new_text}
    image_replacements: dict,  # {layer_idx: image_bytes}
    output_suffix: str = "_edited",
) -> str:
    """
    원본 PSD를 열어서 레이어를 교체하는 JSX 스크립트 생성.

    ZIP 안에 포함된 원본 PSD와 같은 폴더에서 JSX를 실행하면
    원본 PSD를 자동으로 찾아 열고 레이어를 교체합니다.
    같은 폴더에 PSD가 없을 때만 수동 선택 창을 띄웁니다.
    """
    layers = psd_info['layers']
    W = psd_info['width']
    H = psd_info['height']
    now = datetime.now().strftime('%Y%m%d_%H%M')

    lines = []
    lines += [
        "// ================================================",
        f"// 미샵 템플릿 OS - PSD 레이어 교체 스크립트",
        f"// 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"// 원본 PSD: {psd_filename}",
        "// 포토샵 CS5~CC 모든 버전 지원",
        "// 실행: File > Scripts > Browse 에서 이 파일 선택",
        "// ================================================",
        "#target photoshop",
        "",
        "function decodeAndSaveTmp(b64str, filename) {",
        "    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';",
        "    b64str = b64str.replace(/[^A-Za-z0-9+\\/]/g, '');",
        "    var bytes = [];",
        "    for (var i = 0; i < b64str.length; i += 4) {",
        "        var b0=chars.indexOf(b64str[i]),   b1=chars.indexOf(b64str[i+1]);",
        "        var b2=chars.indexOf(b64str[i+2]), b3=chars.indexOf(b64str[i+3]);",
        "        bytes.push((b0<<2)|(b1>>4));",
        "        if(b2!==64) bytes.push(((b1&0xF)<<4)|(b2>>2));",
        "        if(b3!==64) bytes.push(((b2&0x3)<<6)|b3);",
        "    }",
        "    var f = new File(Folder.temp.fsName + '/' + filename);",
        "    f.open('w'); f.encoding = 'BINARY';",
        "    for(var j=0;j<bytes.length;j++) f.write(String.fromCharCode(bytes[j]));",
        "    f.close(); return f;",
        "}",
        "",
        "function findLayerByName(doc, name) {",
        "    for (var i = 0; i < doc.layers.length; i++) {",
        "        if (doc.layers[i].name === name) return doc.layers[i];",
        "    }",
        "    // 그룹 내부도 탐색",
        "    for (var i = 0; i < doc.layerSets.length; i++) {",
        "        var grp = doc.layerSets[i];",
        "        for (var j = 0; j < grp.layers.length; j++) {",
        "            if (grp.layers[j].name === name) return grp.layers[j];",
        "        }",
        "    }",
        "    return null;",
        "}",
        "",
        "function main() {",
        "    // 원본 PSD 자동 찾기 (JSX와 같은 폴더 우선)",
        "    var jsxFile = new File($.fileName);",
        "    var jsxFolder = jsxFile.parent;",
        f"    var expectedPsd = new File(jsxFolder.fsName + '/{psd_filename}');",
        "    var psdFile = null;",
        "    if (expectedPsd.exists) {",
        "        psdFile = expectedPsd;",
        "    } else {",
        "        var psdCandidates = jsxFolder.getFiles('*.psd');",
        "        if (psdCandidates && psdCandidates.length > 0) {",
        "            psdFile = psdCandidates[0];",
        "        }",
        "    }",
        "    if (!psdFile) {",
        f"        psdFile = File.openDialog('원본 PSD 파일을 선택하세요 ({psd_filename})', '*.psd');",
        "    }",
        "    if (!psdFile) { alert('원본 PSD 파일을 찾지 못했습니다. ZIP을 그대로 압축 해제한 폴더에서 JSX를 실행해주세요.'); return; }",
        "    var doc = app.open(psdFile);",
        "    app.activeDocument = doc;",
        "",
    ]

    # 텍스트 레이어 교체
    if text_replacements:
        lines.append("    // ── 텍스트 레이어 교체 ──")
        for layer_idx, new_text in text_replacements.items():
            layer = next((l for l in layers if l['idx'] == layer_idx), None)
            if not layer: continue
            layer_name = layer['name'].replace("'", "\\'")
            safe_text  = new_text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\r")
            lines += [
                f"    // 레이어: {layer['name']}",
                f"    var txtLayer_{layer_idx} = findLayerByName(doc, '{layer_name}');",
                f"    if (txtLayer_{layer_idx} && txtLayer_{layer_idx}.kind === LayerKind.TEXT) {{",
                f"        txtLayer_{layer_idx}.textItem.contents = '{safe_text}';",
                f"    }} else {{",
                f"        alert('텍스트 레이어를 찾지 못했습니다');",
                f"    }}",
                "",
            ]

    # 이미지 레이어 교체
    if image_replacements:
        lines.append("    // ── 이미지 레이어 교체 ──")
        for layer_idx, img_bytes in image_replacements.items():
            layer = next((l for l in layers if l['idx'] == layer_idx), None)
            if not layer: continue

            # 이미지 리사이즈 후 base64
            try:
                img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                lw, lh = layer['w'], layer['h']
                if lw > 0 and lh > 0:
                    img = img.resize((lw, lh), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, 'JPEG', quality=90)
                b64 = base64.b64encode(buf.getvalue()).decode()
            except Exception as e:
                continue

            layer_name = layer['name'].replace("'", "\\'")
            safe_name  = f"img_{layer_idx}"
            lx  = layer['rect'][1]
            ly  = layer['rect'][0]
            lw2 = layer['w']
            lh2 = layer['h']
            cx  = lx + lw2 // 2
            cy  = ly + lh2 // 2
            lines += [
                f"    // 레이어: {layer['name']} ({lw2}×{lh2}px) → Smart Object",
                f"    var {safe_name}B64 = '{b64}';",
                f"    var {safe_name}File = decodeAndSaveTmp({safe_name}B64, 'misharp_{safe_name}.jpg');",
                f"    var {safe_name}OldLayer = findLayerByName(doc, '{layer_name}');",
                f"    if ({safe_name}OldLayer) {{",
                f"        doc.activeLayer = {safe_name}OldLayer;",
                f"        var {safe_name}PlaceDesc = new ActionDescriptor();",
                f"        {safe_name}PlaceDesc.putPath(charIDToTypeID('null'), {safe_name}File);",
                f"        {safe_name}PlaceDesc.putEnumerated(charIDToTypeID('FTcs'), charIDToTypeID('QCSt'), charIDToTypeID('Qcsl'));",
                f"        var {safe_name}Pos = new ActionDescriptor();",
                f"        {safe_name}Pos.putUnitDouble(charIDToTypeID('Hrzn'), charIDToTypeID('#Pxl'), {cx});",
                f"        {safe_name}Pos.putUnitDouble(charIDToTypeID('Vrtc'), charIDToTypeID('#Pxl'), {cy});",
                f"        {safe_name}PlaceDesc.putObject(charIDToTypeID('Pstn'), charIDToTypeID('Pnt '), {safe_name}Pos);",
                f"        var {safe_name}SzDesc = new ActionDescriptor();",
                f"        {safe_name}SzDesc.putUnitDouble(charIDToTypeID('Wdth'), charIDToTypeID('#Pxl'), {lw2});",
                f"        {safe_name}SzDesc.putUnitDouble(charIDToTypeID('Hght'), charIDToTypeID('#Pxl'), {lh2});",
                f"        {safe_name}PlaceDesc.putObject(charIDToTypeID('Dmns'), charIDToTypeID('Pnt '), {safe_name}SzDesc);",
                f"        executeAction(charIDToTypeID('Plc '), {safe_name}PlaceDesc, DialogModes.NO);",
                f"        var {safe_name}NewLayer = doc.activeLayer;",
                f"        {safe_name}NewLayer.name = '{layer_name}';",
                f"        {safe_name}OldLayer.remove();",
                f"    }}",
                "",
            ]


    # 저장
    lines += [
        "    // ── 결과 저장 ──",
        f"    var savePath = psdFile.path + '/미샵_교체완성_{now}.psd';",
        "    var saveFile = new File(savePath);",
        "    var psdOpts = new PhotoshopSaveOptions();",
        "    psdOpts.layers = true;",
        "    psdOpts.embedColorProfile = true;",
        "    doc.saveAs(saveFile, psdOpts, true);",
        f"    alert('완료!\\n저장 위치:\\n' + savePath);",
        "}",
        "",
        "try { main(); } catch(e) { alert('오류: ' + e.message + '\\n라인: ' + e.line); }",
    ]

    return "\n".join(lines)
