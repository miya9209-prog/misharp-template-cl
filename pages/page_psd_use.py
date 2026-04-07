"""
page_psd_use.py — ① 템플릿 불러오기

레이아웃:
  선택화면: 카드(이름+버튼+썸네일) + 삭제 버튼
  작업화면: 3열 - [이미지 교체] | [텍스트 교체] | [PSD 미리보기]
"""
import streamlit as st
import io, sys, os, base64, zipfile, json, struct, shutil
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import (
    load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
)
from utils.psd_parser import (
    psd_to_preview_jpg, get_layer_thumbnail, build_editable_layer_sets
)
from utils.psd_jsx_builder import build_psd_edit_jsx



# ── 템플릿 삭제
def _delete_template(tid):
    try:
        mf = Path("templates/_meta.json")
        data = json.loads(mf.read_text(encoding="utf-8"))
        data.pop(tid, None)
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        td = Path(f"templates/{tid}")
        if td.exists():
            shutil.rmtree(td)
    except Exception as e:
        st.error(f"삭제 오류: {e}")


# ── 레이어 썸네일 추출 (정사각형 cover)
@st.cache_data(show_spinner=False)
def _layer_thumb(psd_json: str, layer_idx: int, rect: tuple, size: int = 56) -> str | None:
    try:
        psd_info = json.loads(psd_json)
        direct = get_layer_thumbnail(psd_info, layer_idx, max_size=max(size * 2, 120))
        if direct:
            return base64.b64encode(direct).decode()

        psd_bytes = psd_info.get('raw')
        if not psd_bytes:
            return None
        if isinstance(psd_bytes, str):
            psd_bytes = base64.b64decode(psd_bytes)
        prev = psd_to_preview_jpg(psd_bytes, max_width=900)
        full = Image.open(io.BytesIO(prev)).convert("RGB")
        pW, pH = full.size
        W_orig = psd_info['width']
        H_orig = psd_info['height']
        sx, sy = pW / W_orig, pH / H_orig

        t, le, b, r = rect
        x1, y1 = max(0, int(le*sx)), max(0, int(t*sy))
        x2, y2 = min(pW, int(r*sx)),  min(pH, int(b*sy))
        if x2-x1 < 5 or y2-y1 < 5:
            return None

        crop = full.crop((x1, y1, x2, y2))
        cW, cH = crop.size
        scale  = size / min(cW, cH)
        new_w, new_h = max(1, int(cW*scale)), max(1, int(cH*scale))
        crop   = crop.resize((new_w, new_h), Image.LANCZOS)
        cx, cy = new_w//2, new_h//2
        half   = size//2
        crop   = crop.crop((max(0,cx-half), max(0,cy-half),
                             max(0,cx-half)+size, max(0,cy-half)+size))
        buf = io.BytesIO()
        crop.save(buf, "JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


# ── 라이브 미리보기 이미지 생성 (캐시)
@st.cache_data(show_spinner=False)
def _make_live_preview(prev_bytes: bytes, editable_json: str,
                       active_idx, inp_json: str, W_orig: int, H_orig: int) -> str:
    editable = json.loads(editable_json)
    inputs = json.loads(inp_json)

    base = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = base.size
    sx, sy = pW / W_orig, pH / H_orig
    canvas = base.copy()
    ov = Image.new("RGBA", (pW, pH), (0, 0, 0, 0))
    drw = ImageDraw.Draw(ov)
    font = ImageFont.load_default()

    def _wrap_text(draw, text, max_width):
        text = str(text).replace("\r", "")
        parts = text.split()
        if not parts:
            return [""]
        lines, cur = [], parts[0]
        for w in parts[1:]:
            test = cur + " " + w
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def _layer_box(layer):
        t, le, b, r = layer['rect']
        x1, y1 = int(le * sx), int(t * sy)
        x2, y2 = int(r * sx), int(b * sy)
        return x1, y1, x2, y2

    def _order_no(layer):
        name = str(layer.get('name', ''))
        digits = ''.join(ch for ch in name if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except Exception:
                pass
        return 0

    def _label_text(layer):
        kind = '이미지' if layer['type'] == 'image' else '텍스트'
        no = _order_no(layer)
        if no > 0:
            return f"{kind} {no}"
        return str(layer.get('name') or kind)

    def _draw_badge(x1, y1, text, fill_rgba, outline_rgba=None, text_fill=(255,255,255)):
        if not text:
            return
        x1 = max(4, x1)
        y1 = max(4, y1)
        pad_x, pad_y = 6, 4
        bbox = drw.textbbox((0, 0), text, font=font)
        bw = (bbox[2] - bbox[0]) + pad_x * 2
        bh = (bbox[3] - bbox[1]) + pad_y * 2
        x2 = min(pW - 4, x1 + bw)
        y2 = min(pH - 4, y1 + bh)
        drw.rounded_rectangle([x1, y1, x2, y2], radius=5, fill=fill_rgba, outline=outline_rgba)
        drw.text((x1 + pad_x, y1 + pad_y - 1), text, fill=text_fill, font=font)

    # 1) 실제 교체된 내용을 먼저 합성
    for layer in editable:
        layer_input = inputs.get(str(layer['idx']), {})
        value = layer_input.get('value')
        if not value:
            continue

        x1, y1, x2, y2 = _layer_box(layer)
        if x2 - x1 < 6 or y2 - y1 < 6:
            continue

        if layer['type'] == 'image' and layer_input.get('kind') == 'image_bytes':
            try:
                rep = Image.open(io.BytesIO(base64.b64decode(value))).convert("RGB")
                fitted = ImageOps.fit(rep, (x2 - x1, y2 - y1), method=Image.LANCZOS)
                canvas.alpha_composite(fitted.convert("RGBA"), (x1, y1))
            except Exception:
                pass
        elif layer['type'] == 'text' and layer_input.get('kind') == 'text_value':
            pad = 6
            drw.rounded_rectangle([x1, y1, x2, y2], radius=4, fill=(255, 255, 255, 235), outline=(53, 137, 255, 255), width=2)
            text_value = str(value).strip()
            max_w = max(40, (x2 - x1) - pad * 2)
            lines = []
            for part in text_value.split("\n"):
                lines.extend(_wrap_text(drw, part, max_w))
            line_h = 14
            max_lines = max(1, ((y2 - y1) - pad * 2) // line_h)
            lines = lines[:max_lines]
            ty = y1 + pad
            for line in lines:
                drw.text((x1 + pad, ty), line, fill=(20, 20, 20), font=font)
                ty += line_h

    # 2) 모든 영역을 색상/번호/상태 배지로 시각화
    for layer in editable:
        x1, y1, x2, y2 = _layer_box(layer)
        if x2 - x1 < 3 or y2 - y1 < 3:
            continue

        lt = layer['type']
        is_active = (layer['idx'] == active_idx)
        has_value = bool(inputs.get(str(layer['idx']), {}).get('value'))
        is_image = (lt == 'image')

        if has_value:
            fill = (40, 210, 100, 24) if is_image else (53, 137, 255, 24)
            outline = (40, 210, 100, 255) if is_image else (53, 137, 255, 255)
            line_w = 6 if is_active else 4
            label = f"교체됨 · {_label_text(layer)}"
            badge_fill = (18, 132, 62, 236) if is_image else (32, 95, 186, 236)
        else:
            fill = (255, 90, 90, 24) if is_active else ((108, 175, 255, 10) if is_image else (255, 199, 0, 10))
            outline = (255, 72, 72, 255) if is_active else ((108, 175, 255, 115) if is_image else (255, 199, 0, 115))
            line_w = 7 if is_active else 2
            label = f"선택중 · {_label_text(layer)}" if is_active else _label_text(layer)
            badge_fill = (190, 36, 36, 238) if is_active else ((32, 46, 84, 215) if is_image else (110, 90, 24, 220))

        drw.rectangle([x1, y1, x2, y2], fill=fill, outline=outline, width=line_w)

        if is_active:
            c = (255, 72, 72, 255)
            seg = max(16, min(42, max(12, (x2 - x1) // 5), max(12, (y2 - y1) // 5)))
            drw.line([x1, y1, x1 + seg, y1], fill=c, width=4)
            drw.line([x1, y1, x1, y1 + seg], fill=c, width=4)
            drw.line([x2, y1, x2 - seg, y1], fill=c, width=4)
            drw.line([x2, y1, x2, y1 + seg], fill=c, width=4)
            drw.line([x1, y2, x1 + seg, y2], fill=c, width=4)
            drw.line([x1, y2, x1, y2 - seg], fill=c, width=4)
            drw.line([x2, y2, x2 - seg, y2], fill=c, width=4)
            drw.line([x2, y2, x2, y2 - seg], fill=c, width=4)

        badge_y = y1 + 6
        if is_active and has_value:
            _draw_badge(x1 + 6, badge_y, f"방금 교체 · {_label_text(layer)}", (200, 40, 40, 242))
            _draw_badge(x1 + 6, badge_y + 24, "미리보기 반영됨", badge_fill)
        else:
            _draw_badge(x1 + 6, badge_y, label, badge_fill)

    merged = Image.alpha_composite(canvas, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">① 템플릿 불러오기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 템플릿을 불러와 이미지·텍스트를 교체하고 새 PSD로 저장하세요</div>', unsafe_allow_html=True)

    for k, v in [("pu_sel",None),("pu_inp",{}),("pu_act",None),("pu_prev",None),
                 ("pu_del_confirm",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # 템플릿 로드
    all_tpl = {}
    try:
        all_tpl = {k:v for k,v in load_all().items()
                   if isinstance(v,dict) and v.get("template_type")=="psd"}
    except Exception:
        pass

    if not all_tpl:
        st.info("PSD 템플릿이 없습니다. ② PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ════════════════════════════════════════
    # A. 템플릿 선택 화면
    # ════════════════════════════════════════
    if not st.session_state.pu_sel:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())

        # 6열 레이아웃 + 2cm 세로형 썸네일
        COLS = 6
        for row in range(0, len(tpl_list), COLS):
            cols = st.columns(COLS, gap="small")
            for ci, (tid, meta) in enumerate(tpl_list[row:row+COLS]):
                with cols[ci]:
                    name = meta.get('name','')
                    w, h = meta.get("canvas_size",[0,0])

                    st.markdown(
                        f'<div style="font-size:11px;font-weight:700;color:#ddd;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                        f'margin-bottom:3px">{name}</div>',
                        unsafe_allow_html=True)
                    st.caption(f"{w}×{h}px")

                    b1, b2 = st.columns([2.4, 1], gap="small")
                    with b1:
                        if st.button("사용", key=f"tsel_{tid}",
                                     use_container_width=True, type="primary"):
                            st.session_state.pu_sel  = tid
                            st.session_state.pu_inp  = {}
                            st.session_state.pu_act  = None
                            st.session_state.pu_prev = None
                            st.rerun()
                    with b2:
                        if st.session_state.pu_del_confirm == tid:
                            if st.button("취소", key=f"del_cnc_{tid}",
                                         use_container_width=True):
                                st.session_state.pu_del_confirm = None
                                st.rerun()
                        else:
                            if st.button("🗑️", key=f"del_{tid}",
                                         use_container_width=True, help="삭제"):
                                st.session_state.pu_del_confirm = tid
                                st.rerun()

                    if st.session_state.pu_del_confirm == tid:
                        if st.button("삭제", key=f"del_cfm_{tid}",
                                     type="primary", use_container_width=True):
                            _delete_template(tid)
                            st.session_state.pu_del_confirm = None
                            st.rerun()

                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<div style="width:2cm;margin:8px auto 0 auto;border-radius:4px;overflow:hidden;'
                            f'border:1px solid rgba(255,255,255,0.12);background:#111">'
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:2cm;height:auto;display:block;"></div>',
                            unsafe_allow_html=True)
        return

    # ════════════════════════════════════════
    # B. 작업 화면
    # ════════════════════════════════════════
    tid       = st.session_state.pu_sel
    meta      = load_one(tid)
    info      = load_psd_info(tid)
    psd_bytes = get_psd_bytes(tid)

    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_sel = None
        return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_all, txt_all, img_all = build_editable_layer_sets(info)
    editable_idxs = set(int(k) for k,v in info.get('editable_layers',{}).items() if v)
    editable = [l for l in editable_all if l['idx'] in editable_idxs and l.get('w', 0) > 0 and l.get('h', 0) > 0]
    txt_lays = [l for l in txt_all if l['idx'] in editable_idxs]
    img_lays = [l for l in img_all if l['idx'] in editable_idxs]
    psd_info_for_thumb = dict(info)
    psd_info_for_thumb['raw'] = base64.b64encode(psd_bytes).decode()
    psd_json_for_thumb = json.dumps(psd_info_for_thumb)

    # 미리보기 로드
    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try:
                st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except Exception:
                st.session_state.pu_prev = b""

    inp = st.session_state.pu_inp
    act = st.session_state.pu_act

    # 상단 바
    st.info(f"📋 **{meta['name']}** | {W}×{H}px | 🖼️ {len(img_lays)}개 · ✏️ {len(txt_lays)}개")
    if st.button("← 템플릿 다시 선택", key="pu_back"):
        st.session_state.pu_sel = None
        st.rerun()
    st.divider()

    # ════════════════════════════════════════
    # 3열 레이아웃
    # [이미지 교체] | [텍스트 교체] | [PSD 미리보기]
    # col_img, col_txt 에만 st.button/st.file_uploader
    # col_prev 는 이미지만
    # ════════════════════════════════════════
    col_img, col_txt, col_prev = st.columns([1, 1, 1], gap="medium")

    # ── 1열: 이미지 교체 ──────────────────
    with col_img:
        id_ = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))
        st.markdown(
            f'<div style="color:#78a8f0;font-weight:700;font-size:13px;'
            f'padding:6px 10px;background:rgba(100,160,230,0.08);'
            f'border-radius:6px;margin-bottom:8px">🖼️ 이미지 교체 {id_}/{len(img_lays)}</div>',
            unsafe_allow_html=True)

        for order_no, l in enumerate(img_lays, start=1):
            is_a  = (act == l['idx'])
            has_v = bool(inp.get(l['idx'],{}).get('value'))
            s     = "✅" if has_v else ("▶" if is_a else "○")
            bg    = "rgba(100,160,230,0.12)" if is_a else "rgba(255,255,255,0.02)"
            border= "2px solid #78a8f0" if is_a else "1px solid rgba(255,255,255,0.07)"

            thumb = _layer_thumb(psd_json_for_thumb, l['idx'], tuple(l['rect']), size=56)
            th_html = (
                f'<img src="data:image/jpeg;base64,{thumb}" '
                f'style="width:56px;height:56px;object-fit:cover;'
                f'border-radius:4px;flex-shrink:0;margin-right:8px;'
                f'border:1px solid rgba(255,255,255,0.15)">'
                if thumb else
                f'<div style="width:56px;height:56px;background:rgba(255,255,255,0.05);'
                f'border-radius:4px;flex-shrink:0;margin-right:8px;'
                f'display:flex;align-items:center;justify-content:center;font-size:20px">🖼️</div>'
            )

            lw, lh = l['w'], l['h']
            display_label = l.get('display_label') or f'이미지 {order_no}'

            st.markdown(
                f'<div style="background:{bg};border:{border};border-radius:8px;'
                f'padding:6px 10px;margin-bottom:2px;display:flex;align-items:center">'
                f'{th_html}'
                f'<div style="flex:1;min-width:0">'
                f'<div style="color:{"#78a8f0" if is_a else "#bbb"};font-size:12px;'
                f'font-weight:{"700" if is_a else "400"};overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">'
                f'{s} {display_label}</div>'
                f'<div style="color:#666;font-size:10px">'
                f'{lw}×{lh}px</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "📂 이미지 선택" if not is_a else "📂 이미지 업로드 ↓",
                key=f"pib{l['idx']}",
                use_container_width=True,
                type="primary" if is_a else "secondary",
            ):
                st.session_state.pu_act = l['idx']
                st.rerun()

            # 선택된 레이어 → 업로더 바로 아래
            if is_a:
                cur = inp.get(l['idx'], {})
                st.caption(f"권장: {lw}×{lh}px")
                up = st.file_uploader(
                    "파일 선택 (JPG/PNG)",
                    type=["jpg","jpeg","png"],
                    key=f"pimg{l['idx']}",
                )
                if up:
                    raw_img = up.read()
                    inp[l['idx']] = {'value': raw_img, 'type': 'image'}
                    st.session_state.pu_inp = inp
                    th2 = Image.open(io.BytesIO(raw_img))
                    th2.thumbnail((200,100))
                    st.image(th2, caption="교체할 이미지")
                elif cur.get('value'):
                    st.success("✓ 이미지 교체 예정")
                st.markdown("---")

    # ── 2열: 텍스트 교체 ──────────────────
    with col_txt:
        td = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
        st.markdown(
            f'<div style="color:#C8A876;font-weight:700;font-size:13px;'
            f'padding:6px 10px;background:rgba(200,168,118,0.08);'
            f'border-radius:6px;margin-bottom:8px">✏️ 텍스트 교체 {td}/{len(txt_lays)}</div>',
            unsafe_allow_html=True)

        for order_no, l in enumerate(txt_lays, start=1):
            is_a  = (act == l['idx'])
            has_v = bool(inp.get(l['idx'],{}).get('value'))
            s     = "✅" if has_v else ("▶" if is_a else "○")
            if st.button(
                f"{s} {l.get('display_label') or f'텍스트 {order_no}'}",
                key=f"ptb{l['idx']}",
                use_container_width=True,
                type="primary" if is_a else "secondary",
            ):
                st.session_state.pu_act = l['idx']
                st.rerun()

            # 선택된 텍스트 레이어 → 입력칸 바로 아래
            if is_a:
                cur  = inp.get(l['idx'], {})
                orig = l.get('text','').split('\n')[0][:60]
                if orig:
                    st.caption(f"원본: {orig}")
                new_txt = st.text_area(
                    "새 텍스트",
                    value=cur.get('value',''),
                    height=80,
                    key=f"ptxt{l['idx']}",
                    placeholder="교체할 텍스트 (비우면 원본 유지)",
                )
                if new_txt.strip():
                    inp[l['idx']] = {'value': new_txt, 'type': 'text'}
                elif l['idx'] in inp:
                    del inp[l['idx']]
                st.session_state.pu_inp = inp
                st.markdown("---")

    # ── 3열: PSD 미리보기 (st.button 없음) ──
    with col_prev:
        st.markdown(
            '<div style="color:#888;font-weight:700;font-size:13px;'
            'padding:6px 10px;background:rgba(255,255,255,0.04);'
            'border-radius:6px;margin-bottom:8px">📄 PSD 미리보기</div>',
            unsafe_allow_html=True)
        st.caption("실시간 교체 미리보기 · 교체 위치는 색상 박스와 번호 배지로 즉시 표시됩니다")

        if st.session_state.pu_prev:
            editable_json = json.dumps([
                {'idx':l['idx'],'type':l['type'],'rect':list(l['rect']),
                 'name':l.get('display_label') or l.get('name',''),'w':l['w'],'h':l['h']}
                for l in editable
            ])
            inp_json = json.dumps({
                str(idx): {
                    'value': (base64.b64encode(v.get('value')).decode() if v.get('type') == 'image' and v.get('value') else v.get('value')),
                    'kind': ('image_bytes' if v.get('type') == 'image' and v.get('value') else 'text_value')
                }
                for idx, v in inp.items() if v.get('value')
            })
            b64 = _make_live_preview(
                st.session_state.pu_prev,
                editable_json, act, inp_json, W, H,
            )
            st.markdown(
                f'<div style="overflow-y:scroll;max-height:900px;'
                f'border:1px solid rgba(255,255,255,0.12);border-radius:8px;background:#111">'
                f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;display:block;">'
                f'</div>'
                f'<div style="color:#888;font-size:10px;text-align:center;margin-top:3px">'
                f'↕ 스크롤 | {W}×{H}px</div>',
                unsafe_allow_html=True,
            )

        act_layer = next((l for l in layers if l['idx']==act), None)
        if act_layer:
            t_col = "#C8A876" if act_layer['type']=='text' else "#78a8f0"
            if act_layer['type'] == 'text':
                order_no = next((i for i, x in enumerate(txt_lays, start=1) if x['idx'] == act_layer['idx']), None)
                active_label = act_layer.get('display_label') or f'텍스트 {order_no or 0}'
            else:
                order_no = next((i for i, x in enumerate(img_lays, start=1) if x['idx'] == act_layer['idx']), None)
                active_label = act_layer.get('display_label') or f'이미지 {order_no or 0}'
            st.markdown(
                f'<div style="color:{t_col};font-weight:700;margin-top:6px;'
                f'padding:6px;background:rgba(255,255,255,0.04);'
                f'border-radius:6px;text-align:center;font-size:12px">'
                f'★ 선택: {active_label}</div>',
                unsafe_allow_html=True)

    st.divider()

    # ── 출력
    st.markdown('<div class="step-header">출력 · PSD 스크립트 생성</div>', unsafe_allow_html=True)
    n_t = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
    n_i = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))

    if n_t + n_i == 0:
        st.warning("교체할 내용을 먼저 입력하세요 (이미지 또는 텍스트)")
    else:
        st.success(f"🖼️ 이미지 {n_i}개 · ✏️ 텍스트 {n_t}개 교체 준비 완료")
        if st.button("⚙️ PSD 스크립트 + 미리보기JPG 생성",
                     use_container_width=True, type="primary", key="pu_gen"):
            with st.spinner("생성 중..."):
                try:
                    txt_rep = {idx:v['value'] for idx,v in inp.items()
                               if v.get('type')=='text' and v.get('value')}
                    img_rep = {idx:v['value'] for idx,v in inp.items()
                               if v.get('type')=='image' and v.get('value')}
                    jsx = build_psd_edit_jsx(
                        psd_filename=f"{meta['name']}.psd",
                        psd_info=info,
                        text_replacements=txt_rep,
                        image_replacements=img_rep,
                    )
                    safe = meta['name'].replace(' ','_')[:30]
                    now  = datetime.now().strftime('%Y%m%d_%H%M')
                    zbuf = io.BytesIO()
                    live_preview_bytes = None
                    if st.session_state.pu_prev:
                        editable_json = json.dumps([
                            {'idx':l['idx'],'type':l['type'],'rect':list(l['rect']),
                             'name':l.get('display_label') or l.get('name',''),'w':l['w'],'h':l['h']}
                            for l in editable
                        ])
                        inp_json = json.dumps({
                            str(idx): {
                                'value': (base64.b64encode(v.get('value')).decode() if v.get('type') == 'image' and v.get('value') else v.get('value')),
                                'kind': ('image_bytes' if v.get('type') == 'image' and v.get('value') else 'text_value')
                            }
                            for idx, v in inp.items() if v.get('value')
                        })
                        live_preview_bytes = base64.b64decode(_make_live_preview(
                            st.session_state.pu_prev, editable_json, act, inp_json, W, H
                        ))

                    with zipfile.ZipFile(zbuf,'w',zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{safe}_{now}.jsx", jsx.encode('utf-8'))
                        if live_preview_bytes:
                            zf.writestr(f"{safe}_{now}_preview.jpg", live_preview_bytes)
                        zf.writestr("README.txt",
                            (f"미샵 템플릿 OS | {meta['name']} | {now}\n"
                             f"이미지 {len(img_rep)}개 텍스트 {len(txt_rep)}개\n"
                             "포토샵 File>Scripts>Browse 에서 jsx 실행 (CS5~CC)")
                            .encode('utf-8'))
                    st.download_button(
                        "⬇️ ZIP 다운로드 (JSX + 미리보기JPG)",
                        data=zbuf.getvalue(),
                        file_name=f"misharp_{safe}_{now}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 완료! 포토샵에서 .jsx 실행 → PSD 자동 저장")
                except Exception as e:
                    st.error(f"오류: {e}")
