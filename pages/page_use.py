import streamlit as st
import io, sys, os
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_source_bytes, get_thumb_b64
from utils.composer import compose_preview, build_output_zip


def render():
    st.markdown('<div class="section-title">② 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 템플릿을 선택하고 이미지·카피를 입력한 뒤 PSD·JPG로 출력하세요</div>', unsafe_allow_html=True)

    all_tpl = load_all()

    if not all_tpl:
        st.info("저장된 템플릿이 없습니다. ① 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    if "u_selected" not in st.session_state: st.session_state.u_selected = None
    if "u_inputs"   not in st.session_state: st.session_state.u_inputs   = {}
    if "u_preview"  not in st.session_state: st.session_state.u_preview  = None

    # ── 템플릿 선택 화면
    if not st.session_state.u_selected:
        st.markdown("### 템플릿 선택")
        st.caption(f"저장된 템플릿 {len(all_tpl)}개")
        tpl_list = list(all_tpl.items())
        cols_per_row = 3
        for row_start in range(0, len(tpl_list), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for col_idx, (tid, meta) in enumerate(tpl_list[row_start:row_start+cols_per_row]):
                with cols[col_idx]:
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.08)">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="background:rgba(255,255,255,0.04);border-radius:8px;height:140px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:28px">🖼️</div>', unsafe_allow_html=True)
                    st.markdown(f"**{meta['name']}**")
                    iz = sum(1 for z in meta["zones"] if z["type"]=="image")
                    tz = sum(1 for z in meta["zones"] if z["type"]=="text")
                    st.caption(f"🖼️ 이미지존 {iz} · ✏️ 텍스트존 {tz} · {meta['canvas_size'][0]}×{meta['canvas_size'][1]}px")
                    if meta.get("description"): st.caption(meta["description"])
                    if st.button("이 템플릿 사용 →", key=f"sel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.u_selected = tid
                        st.session_state.u_inputs = {}
                        st.session_state.u_preview = None
                        st.rerun()
        return

    # ── 선택된 템플릿 작업
    tid = st.session_state.u_selected
    tpl = load_one(tid)
    source_bytes = get_source_bytes(tid)
    if not tpl or not source_bytes:
        st.error("템플릿 정보를 불러오지 못했습니다")
        st.session_state.u_selected = None
        return

    zones = tpl["zones"]
    iz = sum(1 for z in zones if z["type"]=="image")
    tz = sum(1 for z in zones if z["type"]=="text")
    st.info(f"📋 **{tpl['name']}** | 🖼️ 이미지존 {iz} · ✏️ 텍스트존 {tz} · {tpl['canvas_size'][0]}×{tpl['canvas_size'][1]}px")

    if st.button("← 다른 템플릿 선택", key="u_back"):
        st.session_state.u_selected = None
        st.session_state.u_inputs = {}
        st.session_state.u_preview = None
        st.rerun()

    st.divider()
    col_form, col_prev = st.columns([1,1], gap="large")

    with col_form:
        st.markdown("### 콘텐츠 입력")
        inputs = dict(st.session_state.u_inputs)

        for i, zone in enumerate(zones):
            ztype, label = zone["type"], zone["label"]
            icon = "🖼️" if ztype=="image" else "✏️"
            with st.expander(f"{icon} {label}  ({zone['w']}×{zone['h']}px)", expanded=True):
                if zone.get("note"): st.caption(zone["note"])
                if ztype == "image":
                    up = st.file_uploader(f"이미지 선택 ({zone['w']}×{zone['h']}px 권장)",
                                         type=["jpg","jpeg","png"], key=f"u_img_{i}")
                    if up:
                        raw = up.read()
                        inputs[i] = {"value": raw}
                        thumb = Image.open(io.BytesIO(raw)); thumb.thumbnail((160,160))
                        st.image(thumb, width=120)
                    elif i in inputs and inputs[i].get("value"):
                        st.caption("✓ 이미지 입력됨")
                else:
                    cur_val = inputs.get(i, {}).get("value", zone.get("default_text",""))
                    new_text = st.text_area("카피 입력", value=cur_val, height=80, key=f"u_txt_{i}")
                    tc1, tc2, tc3 = st.columns(3)
                    with tc1:
                        new_fs = st.number_input("폰트 크기", 12, 200,
                            int(inputs.get(i,{}).get("font_size", zone.get("font_size",36))), key=f"u_fs_{i}")
                    with tc2:
                        new_tc = st.color_picker("글자색",
                            inputs.get(i,{}).get("text_color", zone.get("text_color","#222222")), key=f"u_tc_{i}")
                    with tc3:
                        cur_al = inputs.get(i,{}).get("align", zone.get("align","center"))
                        new_al = st.selectbox("정렬", ["center","left","right"],
                            index=["center","left","right"].index(cur_al),
                            format_func=lambda x:{"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],
                            key=f"u_al_{i}")
                    inputs[i] = {"value":new_text,"font_size":new_fs,"text_color":new_tc,"align":new_al}

        st.session_state.u_inputs = inputs

        st.divider()
        if st.button("🔍 미리보기 생성", use_container_width=True, key="u_prevbtn"):
            with st.spinner("합성 중..."):
                pv = compose_preview(source_bytes, zones, tpl.get("bg_color","#FFFFFF"), inputs, show_guides=True)
            st.session_state.u_preview = pv
            st.rerun()

    with col_prev:
        st.markdown("### 미리보기 & 출력")
        if st.session_state.u_preview:
            pv_img = Image.open(io.BytesIO(st.session_state.u_preview))
            crop_h = min(pv_img.height, int(pv_img.width * 1.8))
            st.image(pv_img.crop((0,0,pv_img.width,crop_h)), caption=f"미리보기 상단 {crop_h}px", use_container_width=True)
            full = pv_img.copy(); full.thumbnail((140,2000))
            st.image(full, caption="전체 뷰", width=140)
        elif source_bytes:
            src_img = Image.open(io.BytesIO(source_bytes))
            crop_h = min(src_img.height, int(src_img.width * 1.8))
            st.image(src_img.crop((0,0,src_img.width,crop_h)), caption="템플릿 원본", use_container_width=True)

        st.divider()
        st.markdown("**📦 출력 파일 다운로드**")
        if st.button("⚙️ PSD + JPG 생성", use_container_width=True, type="primary", key="u_genbtn"):
            with st.spinner("PSD 및 ZIP 생성 중..."):
                try:
                    zip_bytes = build_output_zip(tpl, source_bytes, st.session_state.u_inputs)
                    safe_name = tpl["name"].replace(" ","_")[:30]
                    st.download_button(
                        "⬇️ ZIP 다운로드 (PSD + JPG + README)",
                        data=zip_bytes,
                        file_name=f"misharp_{safe_name}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 생성 완료! 다운로드 버튼을 눌러 저장하세요")
                    st.caption("ZIP 포함: _preview.jpg · .psd (포토샵 레이어) · README.txt")
                except Exception as e:
                    st.error(f"생성 오류: {e}")
