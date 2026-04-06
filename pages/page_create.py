import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_analyzer import analyze_detail_page, fallback_zones
from utils.template_manager import save_template, load_all
from utils.composer import compose_preview


def show_scrollable_image(img_bytes: bytes, height_px: int = 560, highlight_zone: dict = None, all_zones: list = None):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    W, H = img.size

    if all_zones:
        ov  = img.copy().convert("RGBA")
        drw = ImageDraw.Draw(ov)
        for zone in all_zones:
            zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
            ztype = zone["type"]
            active = highlight_zone and zone["label"] == highlight_zone["label"]
            if active:
                fill    = (255,200,0,65) if ztype=="image" else (0,160,255,65)
                outline = (255,200,0,255) if ztype=="image" else (0,160,255,255)
                drw.rectangle([zx,zy,zx+zw,zy+zh], fill=fill, outline=outline, width=5)
                drw.rectangle([zx,zy,zx+zw,zy+38], fill=(0,0,0,170))
                drw.text((zx+8,zy+9), f"{'[IMG]' if ztype=='image' else '[TXT]'} {zone['label']}", fill=(255,255,255,255))
            else:
                col = (200,168,118,80) if ztype=="image" else (100,160,230,80)
                drw.rectangle([zx,zy,zx+zw,zy+zh], outline=col, width=2)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    st.markdown(
        f'<img src="data:image/jpeg;base64,{b64}" '
        f'style="width:100%;display:block;border-radius:8px;'
        f'border:1px solid rgba(255,255,255,0.12);">',
        unsafe_allow_html=True,
    )
    st.caption(f"{W}×{H}px | 페이지 스크롤로 전체 확인")


