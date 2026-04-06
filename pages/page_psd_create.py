"""
page_psd_create.py — ① PSD 템플릿 생성
3열 구조:
  [1열] 텍스트 레이어 목록 + 체크박스
  [2열] 이미지 레이어 목록 + 체크박스
  [3열] PSD 전체 이미지 (스크롤)
"""
import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.template_manager import save_psd_template, load_all


def _draw_overlay(prev_bytes, editable_layers, eflags, W_orig, H_orig):
    """체크된 레이어만 강조 표시"""
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0, 0, 0, 0))
    drw = ImageDraw.Draw(ov)
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1, y1 = int(le * sx), int(t  * sy)
        x2, y2 = int(r  * sx), int(b  * sy)
        if x2 - x1 < 3 or y2 - y1 < 3:
            continue
        lt      = l['type']
        checked = eflags.get(l['idx'], True)
        if checked:
            fill    = (255, 200, 0, 35)   if lt == 'text' else (100, 160, 255, 28)
            outline = (255, 200, 0, 200)  if lt == 'text' else (100, 160, 255, 180)
            lw = 2
        else:
            fill    = (80, 80, 80, 15)
            outline = (80, 80, 80, 80)
            lw = 1
        drw.rectangle([x1, y1, x2, y2], fill=fill, outline=outline, width=lw)
    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">① PSD 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 파일을 업로드하면 레이어를 자동 분석합니다. 체크박스로 교체 대상을 지정한 후 저장하세요.</div>', unsafe_allow_html=True)

    for k, v in [("pc_info", None), ("pc_bytes", None), ("pc_prev", None),
                 ("pc_fname", ""), ("pc_editable", {})]:
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
                n_t = sum(1 for l in info['layers'] if l['type'] == 'text' and l['w'] > 0)
                n_p = sum(1 for l in info['layers'] if l['type'] == 'pixel' and l['w'] > 80)
                st.success(f"✅ {info['width']}×{info['height']}px | 텍스트 {n_t}개 · 이미지 {n_p}개 레이어 감지")
            except Exception as e:
                st.error(f"PSD 파싱 오류: {e}")
                return

    if not st.session_state.pc_info:
        st.info("PSD 파일을 올리면 레이어 구조를 자동으로 분석합니다")
        return

    info    = st.session_state.pc_info
    layers  = info['layers']
    W, H    = info['width'], info['height']
    eflags  = st.session_state.pc_editable

    editable_layers = [l for l in layers
                       if l['type'] in ('text', 'pixel')
                       and l['w'] > 30 and l['h'] > 10
                       and l['idx'] != 0]
    txt_layers = [l for l in editable_layers if l['type'] == 'text']
    pix_layers = [l for l in editable_layers
                  if l['type'] == 'pixel' and l['w'] > 80 and l['h'] > 80]

    st.divider()
    st.markdown("**STEP 2 · 교체 대상 레이어 지정**")
    st.caption("✅ 체크 = 템플릿에 포함 | 해제 = 제외 | 우측 이미지에서 노란색=텍스트, 파란색=이미지")

    # ── 3열 구조
    col_txt, col_img, col_prev = st.columns([1, 1, 1], gap="medium")

    # ── 1열: 텍스트 레이어
    with col_txt:
        checked_t = sum(1 for l in txt_layers if eflags.get(l['idx'], True))
        st.markdown(
            f'<div style="color:#C8A876;font-weight:700;font-size:13px;'
            f'padding:6px 10px;background:rgba(200,168,118,0.08);'
            f'border-radius:6px;margin-bottom:8px">'
            f'✏️ 텍스트 레이어 ({checked_t}/{len(txt_layers)})</div>',
            unsafe_allow_html=True,
        )
        for l in txt_layers:
            checked = eflags.get(l['idx'], True)
            orig    = l['text'].split('\n')[0][:30] if l['text'] else ''
            new_ck  = st.checkbox(
                f"{l['name'][:28]}",
                value=checked,
                key=f"ck_t_{l['idx']}",
            )
            if orig:
                st.caption(orig)
            eflags[l['idx']] = new_ck

    # ── 2열: 이미지 레이어
    with col_img:
        checked_p = sum(1 for l in pix_layers if eflags.get(l['idx'], True))
        st.markdown(
            f'<div style="color:#78a8f0;font-weight:700;font-size:13px;'
            f'padding:6px 10px;background:rgba(100,160,230,0.08);'
            f'border-radius:6px;margin-bottom:8px">'
            f'🖼️ 이미지 레이어 ({checked_p}/{len(pix_layers)})</div>',
            unsafe_allow_html=True,
        )
        for l in pix_layers:
            checked = eflags.get(l['idx'], True)
            new_ck  = st.checkbox(
                f"{l['name'][:26]}",
                value=checked,
                key=f"ck_p_{l['idx']}",
            )
            st.caption(f"{l['w']}×{l['h']}px")
            eflags[l['idx']] = new_ck

    # ── 3열: PSD 미리보기 (스크롤)
    with col_prev:
        st.markdown(
            '<div style="color:#888;font-weight:700;font-size:13px;'
            'padding:6px 10px;background:rgba(255,255,255,0.04);'
            'border-radius:6px;margin-bottom:8px">'
            '📄 PSD 미리보기</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.pc_prev:
            b64 = _draw_overlay(
                st.session_state.pc_prev, editable_layers, eflags, W, H,
            )
            st.markdown(f"""
<div style="height:580px;overflow-y:scroll;overflow-x:hidden;
            border:1px solid rgba(255,255,255,0.12);border-radius:8px;
            background:#111;">
  <img src="data:image/jpeg;base64,{b64}" style="width:100%;display:block;">
</div>
<div style="color:#888;font-size:11px;text-align:center;margin-top:4px">
  ↕ 스크롤 | {W}×{H}px | 🟡 텍스트 🔵 이미지
</div>""", unsafe_allow_html=True)

    st.session_state.pc_editable = eflags

    # 지정 현황
    st.divider()
    cnt = sum(1 for v in eflags.values() if v)
    if cnt:
        st.success(f"✅ 총 {cnt}개 레이어 교체 대상 지정 (텍스트 {checked_t}개 · 이미지 {checked_p}개)")
    else:
        st.warning("교체할 레이어를 1개 이상 체크하세요")

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
                        name=tpl_name.strip(),
                        psd_bytes=st.session_state.pc_bytes,
                        psd_info=save_info,
                        description=tpl_desc.strip(),
                    )
                st.success("✅ PSD 템플릿 저장 완료!")
                st.balloons()
                for k in ["pc_info", "pc_bytes", "pc_prev", "pc_fname"]:
                    st.session_state[k] = None
                st.session_state.pc_editable = {}
                st.rerun()

    st.caption(f"현재 저장된 템플릿: {len(load_all())}개")
