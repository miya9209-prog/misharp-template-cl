"""
page_use.py
───────────
② 템플릿 활용
  1) 저장된 템플릿 선택
  2) 존별 이미지 업로드 / 카피 입력
  3) 미리보기 확인
  4) PSD + JPG ZIP 다운로드
"""

import streamlit as st
import io
import sys
import os
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_source_bytes, get_thumb_b64
from utils.composer import compose_preview, build_output_zip


def render():
    st.markdown("""
    <div class="section-header">
        <div class="section-title">② 템플릿 활용</div>
        <div class="section-desc">
            저장된 템플릿을 선택하고 이미지·카피를 입력한 뒤 PSD·JPG로 출력하세요
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_tpl = load_all()

    if not all_tpl:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1.5px dashed rgba(255,255,255,0.1);
                    border-radius:12px;padding:80px;text-align:center;color:rgba(255,255,255,0.25)">
            <div style="font-size:48px;margin-bottom:16px">📂</div>
            <div style="font-size:15px;margin-bottom:8px">저장된 템플릿이 없습니다</div>
            <div style="font-size:13px">① 템플릿 생성 탭에서 먼저 템플릿을 만들어보세요</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 세션 초기화
    if "use_selected" not in st.session_state:
        st.session_state.use_selected = None
    if "use_inputs" not in st.session_state:
        st.session_state.use_inputs = {}
    if "use_preview" not in st.session_state:
        st.session_state.use_preview = None

    # ══════════════════════════════════════════
    # 템플릿 선택 화면
    # ══════════════════════════════════════════
    if not st.session_state.use_selected:
        st.markdown("### 템플릿 선택")
        st.caption(f"저장된 템플릿 {len(all_tpl)}개")

        cols_per_row = 3
        tpl_list = list(all_tpl.items())
        for row_start in range(0, len(tpl_list), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for col_idx, (tid, meta) in enumerate(tpl_list[row_start:row_start+cols_per_row]):
                with cols[col_idx]:
                    # 썸네일
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.08)">',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="background:rgba(255,255,255,0.04);border-radius:8px;'
                            f'height:160px;display:flex;align-items:center;justify-content:center;'
                            f'color:rgba(255,255,255,0.2);font-size:32px">🖼️</div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown(f"**{meta['name']}**")
                    img_cnt = sum(1 for z in meta["zones"] if z["type"]=="image")
                    txt_cnt = sum(1 for z in meta["zones"] if z["type"]=="text")
                    st.caption(
                        f"🖼️ 이미지존 {img_cnt}개 · ✏️ 텍스트존 {txt_cnt}개 · "
                        f"{meta['canvas_size'][0]}×{meta['canvas_size'][1]}px"
                    )
                    if meta.get("description"):
                        st.caption(meta["description"])

                    if st.button("이 템플릿 사용 →", key=f"sel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.use_selected = tid
                        st.session_state.use_inputs = {}
                        st.session_state.use_preview = None
                        st.rerun()
        return

    # ══════════════════════════════════════════
    # 선택된 템플릿 작업 화면
    # ══════════════════════════════════════════
    tid = st.session_state.use_selected
    tpl = load_one(tid)
    if not tpl:
        st.error("템플릿 정보를 불러오지 못했습니다")
        st.session_state.use_selected = None
        return

    source_bytes = get_source_bytes(tid)
    if not source_bytes:
        st.error("템플릿 원본 이미지를 찾을 수 없습니다")
        st.session_state.use_selected = None
        return

    zones = tpl["zones"]

    # 상단 템플릿 정보 바
    img_cnt = sum(1 for z in zones if z["type"]=="image")
    txt_cnt = sum(1 for z in zones if z["type"]=="text")
    st.markdown(f"""
    <div style="background:rgba(200,168,118,0.07);border:1px solid rgba(200,168,118,0.18);
                border-radius:10px;padding:14px 20px;margin-bottom:20px">
        <span style="color:#C8A876;font-weight:700;font-size:16px">📋 {tpl['name']}</span>
        <span style="color:rgba(255,255,255,0.3);font-size:12px;margin-left:14px">
            🖼️ 이미지존 {img_cnt} · ✏️ 텍스트존 {txt_cnt} · 
            {tpl['canvas_size'][0]}×{tpl['canvas_size'][1]}px
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택"):
        st.session_state.use_selected = None
        st.session_state.use_inputs = {}
        st.session_state.use_preview = None
        st.rerun()

    st.divider()

    # ── 2열 레이아웃: 입력 폼 | 미리보기
    col_form, col_prev = st.columns([1, 1], gap="large")

    # ══════════════════════════════════════════
    # 왼쪽: 존별 입력 폼
    # ══════════════════════════════════════════
    with col_form:
        st.markdown("### 콘텐츠 입력")

        inputs = dict(st.session_state.use_inputs)

        for i, zone in enumerate(zones):
            ztype = zone["type"]
            label = zone["label"]
            icon = "🖼️" if ztype == "image" else "✏️"
            W_z, H_z = zone["w"], zone["h"]

            with st.expander(f"{icon} {label}  ({W_z}×{H_z}px)", expanded=True):
                if zone.get("note"):
                    st.caption(zone["note"])

                if ztype == "image":
                    up = st.file_uploader(
                        f"이미지 선택 ({W_z}×{H_z}px 권장)",
                        type=["jpg","jpeg","png"],
                        key=f"use_img_{i}",
                    )
                    if up:
                        raw = up.read()
                        inputs[i] = {"value": raw}
                        thumb = Image.open(io.BytesIO(raw))
                        thumb.thumbnail((160, 160))
                        st.image(thumb, width=120)
                    elif i in inputs and inputs[i].get("value"):
                        st.caption("✓ 이미지 입력됨")

                elif ztype == "text":
                    default_txt = zone.get("default_text", "")
                    cur_val = inputs.get(i, {}).get("value", default_txt)
                    new_text = st.text_area(
                        "카피 입력",
                        value=cur_val,
                        height=80,
                        key=f"use_txt_{i}",
                    )

                    tc1, tc2, tc3 = st.columns(3)
                    with tc1:
                        new_fs = st.number_input(
                            "폰트 크기", 12, 200,
                            int(inputs.get(i, {}).get("font_size", zone.get("font_size", 36))),
                            key=f"use_fs_{i}",
                        )
                    with tc2:
                        new_tc = st.color_picker(
                            "글자색",
                            inputs.get(i, {}).get("text_color", zone.get("text_color", "#222222")),
                            key=f"use_tc_{i}",
                        )
                    with tc3:
                        cur_align = inputs.get(i, {}).get("align", zone.get("align", "center"))
                        new_al = st.selectbox(
                            "정렬",
                            ["center","left","right"],
                            index=["center","left","right"].index(cur_align),
                            format_func=lambda x: {"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],
                            key=f"use_al_{i}",
                        )

                    inputs[i] = {
                        "value": new_text,
                        "font_size": new_fs,
                        "text_color": new_tc,
                        "align": new_al,
                    }

        st.session_state.use_inputs = inputs

        st.divider()

        # ── 미리보기 버튼
        if st.button("🔍 미리보기 생성", use_container_width=True):
            with st.spinner("합성 중..."):
                pv = compose_preview(
                    source_bytes, zones,
                    tpl.get("bg_color", "#FFFFFF"),
                    inputs,
                    show_guides=True,
                )
            st.session_state.use_preview = pv
            st.rerun()

    # ══════════════════════════════════════════
    # 오른쪽: 미리보기 + 다운로드
    # ══════════════════════════════════════════
    with col_prev:
        st.markdown("### 미리보기 & 출력")

        if st.session_state.use_preview:
            pv_img = Image.open(io.BytesIO(st.session_state.use_preview))
            # 상단 미리보기
            crop_h = min(pv_img.height, int(pv_img.width * 1.8))
            st.image(
                pv_img.crop((0, 0, pv_img.width, crop_h)),
                caption=f"미리보기 (상단 {crop_h}px / 전체 {pv_img.height}px)",
                use_container_width=True,
            )
            # 전체 썸네일
            full = pv_img.copy()
            full.thumbnail((140, 2000))
            st.image(full, caption="전체 뷰", width=140)

        elif source_bytes:
            src_img = Image.open(io.BytesIO(source_bytes))
            crop_h = min(src_img.height, int(src_img.width * 1.8))
            st.image(
                src_img.crop((0, 0, src_img.width, crop_h)),
                caption="템플릿 원본 (상단)",
                use_container_width=True,
            )
        else:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.03);border:1.5px dashed rgba(255,255,255,0.1);
                        border-radius:12px;padding:60px;text-align:center;color:rgba(255,255,255,0.2)">
                콘텐츠 입력 후 미리보기를 생성하세요
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── 출력 다운로드
        st.markdown("**📦 출력 파일 다운로드**")

        if st.button("⚙️ PSD + JPG 생성", use_container_width=True, type="primary"):
            # 최소 입력 확인
            missing_images = [
                zones[i]["label"] for i in range(len(zones))
                if zones[i]["type"] == "image" and not st.session_state.use_inputs.get(i, {}).get("value")
            ]
            if missing_images:
                st.warning(f"이미지가 없는 존: {', '.join(missing_images)}\n(빈 투명 레이어로 처리됩니다)")

            with st.spinner("PSD 및 ZIP 생성 중... 잠시만 기다려주세요"):
                try:
                    zip_bytes = build_output_zip(
                        template_meta=tpl,
                        source_bytes=source_bytes,
                        inputs=st.session_state.use_inputs,
                    )
                    safe_name = tpl["name"].replace(" ","_")[:30]
                    st.download_button(
                        label="⬇️ ZIP 다운로드 (PSD + JPG + README)",
                        data=zip_bytes,
                        file_name=f"misharp_{safe_name}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 생성 완료! 다운로드 버튼을 눌러 저장하세요")
                    st.markdown("""
                    <div style="background:rgba(200,168,118,0.06);border:1px solid rgba(200,168,118,0.15);
                                border-radius:8px;padding:14px;font-size:12px;color:rgba(255,255,255,0.5);
                                margin-top:8px;line-height:1.8">
                        📁 ZIP 포함 파일<br>
                        · <b>_preview.jpg</b> — 최종 미리보기<br>
                        · <b>.psd</b> — 포토샵 레이어 파일<br>
                        · <b>README.txt</b> — 사용 안내
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"생성 오류: {e}")
