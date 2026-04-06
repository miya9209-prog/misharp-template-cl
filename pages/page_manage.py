import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, get_thumb_b64, delete_template


def _safe_meta(meta) -> dict | None:
    """meta가 유효한 템플릿 dict인지 확인. 아니면 None 반환."""
    try:
        if not isinstance(meta, dict):
            return None
        name = meta.get("name")
        if not name or not isinstance(name, str):
            return None
        return meta
    except Exception:
        return None


def render():
    st.markdown('<div class="section-title">④ 템플릿 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 JPG·PSD 템플릿을 확인하고 관리합니다</div>', unsafe_allow_html=True)

    # load_all 자체도 try-except
    try:
        all_tpl_raw = load_all()
    except Exception as e:
        st.error(f"템플릿 데이터 로드 오류: {e}")
        return

    # 유효한 항목만 추출
    all_tpl = {}
    for tid, meta in all_tpl_raw.items():
        safe = _safe_meta(meta)
        if safe is not None:
            all_tpl[tid] = safe

    if not all_tpl:
        st.info("저장된 템플릿이 없습니다")
        return

    total   = len(all_tpl)
    jpg_cnt = sum(1 for m in all_tpl.values() if m.get("template_type", "jpg") != "psd")
    psd_cnt = sum(1 for m in all_tpl.values() if m.get("template_type") == "psd")

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
                try:
                    ttype = str(meta.get("template_type", "jpg")).upper()
                    canvas = meta.get("canvas_size", [0, 0])
                    W = canvas[0] if len(canvas) > 0 else 0
                    H = canvas[1] if len(canvas) > 1 else 0
                    name = meta.get("name", "(이름없음)")
                    created = str(meta.get("created_at", ""))[:10]

                    badge_col = "#C8A876" if ttype == "PSD" else "#78a8f0"
                    st.markdown(
                        f'<span style="background:rgba(200,168,118,0.12);color:{badge_col};'
                        f'font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px">'
                        f'{ttype}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{name}**")

                    if ttype == "PSD":
                        st.caption(f"{W}×{H}px · {created}")
                    else:
                        zones = meta.get("zones", [])
                        zones = zones if isinstance(zones, list) else []
                        iz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "image")
                        tz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "text")
                        st.caption(f"🖼️{iz} ✏️{tz} · {W}×{H}px · {created}")

                    desc = meta.get("description", "")
                    if desc:
                        st.caption(str(desc))

                except Exception as e:
                    st.caption(f"데이터 오류: {e}")

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
                try:
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;max-height:140px;object-fit:cover;'
                            f'object-position:top;border-radius:6px;'
                            f'border:1px solid rgba(255,255,255,0.08);margin-top:6px">',
                            unsafe_allow_html=True,
                        )
                except Exception:
                    pass

        st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)
