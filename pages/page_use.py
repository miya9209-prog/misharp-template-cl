import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_source_bytes, get_thumb_b64
from utils.composer import compose_preview, build_output_zip


# ── 긴 이미지를 스크롤 가능한 컨테이너로 표시
def show_scrollable_image(img_bytes: bytes, height_px: int = 600, highlight_zone: dict = None, all_zones: list = None):
    """
    세로가 긴 이미지를 고정 높이 + 스크롤 컨테이너로 표시.
    highlight_zone: 현재 선택된 존 (빨간 테두리 강조)
    all_zones: 모든 존 (반투명 오버레이)
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    W, H = img.size

    # 존 오버레이 그리기
    if all_zones:
        overlay = img.copy().convert("RGBA")
        draw = ImageDraw.Draw(overlay)
        for zone in all_zones:
            zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
            ztype = zone["type"]
            is_active = (highlight_zone and zone["label"] == highlight_zone["label"])

            if is_active:
                # 활성 존: 밝은 테두리 + 반투명 채우기
                fill = (255, 200, 0, 60) if ztype == "image" else (0, 160, 255, 60)
                outline = (255, 200, 0, 255) if ztype == "image" else (0, 160, 255, 255)
                draw.rectangle([zx, zy, zx+zw, zy+zh], fill=fill, outline=outline, width=4)
                # 라벨
                draw.rectangle([zx, zy, zx+zw, zy+36], fill=(0,0,0,160))
                draw.text((zx+8, zy+8), f"{'🖼' if ztype=='image' else '✏'} {zone['label']}", fill=(255,255,255,255))
            else:
                # 비활성 존: 얇은 테두리만
                outline_dim = (200,168,118,80) if ztype=="image" else (100,160,230,80)
                draw.rectangle([zx, zy, zx+zw, zy+zh], outline=outline_dim, width=2)

        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # base64 변환
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # 스크롤 가능한 div로 렌더링
    st.markdown(f"""
    <div style="
        height:{height_px}px;
        overflow-y:auto;
        overflow-x:hidden;
        border:1px solid rgba(255,255,255,0.12);
        border-radius:10px;
        background:#111;
        scroll-behavior:smooth;
    ">
        <img src="data:image/jpeg;base64,{b64}"
             style="width:100%;display:block;" />
    </div>
    <div style="color:#888;font-size:11px;margin-top:4px;text-align:center">
        ↕ 스크롤하여 전체 이미지 확인 | {W}×{H}px
    </div>
    """, unsafe_allow_html=True)


# ── 존 카드 HTML (활성/비활성 스타일)
def zone_card_style(is_active: bool, ztype: str) -> str:
    if is_active:
        border_color = "#C8A876" if ztype == "image" else "#78a8f0"
        bg = "rgba(200,168,118,0.1)" if ztype == "image" else "rgba(100,160,230,0.1)"
        return f"border:2px solid {border_color};background:{bg};border-radius:8px;padding:2px;"
    return "border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:2px;"


def render():
    st.markdown('<div class="section-title">② 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 템플릿을 선택하고 이미지·카피를 입력한 뒤 PSD·JPG로 출력하세요</div>', unsafe_allow_html=True)

    all_tpl = load_all()
    if not all_tpl:
        st.info("저장된 템플릿이 없습니다. ① 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    if "u_selected"    not in st.session_state: st.session_state.u_selected    = None
    if "u_inputs"      not in st.session_state: st.session_state.u_inputs      = {}
    if "u_preview"     not in st.session_state: st.session_state.u_preview     = None
    if "u_active_zone" not in st.session_state: st.session_state.u_active_zone = None

    # ══════════════════════════════════════
    # 템플릿 선택 화면
    # ══════════════════════════════════════
    if not st.session_state.u_selected:
        st.markdown("### 템플릿 선택")
        st.caption(f"저장된 템플릿 {len(all_tpl)}개 | 사용할 템플릿을 클릭하세요")
        tpl_list = list(all_tpl.items())
        for row_start in range(0, len(tpl_list), 3):
            cols = st.columns(3, gap="medium")
            for col_idx, (tid, meta) in enumerate(tpl_list[row_start:row_start+3]):
                with cols[col_idx]:
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1)">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="background:rgba(255,255,255,0.05);border-radius:8px;height:140px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.3);font-size:28px">🖼️</div>', unsafe_allow_html=True)
                    st.markdown(f"**{meta['name']}**")
                    iz = sum(1 for z in meta["zones"] if z["type"]=="image")
                    tz = sum(1 for z in meta["zones"] if z["type"]=="text")
                    st.caption(f"🖼️ {iz}개 · ✏️ {tz}개 · {meta['canvas_size'][0]}×{meta['canvas_size'][1]}px")
                    if meta.get("description"): st.caption(meta["description"])
                    if st.button("이 템플릿 사용 →", key=f"sel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.u_selected    = tid
                        st.session_state.u_inputs      = {}
                        st.session_state.u_preview     = None
                        st.session_state.u_active_zone = None
                        st.rerun()
        return

    # ══════════════════════════════════════
    # 선택된 템플릿 작업 화면
    # ══════════════════════════════════════
    tid          = st.session_state.u_selected
    tpl          = load_one(tid)
    source_bytes = get_source_bytes(tid)
    if not tpl or not source_bytes:
        st.error("템플릿 정보를 불러오지 못했습니다")
        st.session_state.u_selected = None
        return

    zones = tpl["zones"]
    iz = sum(1 for z in zones if z["type"]=="image")
    tz = sum(1 for z in zones if z["type"]=="text")
    W_canvas, H_canvas = tpl["canvas_size"]

    st.markdown(f"""
    <div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {tpl['name']}</strong><br>
        <span style="color:#A0A0A0;font-size:12px">🖼️ 이미지존 {iz}개 &nbsp;·&nbsp; ✏️ 텍스트존 {tz}개 &nbsp;·&nbsp; {W_canvas}×{H_canvas}px</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="u_back"):
        st.session_state.u_selected    = None
        st.session_state.u_inputs      = {}
        st.session_state.u_preview     = None
        st.session_state.u_active_zone = None
        st.rerun()

    st.divider()

    # ══════════════════════════════════════
    # 2열: 왼쪽 입력 / 오른쪽 미리보기
    # ══════════════════════════════════════
    col_form, col_prev = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### 콘텐츠 입력")
        st.caption("존을 클릭하면 오른쪽 미리보기에서 해당 위치가 강조됩니다")
        inputs = dict(st.session_state.u_inputs)

        for i, zone in enumerate(zones):
            ztype  = zone["type"]
            label  = zone["label"]
            icon   = "🖼️" if ztype == "image" else "✏️"
            W_z, H_z = zone["w"], zone["h"]

            is_active = (st.session_state.u_active_zone == i)
            active_marker = "◀ 선택됨" if is_active else ""

            # 존 타이틀 — 배경색으로 확실히 구분
            title_bg   = "rgba(200,168,118,0.18)" if ztype == "image" else "rgba(100,160,230,0.15)"
            title_color = "#C8A876" if ztype == "image" else "#78a8f0"
            border_color = "#C8A876" if ztype == "image" else "#78a8f0"
            active_border = f"2px solid {border_color}" if is_active else f"1px solid rgba(255,255,255,0.1)"

            st.markdown(f"""
            <div style="
                background:{title_bg};
                border:{active_border};
                border-radius:8px 8px 0 0;
                padding:8px 14px;
                margin-top:12px;
                margin-bottom:0;
                display:flex; align-items:center; justify-content:space-between;
            ">
                <span style="color:{title_color};font-weight:700;font-size:13px">{icon} {label}</span>
                <span style="color:#888;font-size:11px">{W_z}×{H_z}px &nbsp; {active_marker}</span>
            </div>
            <div style="border:{active_border};border-top:none;border-radius:0 0 8px 8px;padding:12px;margin-bottom:4px;background:rgba(255,255,255,0.02)">
            """, unsafe_allow_html=True)

            if zone.get("note"):
                st.caption(zone["note"])

            if ztype == "image":
                up = st.file_uploader(
                    f"이미지 선택 (권장: {W_z}×{H_z}px)",
                    type=["jpg","jpeg","png"], key=f"u_img_{i}",
                )
                if up:
                    raw = up.read()
                    inputs[i] = {"value": raw}
                    thumb = Image.open(io.BytesIO(raw))
                    thumb.thumbnail((200, 200))
                    st.image(thumb, width=150)
                    st.session_state.u_active_zone = i
                elif i in inputs and inputs[i].get("value"):
                    st.success("✓ 이미지 입력됨")

            else:  # text
                cur_val  = inputs.get(i, {}).get("value", zone.get("default_text", ""))
                new_text = st.text_area("카피 입력", value=cur_val, height=90, key=f"u_txt_{i}")
                tc1, tc2, tc3 = st.columns(3)
                with tc1:
                    new_fs = st.number_input("폰트 크기", 12, 200,
                        int(inputs.get(i,{}).get("font_size", zone.get("font_size", 36))),
                        key=f"u_fs_{i}")
                with tc2:
                    new_tc = st.color_picker("글자색",
                        inputs.get(i,{}).get("text_color", zone.get("text_color","#222222")),
                        key=f"u_tc_{i}")
                with tc3:
                    cur_al = inputs.get(i,{}).get("align", zone.get("align","center"))
                    new_al = st.selectbox("정렬", ["center","left","right"],
                        index=["center","left","right"].index(cur_al),
                        format_func=lambda x:{"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],
                        key=f"u_al_{i}")
                inputs[i] = {"value":new_text,"font_size":new_fs,"text_color":new_tc,"align":new_al}

                # 텍스트 입력 시 해당 존 활성화
                if new_text != zone.get("default_text",""):
                    st.session_state.u_active_zone = i

            # 이 존 미리보기 버튼
            if st.button(f"👁 이 존 미리보기에서 확인", key=f"u_focus_{i}", use_container_width=False):
                st.session_state.u_active_zone = i
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.session_state.u_inputs = inputs

        st.divider()
        if st.button("🔍 전체 미리보기 생성", use_container_width=True, key="u_prevbtn", type="primary"):
            with st.spinner("합성 중..."):
                pv = compose_preview(source_bytes, zones, tpl.get("bg_color","#FFFFFF"), inputs, show_guides=False)
            st.session_state.u_preview = pv
            st.rerun()

    # ══════════════════════════════════════
    # 오른쪽: 미리보기 (스크롤 가능)
    # ══════════════════════════════════════
    with col_prev:
        st.markdown("### 미리보기")

        active_idx  = st.session_state.u_active_zone
        active_zone = zones[active_idx] if active_idx is not None and active_idx < len(zones) else None

        if st.session_state.u_preview:
            # 합성된 미리보기 + 존 오버레이
            st.caption("합성 결과 | 스크롤로 전체 확인")
            show_scrollable_image(
                st.session_state.u_preview,
                height_px=640,
                highlight_zone=active_zone,
                all_zones=zones,
            )
            if active_zone:
                ztype = active_zone["type"]
                color = "#C8A876" if ztype=="image" else "#78a8f0"
                st.markdown(f'<div style="text-align:center;margin-top:6px;color:{color};font-size:12px;font-weight:600">현재 선택: {active_zone["label"]}</div>', unsafe_allow_html=True)
        else:
            # 원본 + 존 위치 오버레이
            st.caption("템플릿 원본 | 스크롤로 전체 확인 | 존 위치 표시됨")
            show_scrollable_image(
                source_bytes,
                height_px=640,
                highlight_zone=active_zone,
                all_zones=zones,
            )
            if active_zone:
                ztype = active_zone["type"]
                color = "#C8A876" if ztype=="image" else "#78a8f0"
                st.markdown(f'<div style="text-align:center;margin-top:6px;color:{color};font-size:12px;font-weight:600">▲ {active_zone["label"]} 위치 강조 표시됨</div>', unsafe_allow_html=True)
            else:
                st.caption("왼쪽 존을 클릭하면 해당 위치가 강조됩니다")

        # 존 목록 요약
        st.markdown("**존 구성**")
        for i, zone in enumerate(zones):
            is_sel = (active_idx == i)
            icon   = "🖼️" if zone["type"]=="image" else "✏️"
            bg     = "rgba(200,168,118,0.12)" if is_sel else "transparent"
            border = "1px solid #C8A876" if is_sel else "1px solid rgba(255,255,255,0.07)"
            y_pct  = int(zone["y"] / tpl["canvas_size"][1] * 100)
            st.markdown(f"""
            <div style="background:{bg};border:{border};border-radius:6px;
                        padding:6px 12px;margin:3px 0;display:flex;
                        align-items:center;justify-content:space-between;cursor:pointer">
                <span style="color:#E0E0E0;font-size:12px">{icon} {zone['label']}</span>
                <span style="color:#666;font-size:11px">Y={zone['y']}px ({y_pct}%)</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶", key=f"jump_{i}", help=f"{zone['label']} 선택"):
                st.session_state.u_active_zone = i
                st.rerun()

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
                    st.success("✅ 생성 완료!")
                    st.caption("ZIP 포함: _preview.jpg · .psd (포토샵 레이어) · README.txt")
                except Exception as e:
                    st.error(f"생성 오류: {e}")
