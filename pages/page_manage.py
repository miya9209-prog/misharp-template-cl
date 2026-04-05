"""
page_manage.py
──────────────
③ 템플릿 관리
  - 저장된 템플릿 목록·상세 확인
  - 삭제
  - 존 구조 요약 확인
"""

import streamlit as st
import io
import sys
import os
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, get_thumb_b64, get_source_bytes, delete_template


def render():
    st.markdown("""
    <div class="section-header">
        <div class="section-title">③ 템플릿 관리</div>
        <div class="section-desc">저장된 템플릿을 확인하고 관리합니다</div>
    </div>
    """, unsafe_allow_html=True)

    all_tpl = load_all()

    if not all_tpl:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1.5px dashed rgba(255,255,255,0.1);
                    border-radius:12px;padding:80px;text-align:center;color:rgba(255,255,255,0.25)">
            <div style="font-size:48px;margin-bottom:16px">🗂️</div>
            <div style="font-size:15px">저장된 템플릿이 없습니다</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # 요약 메트릭
    total = len(all_tpl)
    total_zones = sum(len(m["zones"]) for m in all_tpl.values())
    img_zones = sum(sum(1 for z in m["zones"] if z["type"]=="image") for m in all_tpl.values())
    txt_zones = sum(sum(1 for z in m["zones"] if z["type"]=="text") for m in all_tpl.values())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 템플릿", f"{total}개")
    m2.metric("총 존", f"{total_zones}개")
    m3.metric("이미지 존", f"{img_zones}개")
    m4.metric("텍스트 존", f"{txt_zones}개")

    st.divider()

    # 삭제 확인 상태
    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = None

    # 템플릿 목록 테이블 스타일
    for tid, meta in all_tpl.items():
        with st.container():
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:16px 20px;margin-bottom:12px">
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 3, 1], gap="medium")

            with c1:
                b64 = get_thumb_b64(tid)
                if b64:
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{b64}" '
                        f'style="width:100%;border-radius:6px">',
                        unsafe_allow_html=True,
                    )

            with c2:
                iz = sum(1 for z in meta["zones"] if z["type"]=="image")
                tz = sum(1 for z in meta["zones"] if z["type"]=="text")
                W, H = meta["canvas_size"]

                st.markdown(f"**{meta['name']}**")
                st.caption(
                    f"🖼️ 이미지존 {iz}개 · ✏️ 텍스트존 {tz}개 · "
                    f"{W}×{H}px · 생성: {meta['created_at'][:10]}"
                )
                if meta.get("description"):
                    st.caption(f"📝 {meta['description']}")

                # 존 태그
                tags_html = " ".join([
                    f'<span style="background:rgba({"200,168,118" if z["type"]=="image" else "100,160,230"},0.12);'
                    f'color:{"#C8A876" if z["type"]=="image" else "#78a8f0"};'
                    f'padding:2px 8px;border-radius:4px;font-size:11px;margin-right:4px">'
                    f'{"🖼" if z["type"]=="image" else "✏"} {z["label"]}</span>'
                    for z in meta["zones"]
                ])
                st.markdown(tags_html, unsafe_allow_html=True)

            with c3:
                # 삭제 버튼
                if st.session_state.delete_confirm == tid:
                    st.warning("정말 삭제할까요?")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("예, 삭제", key=f"confirm_del_{tid}", type="primary"):
                            delete_template(tid)
                            st.session_state.delete_confirm = None
                            st.success("삭제되었습니다")
                            st.rerun()
                    with dc2:
                        if st.button("취소", key=f"cancel_del_{tid}"):
                            st.session_state.delete_confirm = None
                            st.rerun()
                else:
                    if st.button("🗑️ 삭제", key=f"del_{tid}", use_container_width=True):
                        st.session_state.delete_confirm = tid
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
