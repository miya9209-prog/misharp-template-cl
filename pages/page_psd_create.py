"""
page_psd_create.py — ① PSD 템플릿 생성
규칙: st.columns 중첩 없음, st.markdown div 최소화
"""
import streamlit as st
import streamlit.components.v1 as components
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.template_manager import save_psd_template, load_all


def _overlay_b64(prev_bytes, editable_layers, active_idx, W_orig, H_orig):
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1,y1,x2,y2 = int(le*sx),int(t*sy),int(r*sx),int(b*sy)
        if x2-x1 < 3 or y2-y1 < 3: continue
        lt   = l['type']
        is_a = (l['idx'] == active_idx)
        if is_a:
            fill    = (255,200,0,90)  if lt=='text' else (100,160,255,90)
            outline = (255,200,0,255) if lt=='text' else (100,160,255,255)
            lw = 5
        else:
            fill    = (255,200,0,20)  if lt=='text' else (100,160,255,15)
            outline = (255,200,0,110) if lt=='text' else (100,160,255,80)
            lw = 1
        ov_l = Image.new("RGBA", (pW,pH), (0,0,0,0))
        ImageDraw.Draw(ov_l).rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=lw)
        ov = Image.alpha_composite(ov, ov_l)
        if is_a:
            drw2 = ImageDraw.Draw(ov)
            lh = min(30, y2-y1)
            drw2.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
            drw2.text((x1+5,y1+6),
                      f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}",
                      fill=(255,255,255))
    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO(); merged.save(buf,"JPEG",quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">① PSD 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 파일을 업로드하면 레이어를 자동 분석하여 템플릿으로 저장합니다</div>', unsafe_allow_html=True)

    for k,v in [("pc_info",None),("pc_bytes",None),("pc_prev",None),
                ("pc_fname",""),("pc_editable",{}),("pc_active",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── STEP 1
    st.markdown("**STEP 1 · PSD 업로드**")
    uploaded = st.file_uploader("PSD 파일 선택", type=["psd"], key="pc_upload")
    if uploaded:
        with st.spinner("레이어 분석 중..."):
            raw = uploaded.read()
            try:
                info = parse_psd(raw)
                prev = psd_to_preview_jpg(raw, max_width=900)
                st.session_state.pc_info     = info
                st.session_state.pc_bytes    = raw
                st.session_state.pc_prev     = prev
                st.session_state.pc_fname    = uploaded.name
                st.session_state.pc_editable = {}
                st.session_state.pc_active   = None
                n_t = sum(1 for l in info['layers'] if l['type']=='text' and l['w']>0)
                n_p = sum(1 for l in info['layers'] if l['type']=='pixel' and l['w']>80)
                st.success(f"✅ {info['width']}×{info['height']}px | 텍스트 {n_t}개 · 이미지 {n_p}개 레이어 감지")
            except Exception as e:
                st.error(f"PSD 파싱 오류: {e}"); return

    if not st.session_state.pc_info:
        st.info("PSD 파일을 올리면 레이어 구조를 자동으로 분석합니다")
        return

    info   = st.session_state.pc_info
    layers = info['layers']
    W, H   = info['width'], info['height']
    active = st.session_state.pc_active
    eflags = st.session_state.pc_editable

    editable_layers = [l for l in layers
                       if l['type'] in ('text','pixel')
                       and l['w'] > 30 and l['h'] > 10
                       and l['idx'] != 0]
    txt_layers = [l for l in editable_layers if l['type']=='text']
    pix_layers = [l for l in editable_layers if l['type']=='pixel'
                  and l['w']>80 and l['h']>80]

    st.divider()
    st.markdown("**STEP 2 · 교체 대상 레이어 지정**")
    st.caption("체크박스: 교체 대상 여부 | 👁 버튼: 오른쪽 미리보기에서 해당 레이어 확인")

    # ── 2열 (중첩 없음)
    col_list, col_prev = st.columns([1, 1], gap="large")

    with col_list:
        # 텍스트 레이어 — 중첩 columns 없이 체크박스+버튼+정보 세로 배치
        if txt_layers:
            st.write("**✏️ 텍스트 레이어**")
            for l in txt_layers:
                is_a     = (active == l['idx'])
                checked  = eflags.get(l['idx'], True)
                orig_txt = l['text'].split('\n')[0][:40] if l['text'] else l['name']
                t_col    = "#C8A876"

                # 체크박스
                new_ck = st.checkbox(
                    f"✏️ **{l['name'][:28]}**",
                    value=checked,
                    key=f"ck_t_{l['idx']}",
                )
                eflags[l['idx']] = new_ck

                # 원본 텍스트 + 위치 표시
                st.caption(f"원본: {orig_txt}  |  {l['w']}×{l['h']}px")

                # 👁 버튼 (단독, 중첩 없음)
                btn_label = f"▶ 미리보기에서 확인" if not is_a else "★ 현재 선택됨"
                if st.button(btn_label, key=f"fct_{l['idx']}",
                             type="primary" if is_a else "secondary"):
                    st.session_state.pc_active = l['idx']
                    st.rerun()

                st.markdown("---")

        # 이미지 레이어
        if pix_layers:
            st.write("**🖼️ 이미지 레이어**")
            for l in pix_layers:
                is_a    = (active == l['idx'])
                checked = eflags.get(l['idx'], True)

                new_ck = st.checkbox(
                    f"🖼️ **{l['name'][:28]}**  ({l['w']}×{l['h']}px)",
                    value=checked,
                    key=f"ck_p_{l['idx']}",
                )
                eflags[l['idx']] = new_ck

                st.caption(f"위치: ({l['rect'][1]},{l['rect'][0]})")

                btn_label = f"▶ 미리보기에서 확인" if not is_a else "★ 현재 선택됨"
                if st.button(btn_label, key=f"fcp_{l['idx']}",
                             type="primary" if is_a else "secondary"):
                    st.session_state.pc_active = l['idx']
                    st.rerun()

                st.markdown("---")

        st.session_state.pc_editable = eflags
        checked_count = sum(1 for v in eflags.values() if v)
        if checked_count:
            st.success(f"✅ {checked_count}개 레이어 교체 대상 지정됨")
        else:
            st.warning("교체할 레이어를 1개 이상 체크하세요")

    # ── 오른쪽: 미리보기 (이미지만, st.button 없음)
    with col_prev:
        st.write("**PSD 미리보기**")
        st.caption("왼쪽 👁 버튼 클릭 → 해당 레이어 강조 표시")

        if st.session_state.pc_prev:
            # 왼쪽 레이어 목록 높이에 맞게
            n_layers = len(txt_layers) + len(pix_layers)
            viewer_h = max(600, min(n_layers * 90 + 200, 1600))

            b64 = _overlay_b64(
                st.session_state.pc_prev,
                editable_layers, active, W, H,
            )
            html = (
                "<!DOCTYPE html><html><head><style>"
                "body{margin:0;background:#0a0a0f;}"
                f".w{{width:100%;height:{viewer_h}px;overflow-y:scroll;"
                "overflow-x:hidden;background:#111;"
                "border:1px solid rgba(255,255,255,0.12);border-radius:8px;}}"
                "img{width:100%;display:block;}"
                ".h{color:#888;font-size:11px;text-align:center;padding:4px;"
                "font-family:sans-serif;background:#0a0a0f;}"
                "</style></head><body>"
                f'<div class="w"><img src="data:image/jpeg;base64,{b64}"/></div>'
                f'<div class="h">↕ 스크롤 | 🟡 텍스트 🔵 이미지 | {W}×{H}px</div>'
                "</body></html>"
            )
            components.html(html, height=viewer_h+32, scrolling=False)

        if active is not None:
            al = next((l for l in layers if l['idx']==active), None)
            if al:
                t_col = "#C8A876" if al['type']=='text' else "#78a8f0"
                st.write(f"**선택:** {al['name']}")

    st.divider()

    # ── STEP 3
    st.markdown("**STEP 3 · 템플릿 저장**")
    c1, c2 = st.columns([3, 1], gap="medium")
    with c1:
        tpl_name = st.text_input("템플릿 이름 *", placeholder="예: 에코레더자켓_상세v1", key="pc_name")
        tpl_desc = st.text_input("설명 (선택)", placeholder="시즌, 카테고리 등", key="pc_desc")
    with c2:
        st.write("")
        st.write("")
        if st.button("💾 PSD 템플릿 저장", type="primary", use_container_width=True, key="pc_save"):
            if not tpl_name.strip():
                st.error("템플릿 이름을 입력하세요")
            elif not any(eflags.values()):
                st.error("교체할 레이어를 1개 이상 체크하세요")
            else:
                save_info = dict(info)
                save_info['editable_layers'] = {
                    str(idx): True for idx,v in eflags.items() if v
                }
                with st.spinner("저장 중..."):
                    tid = save_psd_template(
                        name        = tpl_name.strip(),
                        psd_bytes   = st.session_state.pc_bytes,
                        psd_info    = save_info,
                        description = tpl_desc.strip(),
                    )
                st.success(f"✅ PSD 템플릿 저장 완료!")
                st.balloons()
                for k in ["pc_info","pc_bytes","pc_prev","pc_fname","pc_active"]:
                    st.session_state[k] = None
                st.session_state.pc_editable = {}
                st.rerun()

    st.caption(f"현재 저장된 템플릿: {len(load_all())}개")
