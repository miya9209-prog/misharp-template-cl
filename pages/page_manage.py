import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, get_thumb_b64, delete_template


def render():
    st.markdown('<div class="section-title">④ 템플릿 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 JPG·PSD 템플릿을 확인하고 관리합니다</div>', unsafe_allow_html=True)

    all_tpl_raw = load_all()

    # ── 방어: meta가 dict가 아닌 경우 필터링
    all_tpl = {
        tid: meta
        for tid, meta in all_tpl_raw.items()
        if isinstance(meta, dict) and meta.get("name")
    }

    if not all_tpl:
        st.info("저장된 템플릿이 없습니다")
        return

    total   = len(all_tpl)
    jpg_cnt = sum(1 for m in all_tpl.values() if isinstance(m, dict) and m.get("template_type", "jpg") != "psd")
    psd_cnt = sum(1 for m in all_tpl.values() if isinstance(m, dict) and m.get("template_type") == "psd")

    m1, m2, m3 = st.columns(3)
    m1.metric("총 템플릿",   f"{total}개")
    m2.metric("JPG 템플릿", f"{jpg_cnt}개")
    m3.metric("PSD 템플릿", f"{psd_cnt}개")
    st.divider()

    if "del_confirm" not in st.session_state:
        st.session_state.del_confirm = None

    tpl_list = list(all_tpl.items())

    for row in range(0, len(tpl_list), 4):
        cols = st.columns(4, gap="medium")
        for ci, (tid, meta) in enumerate(tpl_list[row:row+4]):
            with cols[ci]:
                # meta가 dict인지 한번 더 보호
                if not isinstance(meta, dict):
                    st.caption(f"잘못된 데이터: {tid}")
                    continue

                ttype = meta.get("template_type", "jpg").upper()
                canvas = meta.get("canvas_size", [0, 0])
                W = canvas[0] if len(canvas) > 0 else 0
                H = canvas[1] if len(canvas) > 1 else 0

                badge_col = "#C8A876" if ttype == "PSD" else "#78a8f0"
                st.markdown(
                    f'<span style="background:rgba(200,168,118,0.12);color:{badge_col};'
                    f'font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px">'
                    f'{ttype}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{meta.get('name','(이름없음)')}**")

                created = meta.get("created_at", "")[:10]
                if ttype == "PSD":
                    st.caption(f"{W}×{H}px · {created}")
                else:
                    zones = meta.get("zones", [])
                    iz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "image")
                    tz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "text")
                    st.caption(f"🖼️{iz} ✏️{tz} · {W}×{H}px · {created}")

                if meta.get("description"):
                    st.caption(meta["description"])

                # 삭제 버튼
                if st.session_state.del_confirm == tid:
                    st.warning("정말 삭제할까요?")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("삭제", key=f"cfm_{tid}", type="primary", use_container_width=True):
                            delete_template(tid)
                            st.session_state.del_confirm = None
                            st.rerun()
                    with dc2:
                        if st.button("취소", key=f"cnc_{tid}", use_container_width=True):
                            st.session_state.del_confirm = None
                            st.rerun()
                else:
                    if st.button("🗑️ 삭제", key=f"del_{tid}", use_container_width=True):
                        st.session_state.del_confirm = tid
                        st.rerun()

                # 썸네일
                b64 = get_thumb_b64(tid)
                if b64:
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{b64}" '
                        f'style="width:100%;max-height:140px;object-fit:cover;object-position:top;'
                        f'border-radius:6px;border:1px solid rgba(255,255,255,0.08);margin-top:6px">',
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)