def render():
    # 세션 초기화 (없으면 생성)
    for _k, _v in [("openai_api_key",""), ("c_source",None), ("c_zones",[]),
                   ("c_canvas",[800,1200]), ("c_preview",None), ("c_active_zone",None)]:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    st.markdown('<div class="section-title">② JPG 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">상세페이지 JPG를 올리면 AI가 이미지·카피 영역을 자동 감지합니다. 수정 후 템플릿으로 저장하세요.</div>', unsafe_allow_html=True)

    defaults = {"c_zones":[], "c_source":None, "c_preview":None,
                "c_canvas":[900,10000], "c_active_zone":None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── STEP 1
    st.markdown('<div class="step-header">STEP 1 · 이미지 업로드 및 AI 분석</div>', unsafe_allow_html=True)

    col_up, col_key = st.columns([3,2], gap="large")
    with col_up:
        uploaded = st.file_uploader("상세페이지 JPG / PNG 업로드 (세로 길이 제한 없음)",
                                    type=["jpg","jpeg","png"], key="c_upload")
        if uploaded:
            raw = uploaded.read()
            img = Image.open(io.BytesIO(raw))
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            if img.mode != "RGB":
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=95)
            st.session_state.c_source = buf.getvalue()
            st.session_state.c_canvas = list(img.size)
            st.session_state.c_preview = None
            st.success(f"✓ 업로드 완료 — {img.size[0]}×{img.size[1]}px | {len(raw)/1024:.0f}KB")

    with col_key:
        st.markdown("**OpenAI API 키**")
        st.caption("GPT-4o Vision 분석용 | 한 번 입력하면 세션 동안 유지")
        api_key_input = st.text_input("API Key", type="password",
                                      placeholder="sk-... (한 번 입력 후 유지됨)",
                                      value=st.session_state.openai_api_key, key="c_apikey")
        if api_key_input:
            st.session_state.openai_api_key = api_key_input
        if st.session_state.openai_api_key:
            st.success("✓ API 키 저장됨")

        c1, c2 = st.columns(2)
        with c1:
            ai_btn = st.button("🤖 AI 자동 분석", use_container_width=True, type="primary", key="c_aibtn")
        with c2:
            fb_btn = st.button("📐 기본 구조 적용", use_container_width=True, key="c_fbbtn")

    if ai_btn:
        if not st.session_state.c_source:
            st.error("먼저 이미지를 업로드하세요")
        elif not st.session_state.openai_api_key:
            st.error("OpenAI API 키를 입력하세요")
        else:
            with st.spinner("GPT-4o Vision 분석 중... (10~30초)"):
                result = analyze_detail_page(st.session_state.c_source, st.session_state.openai_api_key)
            if result["error"]:
                st.error(f"분석 오류: {result['error']}")
            else:
                st.session_state.c_zones   = result["zones"]
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
            st.session_state.c_zones   = fallback_zones(W, H)
            st.session_state.c_preview = None
            st.info(f"📐 기본 레이아웃 {len(st.session_state.c_zones)}개 존 적용됨")
            st.rerun()

    st.divider()

    # ── STEP 2
    st.markdown('<div class="step-header">STEP 2 · 존 확인 및 수정</div>', unsafe_allow_html=True)

    col_z, col_p = st.columns([1,1], gap="large")
    W, H = st.session_state.c_canvas

    with col_z:
        zones = st.session_state.c_zones
        if zones:
            st.markdown(f"**감지된 존 ({len(zones)}개)** — 존을 선택하면 오른쪽 미리보기에서 강조됩니다")
            for i, z in enumerate(zones):
                icon      = "🖼️" if z["type"]=="image" else "✏️"
                conf      = z.get("confidence", 0)
                is_active = (st.session_state.c_active_zone == i)
                ztype     = z["type"]
                title_bg  = "rgba(200,168,118,0.15)" if ztype=="image" else "rgba(100,160,230,0.12)"
                title_col = "#C8A876" if ztype=="image" else "#78a8f0"
                border    = f"2px solid {title_col}" if is_active else "1px solid rgba(255,255,255,0.1)"

                st.markdown(f"""
                <div style="background:{title_bg};border:{border};border-radius:8px 8px 0 0;
                            padding:8px 14px;margin-top:10px;
                            display:flex;align-items:center;justify-content:space-between;">
                    <span style="color:{title_col};font-weight:700;font-size:13px">{icon} {z['label']}</span>
                    <span style="color:#888;font-size:11px">신뢰도 {int(conf*100)}%</span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("편집", expanded=is_active):
                    # 이 존 선택 버튼
                    if st.button(f"👁 미리보기에서 확인", key=f"c_focus_{i}"):
                        st.session_state.c_active_zone = i
                        st.rerun()

                    if z.get("note"): st.caption(z["note"])
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_type  = st.selectbox("유형", ["image","text"],
                            index=0 if z["type"]=="image" else 1,
                            format_func=lambda x: "🖼️ 이미지 존" if x=="image" else "✏️ 텍스트 존",
                            key=f"ztype_{i}")
                        new_label = st.text_input("존 이름", value=z["label"], key=f"zlabel_{i}")
                    with ec2:
                        new_x = st.number_input("X (px)", 0, W, z["x"], step=10, key=f"zx_{i}")
                        new_y = st.number_input("Y (px)", 0, H, z["y"], step=10, key=f"zy_{i}")
                    ec3, ec4 = st.columns(2)
                    with ec3:
                        new_w = st.number_input("너비 w", 10, W, z["w"], step=10, key=f"zw_{i}")
                    with ec4:
                        new_h = st.number_input("높이 h", 10, H, z["h"], step=10, key=f"zh_{i}")
                    if new_type == "text":
                        tc1, tc2 = st.columns(2)
                        with tc1:
                            new_dt = st.text_input("기본 텍스트", value=z.get("default_text",""), key=f"zdt_{i}")
                            new_fs = st.number_input("폰트 크기", 12, 200, z.get("font_size",36), key=f"zfs_{i}")
                        with tc2:
                            new_tc = st.color_picker("글자색", z.get("text_color","#222222"), key=f"ztc_{i}")
                            new_al = st.selectbox("정렬", ["center","left","right"],
                                index=["center","left","right"].index(z.get("align","center")),
                                format_func=lambda x:{"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],
                                key=f"zal_{i}")
                    col_upd, col_del = st.columns([3,1])
                    with col_upd:
                        if st.button("✓ 수정 적용", key=f"zupd_{i}", use_container_width=True, type="primary"):
                            zones[i].update({"type":new_type,"label":new_label,"x":new_x,"y":new_y,"w":new_w,"h":new_h})
                            if new_type == "text":
                                zones[i].update({"default_text":new_dt,"font_size":new_fs,"text_color":new_tc,"align":new_al})
                            st.session_state.c_zones   = zones
                            st.session_state.c_preview = None
                            st.rerun()
                    with col_del:
                        if st.button("삭제", key=f"zdel_{i}", use_container_width=True):
                            zones.pop(i)
                            st.session_state.c_zones   = zones
                            st.session_state.c_preview = None
                            st.rerun()
        else:
            st.info("위에서 AI 분석 또는 기본 구조 적용 후 존이 표시됩니다")

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
        st.markdown("**미리보기 — 스크롤로 전체 확인**")

        active_idx  = st.session_state.c_active_zone
        active_zone = zones[active_idx] if (zones and active_idx is not None and active_idx < len(zones)) else None

        if st.button("🔍 존 위치 미리보기 생성", use_container_width=True, key="c_prevbtn"):
            if not st.session_state.c_source:
                st.error("이미지를 먼저 업로드하세요")
            elif not zones:
                st.error("존을 먼저 추가/분석하세요")
            else:
                with st.spinner("미리보기 생성 중..."):
                    pv = compose_preview(st.session_state.c_source, zones, "#FFFFFF", {}, show_guides=True)
                    st.session_state.c_preview = pv
                st.rerun()

        if st.session_state.c_preview:
            show_scrollable_image(st.session_state.c_preview, height_px=580,
                                  highlight_zone=active_zone, all_zones=zones)
        elif st.session_state.c_source:
            show_scrollable_image(st.session_state.c_source, height_px=580,
                                  highlight_zone=active_zone, all_zones=zones if zones else None)
        else:
            st.info("이미지를 업로드하면 여기에 표시됩니다")

        if active_zone:
            ztype = active_zone["type"]
            color = "#C8A876" if ztype=="image" else "#78a8f0"
            st.markdown(f'<div style="text-align:center;color:{color};font-size:12px;font-weight:600;margin-top:6px">▲ 강조 표시: {active_zone["label"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ── STEP 3
    st.markdown('<div class="step-header">STEP 3 · 템플릿 저장</div>', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns([2,1,1], gap="medium")
    with sc1:
        tpl_name = st.text_input("템플릿 이름 *", placeholder="예: 니트자켓_상세v1", key="c_name")
        tpl_desc = st.text_input("설명 (선택)", placeholder="시즌, 카테고리 등", key="c_desc")
    with sc2:
        bg_color = st.color_picker("배경색", "#FFFFFF", key="c_bg")
        st.caption(f"선택: {bg_color}")
    with sc3:
        st.write(""); st.write("")
        if st.button("💾 템플릿 저장", type="primary", use_container_width=True, key="c_save"):
            if not st.session_state.c_source:
                st.error("이미지를 업로드하세요")
            elif not tpl_name.strip():
                st.error("템플릿 이름을 입력하세요")
            elif not st.session_state.c_zones:
                st.error("최소 1개 이상의 존이 필요합니다")
            else:
                with st.spinner("저장 중..."):
                    tid = save_template(tpl_name.strip(), st.session_state.c_source,
                                        st.session_state.c_zones, bg_color, tpl_desc.strip())
                st.success(f"✅ 저장 완료! ID: {tid} | 존 {len(st.session_state.c_zones)}개")
                st.balloons()
                for k in ["c_zones","c_source","c_preview","c_active_zone"]:
                    st.session_state[k] = [] if k=="c_zones" else None
                st.rerun()

    st.caption(f"현재 저장된 템플릿: {len(load_all())}개")
