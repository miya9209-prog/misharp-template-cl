"""
page_psd_create.py — ① PSD 템플릿 생성
- PSD 업로드 → 레이어 자동 파싱
- 교체 대상 레이어 체크
- 미리보기 (스크롤 가능)
- 저장
"""
import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.template_manager import save_psd_template, load_all


def _draw_overlay(prev_bytes, editable_layers, active_idx, W_orig, H_orig):
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1, y1 = int(le*sx), int(t*sy)
        x2, y2 = int(r*sx),  int(b*sy)
        if x2-x1 < 3 or y2-y1 < 3:
            continue
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
        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=lw)
        if is_a:
            lh = min(30, y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
            drw.text((x1+5,y1+6),
                     f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}",
                     fill=(255,255,255))
    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">① PSD 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 파일을 업로드하면 레이어를 자동 분석하여 템플릿으로 저장합니다</div>', unsafe_allow_html=True)

    for k, v in [("pc_info",None),("pc_bytes",None),("pc_prev",None),
                 ("pc_fname",""),("pc_editable",{}),("pc_active",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── STEP 1: 업로드
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
                st.success(f"✅ {info['width']}×{info['height']}px | 텍스트 {n_t}개 · 이미지 {n_p}개 감지")
            except Exception as e:
                st.error(f"PSD 파싱 오류: {e}")
                return

    if not st.session_state.pc_info:
        st.info("PSD 파일을 올리면 레이어 구조를 자동으로 분석합니다")
        return

    info    = st.session_state.pc_info
    layers  = info['layers']
    W, H    = info['width'], info['height']
    active  = st.session_state.pc_active
    eflags  = st.session_state.pc_editable

    editable_layers = [l for l in layers
                       if l['type'] in ('text','pixel')
                       and l['w'] > 30 and l['h'] > 10
                       and l['idx'] != 0]
    txt_layers = [l for l in editable_layers if l['type'] == 'text']
    pix_layers = [l for l in editable_layers
                  if l['type'] == 'pixel' and l['w'] > 80 and l['h'] > 80]

    st.divider()
    st.markdown("**STEP 2 · 교체 대상 레이어 지정**")
    st.caption("✅ 체크 = 교체 가능 레이어로 포함 | 레이어명 클릭 → 우측 미리보기에서 위치 강조")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        if txt_layers:
            st.write("**✏️ 텍스트 레이어**")
            for l in txt_layers:
                is_a    = (active == l['idx'])
                checked = eflags.get(l['idx'], True)
                orig    = l['text'].split('\n')[0][:40] if l['text'] else l['name']
                eflags[l['idx']] = st.checkbox(
                    f"✏️ {l['name'][:30]}",
                    value=checked, key=f"ck_t_{l['idx']}",
                )
                st.caption(f"원본: {orig}  |  {l['w']}×{l['h']}px")
                if st.button(
                    "★ 선택됨" if is_a else "👁 미리보기 위치 확인",
                    key=f"fct_{l['idx']}",
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pc_active = l['idx']
                    st.rerun()
                st.markdown("---")

        if pix_layers:
            st.write("**🖼️ 이미지 레이어**")
            for l in pix_layers:
                is_a    = (active == l['idx'])
                checked = eflags.get(l['idx'], True)
                eflags[l['idx']] = st.checkbox(
                    f"🖼️ {l['name'][:28]}  ({l['w']}×{l['h']})",
                    value=checked, key=f"ck_p_{l['idx']}",
                )
                st.caption(f"위치: ({l['rect'][1]}, {l['rect'][0]})")
                if st.button(
                    "★ 선택됨" if is_a else "👁 미리보기 위치 확인",
                    key=f"fcp_{l['idx']}",
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pc_active = l['idx']
                    st.rerun()
                st.markdown("---")

        st.session_state.pc_editable = eflags
        cnt = sum(1 for v in eflags.values() if v)
        if cnt:
            st.success(f"✅ {cnt}개 레이어 교체 대상 지정됨")
        else:
            st.warning("교체할 레이어를 1개 이상 체크하세요")

    # 오른쪽: 스크롤 가능한 미리보기
    with col_right:
        st.write("**PSD 미리보기**")
        st.caption("🟡 텍스트  🔵 이미지  ★ 선택됨")
        if st.session_state.pc_prev:
            b64 = _draw_overlay(
                st.session_state.pc_prev, editable_layers, active, W, H,
            )
            # 스크롤 가능한 고정 높이 컨테이너
            st.markdown(f"""
<div style="height:600px;overflow-y:scroll;overflow-x:hidden;
            border:1px solid rgba(255,255,255,0.12);border-radius:8px;
            background:#111;">
  <img src="data:image/jpeg;base64,{b64}" style="width:100%;display:block;">
</div>
<div style="color:#888;font-size:11px;text-align:center;margin-top:4px">
  ↕ 스크롤하여 전체 확인 | {W}×{H}px
</div>""", unsafe_allow_html=True)

        if active is not None:
            al = next((l for l in layers if l['idx'] == active), None)
            if al:
                t_col = "#C8A876" if al['type']=='text' else "#78a8f0"
                st.markdown(f'<div style="color:{t_col};font-weight:700;margin-top:8px">선택: {al["name"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ── STEP 3: 저장
    st.markdown("**STEP 3 · 템플릿 저장**")
    c1, c2 = st.columns([3, 1], gap="medium")
    with c1:
        tpl_name = st.text_input("템플릿 이름 *",
                                  placeholder="예: 에코레더자켓_상세v1", key="pc_name")
        tpl_desc = st.text_input("설명 (선택)",
                                  placeholder="시즌, 카테고리 등", key="pc_desc")
    with c2:
        st.write(""); st.write("")
        if st.button("💾 PSD 템플릿 저장", type="primary",
                     use_container_width=True, key="pc_save"):
            if not tpl_name.strip():
                st.error("템플릿 이름을 입력하세요")
            elif not any(eflags.values()):
                st.error("교체할 레이어를 1개 이상 체크하세요")
            else:
                save_info = dict(info)
                save_info['editable_layers'] = {
                    str(idx): True for idx, v in eflags.items() if v
                }
                with st.spinner("저장 중..."):
                    save_psd_template(
                        name=tpl_name.strip(), psd_bytes=st.session_state.pc_bytes,
                        psd_info=save_info, description=tpl_desc.strip(),
                    )
                st.success("✅ PSD 템플릿 저장 완료!")
                st.balloons()
                for k in ["pc_info","pc_bytes","pc_prev","pc_fname","pc_active"]:
                    st.session_state[k] = None
                st.session_state.pc_editable = {}
                st.rerun()

    st.caption(f"현재 저장된 템플릿: {len(load_all())}개")
