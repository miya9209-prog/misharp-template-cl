"""
page_create.py - ① 템플릿 생성
긴 이미지 지원: 세로 분할 표시
API 키 세션 유지
"""
import streamlit as st
import io, sys, os, base64
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_analyzer import analyze_detail_page, fallback_zones
from utils.template_manager import save_template, load_all
from utils.composer import compose_preview


def show_long_image(img_bytes: bytes, caption: str = "", max_width: int = 400):
    """
    세로가 긴 상세페이지 이미지를 base64로 직접 렌더링.
    Streamlit st.image()는 매우 긴 이미지를 자동 압축하므로 HTML img 태그 사용.
    """
    b64 = base64.b64encode(img_bytes).decode()
    st.markdown(
        f'<img src="data:image/jpeg;base64,{b64}" '
        f'style="width:100%;max-width:{max_width}px;display:block;margin:0 auto;border-radius:6px;" '
        f'alt="{caption}">',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def render():
    st.markdown('<div class="section-title">① 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">상세페이지 JPG를 올리면 AI가 이미지·카피 영역을 자동 감지합니다. 수정 후 템플릿으로 저장하세요.</div>', unsafe_allow_html=True)

    # 세션 초기화
    defaults = {"c_zones":[],"c_source":None,"c_preview":None,"c_canvas":[900,10000]}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ════════════════════════════════════
    # STEP 1 · 이미지 업로드 + AI 분석
    # ════════════════════════════════════
    st.markdown('<div class="step-header">STEP 1 · 이미지 업로드 및 AI 분석</div>', unsafe_allow_html=True)

    col_up, col_key = st.columns([3, 2], gap="large")

    with col_up:
        uploaded = st.file_uploader(
            "상세페이지 JPG / PNG 업로드 (용량 제한 없음)",
            type=["jpg","jpeg","png"],
            key="c_upload",
        )
        if uploaded:
            raw = uploaded.read()
            img = Image.open(io.BytesIO(raw))
            # EXIF 회전 보정
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            # RGB 변환
            if img.mode != "RGB":
                img = img.convert("RGB")
            # 저장용 bytes 재생성
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=95)
            st.session_state.c_source = buf.getvalue()
            st.session_state.c_canvas = list(img.size)
            st.success(f"✓ 업로드 완료 — {img.size[0]}×{img.size[1]}px | {len(raw)/1024:.0f}KB")

    with col_key:
        st.markdown("**OpenAI API 키**")
        st.caption("GPT-4o Vision 분석용 | 입력 후 저장됩니다")
        # API 키 세션 유지 — 한 번 입력하면 재입력 불필요
        api_key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-... (한 번 입력 후 유지됨)",
            value=st.session_state.openai_api_key,
            key="c_apikey",
        )
        if api_key_input:
            st.session_state.openai_api_key = api_key_input

        if st.session_state.openai_api_key:
            st.success("✓ API 키 저장됨 (재입력 불필요)")

        c1, c2 = st.columns(2)
        with c1:
            ai_btn = st.button("🤖 AI 자동 분석", use_container_width=True, type="primary", key="c_aibtn")
        with c2:
            fb_btn = st.button("📐 기본 구조 적용", use_container_width=True, key="c_fbbtn",
                               help="API 없이 일반 레이아웃으로 존 자동 배치")

    if ai_btn:
        if not st.session_state.c_source:
            st.error("먼저 이미지를 업로드하세요")
        elif not st.session_state.openai_api_key:
            st.error("OpenAI API 키를 입력하세요")
        else:
            with st.spinner("GPT-4o Vision이 분석 중입니다... (10~30초 소요)"):
                result = analyze_detail_page(st.session_state.c_source, st.session_state.openai_api_key)
            if result["error"]:
                st.error(f"분석 오류: {result['error']}")
            else:
                st.session_state.c_zones = result["zones"]
                st.session_state.c_preview = None
                st.success(f"✅ 분석 완료 — {len(result['zones'])}개 존 감지")
                if result.get("analysis_summary"):
                    st.info(f"📋 {result['analysis_summary']}")
                st.rerun()

    if fb_btn:
        if not st.session_state.c_source:
            st.error("먼저 이미지를 업로드하세요")
        else:
            W, H = st.session_state.c_canvas
            st.session_state.c_zones = fallback_zones(W, H)
            st.session_state.c_preview = None
            st.info(f"📐 기본 레이아웃 {len(st.session_state.c_zones)}개 존 적용됨")
            st.rerun()

    st.divider()

    # ════════════════════════════════════
    # STEP 2 · 존 확인 및 수정
    # ════════════════════════════════════
    st.markdown('<div class="step-header">STEP 2 · 존 확인 및 수정</div>', unsafe_allow_html=True)

    col_z, col_p = st.columns([1,1], gap="large")
    W, H = st.session_state.c_canvas

    with col_z:
        zones = st.session_state.c_zones
        if zones:
            st.markdown(f"**감지된 존 ({len(zones)}개)**")
            for i, z in enumerate(zones):
                icon = "🖼️" if z["type"]=="image" else "✏️"
                conf = z.get("confidence", 0)
                with st.expander(f"{icon} {z['label']}  신뢰도 {int(conf*100)}%", expanded=False):
                    if z.get("note"):
                        st.caption(z["note"])
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_type = st.selectbox(
                            "유형", ["image","text"],
                            index=0 if z["type"]=="image" else 1,
                            format_func=lambda x: "🖼️ 이미지 존" if x=="image" else "✏️ 텍스트 존",
                            key=f"ztype_{i}",
                        )
                        new_label = st.text_input("존 이름", value=z["label"], key=f"zlabel_{i}")
                    with ec2:
                        new_x = st.number_input("X (px)", 0, W, z["x"], step=10, key=f"zx_{i}")
                        new_y = st.number_input("Y (px)", 0, H, z["y"], step=10, key=f"zy_{i}")
                    ec3, ec4 = st.columns(2)
                    with ec3:
                        new_w = st.number_input("너비 w (px)", 10, W, z["w"], step=10, key=f"zw_{i}")
                    with ec4:
                        new_h = st.number_input("높이 h (px)", 10, H, z["h"], step=10, key=f"zh_{i}")
                    if new_type == "text":
                        tc1, tc2 = st.columns(2)
                        with tc1:
                            new_dt = st.text_input("기본 텍스트", value=z.get("default_text",""), key=f"zdt_{i}")
                            new_fs = st.number_input("폰트 크기", 12, 200, z.get("font_size",36), key=f"zfs_{i}")
                        with tc2:
                            new_tc = st.color_picker("글자색", z.get("text_color","#222222"), key=f"ztc_{i}")
                            new_al = st.selectbox(
                                "정렬", ["center","left","right"],
                                index=["center","left","right"].index(z.get("align","center")),
                                format_func=lambda x: {"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],
                                key=f"zal_{i}",
                            )
                    col_upd, col_del = st.columns([3,1])
                    with col_upd:
                        if st.button("✓ 수정 적용", key=f"zupd_{i}", use_container_width=True, type="primary"):
                            zones[i].update({"type":new_type,"label":new_label,"x":new_x,"y":new_y,"w":new_w,"h":new_h})
                            if new_type == "text":
                                zones[i].update({"default_text":new_dt,"font_size":new_fs,"text_color":new_tc,"align":new_al})
                            st.session_state.c_zones = zones
                            st.session_state.c_preview = None
                            st.rerun()
                    with col_del:
                        if st.button("삭제", key=f"zdel_{i}", use_container_width=True):
                            zones.pop(i)
                            st.session_state.c_zones = zones
                            st.session_state.c_preview = None
                            st.rerun()
        else:
            st.info("위에서 AI 분석 또는 기본 구조 적용 후 존이 표시됩니다")

        # 존 직접 추가
        st.markdown("**➕ 존 직접 추가**")
        with st.expander("새 존 추가", expanded=False):
            ac1, ac2 = st.columns(2)
            with ac1:
                a_type  = st.selectbox("유형", ["image","text"],
                    format_func=lambda x:"🖼️ 이미지" if x=="image" else "✏️ 텍스트", key="add_type")
                a_label = st.text_input("존 이름", placeholder="예: 메인이미지", key="add_label")
            with ac2:
                a_x = st.number_input("X", 0, W, 0, step=10, key="add_x")
                a_y = st.number_input("Y", 0, H, 0, step=10, key="add_y")
            ac3, ac4 = st.columns(2)
            with ac3:
                a_w = st.number_input("너비(w)", 10, W, W, step=10, key="add_w")
            with ac4:
                a_h = st.number_input("높이(h)", 10, H, 400, step=10, key="add_h")
            if a_type == "text":
                at1, at2 = st.columns(2)
                with at1:
                    a_dt = st.text_input("기본 텍스트", key="add_dt")
                    a_fs = st.number_input("폰트 크기", 12, 200, 36, key="add_fs")
                with at2:
                    a_tc = st.color_picker("글자색", "#222222", key="add_tc")
                    a_al = st.selectbox("정렬", ["center","left","right"],
                        format_func=lambda x:{"center":"가운데","left":"왼쪽","right":"오른쪽"}[x], key="add_al")
            if st.button("존 추가", use_container_width=True, type="primary", key="add_btn"):
                if not a_label:
                    st.error("존 이름을 입력하세요")
                else:
                    st.session_state.c_zones.append({
                        "type":a_type,"label":a_label,"x":a_x,"y":a_y,"w":a_w,"h":a_h,
                        "confidence":1.0,"note":"수동 추가",
                        "default_text": a_dt if a_type=="text" else "",
                        "font_size":    a_fs if a_type=="text" else 36,
                        "text_color":   a_tc if a_type=="text" else "#222222",
                        "align":        a_al if a_type=="text" else "center",
                    })
                    st.session_state.c_preview = None
                    st.rerun()

    with col_p:
        st.markdown("**🔍 미리보기**")
        st.caption("존 위치를 이미지 위에서 확인할 수 있습니다")

        if st.button("미리보기 생성", use_container_width=True, key="c_prevbtn"):
            if not st.session_state.c_source:
                st.error("이미지를 먼저 업로드하세요")
            elif not st.session_state.c_zones:
                st.error("존을 먼저 추가/분석하세요")
            else:
                with st.spinner("미리보기 생성 중..."):
                    pv = compose_preview(
                        st.session_state.c_source,
                        st.session_state.c_zones,
                        "#FFFFFF", {}, show_guides=True,
                    )
                    st.session_state.c_preview = pv
                st.rerun()

        if st.session_state.c_preview:
            pv_bytes = st.session_state.c_preview
            pv_img = Image.open(io.BytesIO(pv_bytes))
            W_img, H_img = pv_img.size
            st.caption(f"전체 크기: {W_img}×{H_img}px | 금색=이미지존 · 파랑=텍스트존")
            # base64로 전체 이미지 렌더링 (잘림 없음)
            show_long_image(pv_bytes, caption="", max_width=420)

        elif st.session_state.c_source:
            src_bytes = st.session_state.c_source
            src_img = Image.open(io.BytesIO(src_bytes))
            st.caption(f"원본: {src_img.size[0]}×{src_img.size[1]}px")
            show_long_image(src_bytes, caption="원본 이미지 (전체)", max_width=420)
        else:
            st.info("이미지를 업로드하면 여기에 표시됩니다")

    st.divider()

    # ════════════════════════════════════
    # STEP 3 · 저장
    # ════════════════════════════════════
    st.markdown('<div class="step-header">STEP 3 · 템플릿 저장</div>', unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns([2,1,1], gap="medium")
    with sc1:
        tpl_name = st.text_input("템플릿 이름 *", placeholder="예: 니트자켓_상세v1", key="c_name")
        tpl_desc = st.text_input("설명 (선택)", placeholder="시즌, 카테고리 등", key="c_desc")
    with sc2:
        bg_color = st.color_picker("배경색", "#FFFFFF", key="c_bg")
        st.caption(f"선택된 색: {bg_color}")
    with sc3:
        st.write("")
        st.write("")
        if st.button("💾 템플릿 저장", type="primary", use_container_width=True, key="c_save"):
            if not st.session_state.c_source:
                st.error("이미지를 업로드하세요")
            elif not tpl_name.strip():
                st.error("템플릿 이름을 입력하세요")
            elif not st.session_state.c_zones:
                st.error("최소 1개 이상의 존이 필요합니다")
            else:
                with st.spinner("저장 중..."):
                    tid = save_template(
                        tpl_name.strip(), st.session_state.c_source,
                        st.session_state.c_zones, bg_color, tpl_desc.strip(),
                    )
                st.success(f"✅ 저장 완료! ID: {tid} | 존 {len(st.session_state.c_zones)}개")
                st.balloons()
                st.session_state.c_zones = []
                st.session_state.c_source = None
                st.session_state.c_preview = None
                st.rerun()

    total = len(load_all())
    st.caption(f"현재 저장된 템플릿: {total}개")
