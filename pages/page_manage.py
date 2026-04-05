import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, get_thumb_b64, delete_template


def render():
    st.markdown('<div class="section-title">③ 템플릿 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 템플릿을 확인하고 관리합니다</div>', unsafe_allow_html=True)

    all_tpl = load_all()
    if not all_tpl:
        st.info("저장된 템플릿이 없습니다")
        return

    total = len(all_tpl)
    total_zones = sum(len(m["zones"]) for m in all_tpl.values())
    iz_all = sum(sum(1 for z in m["zones"] if z["type"]=="image") for m in all_tpl.values())
    tz_all = sum(sum(1 for z in m["zones"] if z["type"]=="text") for m in all_tpl.values())

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("총 템플릿", f"{total}개")
    m2.metric("총 존",     f"{total_zones}개")
    m3.metric("이미지 존", f"{iz_all}개")
    m4.metric("텍스트 존", f"{tz_all}개")
    st.divider()

    if "del_confirm" not in st.session_state:
        st.session_state.del_confirm = None

    for tid, meta in all_tpl.items():
        c1, c2, c3 = st.columns([1,3,1], gap="medium")
        with c1:
            b64 = get_thumb_b64(tid)
            if b64:
                st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px">', unsafe_allow_html=True)
        with c2:
            iz = sum(1 for z in meta["zones"] if z["type"]=="image")
            tz = sum(1 for z in meta["zones"] if z["type"]=="text")
            W, H = meta["canvas_size"]
            st.markdown(f"**{meta['name']}**")
            st.caption(f"🖼️ 이미지존 {iz} · ✏️ 텍스트존 {tz} · {W}×{H}px · {meta['created_at'][:10]}")
            if meta.get("description"): st.caption(f"📝 {meta['description']}")
            tags = " ".join([
                f'<span style="background:rgba({"200,168,118" if z["type"]=="image" else "100,160,230"},0.12);'
                f'color:{"#C8A876" if z["type"]=="image" else "#78a8f0"};'
                f'padding:2px 8px;border-radius:4px;font-size:11px;margin-right:4px">'
                f'{"🖼" if z["type"]=="image" else "✏"} {z["label"]}</span>'
                for z in meta["zones"]
            ])
            st.markdown(tags, unsafe_allow_html=True)
        with c3:
            if st.session_state.del_confirm == tid:
                st.warning("정말 삭제할까요?")
                if st.button("예, 삭제", key=f"cfm_{tid}", type="primary"):
                    delete_template(tid)
                    st.session_state.del_confirm = None
                    st.rerun()
                if st.button("취소", key=f"cnc_{tid}"):
                    st.session_state.del_confirm = None
                    st.rerun()
            else:
                if st.button("🗑️ 삭제", key=f"del_{tid}", use_container_width=True):
                    st.session_state.del_confirm = tid
                    st.rerun()
        st.divider()
