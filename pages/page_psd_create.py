"""
page_psd_create.py — ① PSD 템플릿 생성
구조:
  - 상단: PSD 업로드
  - 중단 왼쪽: 레이어 목록 (체크박스+버튼) ← 클릭 완전 보장
  - 중단 오른쪽: 선택된 레이어 정보
  - 하단: 전체 PSD 이미지 (columns 밖, 전체 높이 표시)
  - 최하단: 저장
"""
import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.template_manager import save_psd_template, load_all


def _make_overlay_b64(prev_bytes, editable_layers, active_idx, W_orig, H_orig):
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1, y1 = int(le*sx), int(t*sy)
        x2, y2 = int(r*sx),  int(b*sy)
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
        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=lw)
        if is_a:
            lh = min(30, y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
            drw.text((x1+5,y1+6),
                     f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}",
                     fill=(255,255,255))
    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO(); merged.save(buf,"JPEG",quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">① PSD 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 파일을 업로드하면 레이어를 자동 분석합니다</div>', unsafe_allow_html=True)

    for k, v in [("pc_info",None),("pc_bytes",None),("pc_prev",None),
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
                st.success(f"✅ {info['width']}×{info['height']}px | 텍스트 {n_t}개 · 이미지 {n_p}개 감지")
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
    txt_layers = [l for l in editable_layers if l['type'] == 'text']
    pix_layers = [l for l in editable_layers
                  if l['type'] == 'pixel' and l['w'] > 80 and l['h'] > 80]

    st.divider()
    st.markdown("**STEP 2 · 교체 대상 레이어 지정**")
    st.caption("체크 = 템플릿에 포함 | 버튼 클릭 = 아래 미리보기에서 해당 위치 강조")

    # ── 2열: 레이어목록 | 선택정보
    # col 내부에 추가 st.columns 없음
    col_list, col_info = st.columns([1, 1], gap="large")

    with col_list:
        if txt_layers:
            st.write("**✏️ 텍스트 레이어**")
            for l in txt_layers:
                is_a    = (active == l['idx'])
                checked = eflags.get(l['idx'], True)
                orig    = l['text'].split('\n')[0][:40] if l['text'] else l['name']
                new_ck  = st.checkbox(
                    f"✏️ {l['name'][:30]}",
                    value=checked, key=f"ck_t_{l['idx']}",
                )
                eflags[l['idx']] = new_ck
                st.caption(f"원본: {orig}  |  {l['w']}×{l['h']}px")
                if st.button(
                    "★ 선택됨" if is_a else "↓ 아래 미리보기에서 확인",
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
                new_ck  = st.checkbox(
                    f"🖼️ {l['name'][:28]}  ({l['w']}×{l['h']})",
                    value=checked, key=f"ck_p_{l['idx']}",
                )
                eflags[l['idx']] = new_ck
                st.caption(f"위치: ({l['rect'][1]}, {l['rect'][0]})")
                if st.button(
                    "★ 선택됨" if is_a else "↓ 아래 미리보기에서 확인",
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

    with col_info:
        st.write("**선택된 레이어 정보**")
        if active is not None:
            al = next((l for l in layers if l['idx'] == active), None)
            if al:
                t_col = "#C8A876" if al['type']=='text' else "#78a8f0"
                icon  = "✏️" if al['type']=='text' else "🖼️"
                st.markdown(
                    f'<p style="background:{"rgba(200,168,118,0.1)" if al["type"]=="text" else "rgba(100,160,230,0.08)"};'
                    f'border:2px solid {t_col};border-radius:8px;padding:12px 16px;'
                    f'color:{t_col};font-weight:700;font-size:14px;margin-bottom:8px">'
                    f'{icon} {al["name"]}<br>'
                    f'<span style="color:#888;font-size:11px;font-weight:400">'
                    f'{al["w"]}×{al["h"]}px | 위치: ({al["rect"][1]},{al["rect"][0]})</span></p>',
                    unsafe_allow_html=True,
                )
                if al['type'] == 'text' and al.get('text'):
                    st.write("**원본 텍스트:**")
                    st.code(al['text'].replace('\n','↵')[:200], language=None)
        else:
            st.info("왼쪽에서 레이어 버튼을 클릭하면 정보가 표시됩니다")

        # 전체 현황 요약
        st.write("**전체 현황**")
        checked_t = sum(1 for l in txt_layers if eflags.get(l['idx'], True))
        checked_p = sum(1 for l in pix_layers if eflags.get(l['idx'], True))
        st.write(f"✏️ 텍스트: {checked_t}/{len(txt_layers)}개 선택")
        st.write(f"🖼️ 이미지: {checked_p}/{len(pix_layers)}개 선택")

    # ── columns 밖: 전체 PSD 이미지 (높이 제한 없음)
    st.divider()
    st.markdown("**PSD 미리보기** — 🟡 텍스트  🔵 이미지  ★ 선택됨")
    if st.session_state.pc_prev:
        b64 = _make_overlay_b64(
            st.session_state.pc_prev, editable_layers, active, W, H,
        )
        st.markdown(
            f'<img src="data:image/jpeg;base64,{b64}" '
            f'style="width:100%;display:block;border-radius:8px;'
            f'border:1px solid rgba(255,255,255,0.12);">',
            unsafe_allow_html=True,
        )
        st.caption(f"{W}×{H}px 전체 이미지 | 페이지 스크롤로 확인")

    st.divider()

    # ── STEP 3
    st.markdown("**STEP 3 · 템플릿 저장**")
    c1, c2 = st.columns([3, 1], gap="medium")
    with c1:
        tpl_name = st.text_input("템플릿 이름 *",
                                  placeholder="예: 에코레더자켓_상세v1", key="pc_name")
        tpl_desc = st.text_input("설명 (선택)",
                                  placeholder="시즌, 카테고리 등", key="pc_desc")
    with c2:
        st.write("")
        st.write("")
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
                    tid = save_psd_template(
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
