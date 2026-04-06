import streamlit as st
import sys, os, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_template_dir():
    return Path("templates")


def _load_all_safe():
    """완전 독립적 safe loader - 어떤 오류도 빈 dict 반환"""
    result = {}
    try:
        meta_file = _get_template_dir() / "_meta.json"
        if not meta_file.exists():
            return result
        text = meta_file.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return result
        for k, v in data.items():
            try:
                if not isinstance(v, dict):
                    continue
                name = v.get("name")
                if not name or not isinstance(name, str) or not name.strip():
                    continue
                result[str(k)] = v
            except Exception:
                continue
    except Exception:
        pass
    return result


def _delete_template(tid):
    import shutil
    try:
        meta_file = _get_template_dir() / "_meta.json"
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        data.pop(tid, None)
        meta_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tdir = _get_template_dir() / tid
        if tdir.exists():
            shutil.rmtree(tdir)
    except Exception as e:
        st.error(f"삭제 오류: {e}")


def _get_thumb_b64(tid):
    import base64
    try:
        p = _get_template_dir() / tid / "thumb.jpg"
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
    except Exception:
        pass
    return None


def render():
    st.markdown('<div class="section-title">④ 템플릿 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 JPG·PSD 템플릿을 확인하고 관리합니다</div>', unsafe_allow_html=True)

    # 비상 초기화
    with st.expander("🔧 데이터 오류 발생 시", expanded=False):
        st.caption("템플릿 목록이 깨진 경우에만 사용하세요.")
        if st.button("⚠️ 메타데이터 초기화", key="reset_meta"):
            try:
                mf = _get_template_dir() / "_meta.json"
                mf.write_text("{}", encoding="utf-8")
                st.success("완료. 재시작 후 확인하세요.")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    all_tpl = _load_all_safe()

    if not all_tpl:
        st.info("저장된 템플릿이 없습니다")
        return

    total   = len(all_tpl)
    psd_cnt = sum(1 for m in all_tpl.values() if m.get("template_type") == "psd")
    jpg_cnt = total - psd_cnt

    c1, c2, c3 = st.columns(3)
    c1.metric("총 템플릿",   f"{total}개")
    c2.metric("JPG 템플릿", f"{jpg_cnt}개")
    c3.metric("PSD 템플릿", f"{psd_cnt}개")
    st.divider()

    if "del_confirm" not in st.session_state:
        st.session_state.del_confirm = None

    tpl_list = list(all_tpl.items())
    for row in range(0, len(tpl_list), 4):
        cols = st.columns(4, gap="medium")
        for ci, (tid, meta) in enumerate(tpl_list[row:row+4]):
            with cols[ci]:
                try:
                    ttype   = str(meta.get("template_type", "jpg")).upper()
                    canvas  = meta.get("canvas_size", [0, 0])
                    W = canvas[0] if isinstance(canvas, list) and len(canvas) > 0 else 0
                    H = canvas[1] if isinstance(canvas, list) and len(canvas) > 1 else 0
                    name    = str(meta.get("name", "(이름없음)"))
                    created = str(meta.get("created_at", ""))[:10]
                    badge   = "#C8A876" if ttype == "PSD" else "#78a8f0"

                    st.markdown(
                        f'<span style="background:rgba(200,168,118,0.12);color:{badge};'
                        f'font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px">'
                        f'{ttype}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{name}**")

                    if ttype == "PSD":
                        st.caption(f"{W}×{H}px · {created}")
                    else:
                        zones = meta.get("zones", [])
                        if not isinstance(zones, list):
                            zones = []
                        iz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "image")
                        tz = sum(1 for z in zones if isinstance(z, dict) and z.get("type") == "text")
                        st.caption(f"🖼️{iz} ✏️{tz} · {W}×{H}px · {created}")

                    desc = meta.get("description", "")
                    if desc and isinstance(desc, str):
                        st.caption(desc)

                except Exception as e:
                    st.caption(f"표시 오류: {e}")

                # 삭제 버튼
                if st.session_state.del_confirm == tid:
                    st.warning("정말 삭제?")
                    d1, d2 = st.columns(2)
                    with d1:
                        if st.button("삭제", key=f"cfm_{tid}", type="primary", use_container_width=True):
                            _delete_template(tid)
                            st.session_state.del_confirm = None
                            st.rerun()
                    with d2:
                        if st.button("취소", key=f"cnc_{tid}", use_container_width=True):
                            st.session_state.del_confirm = None
                            st.rerun()
                else:
                    if st.button("🗑️ 삭제", key=f"del_{tid}", use_container_width=True):
                        st.session_state.del_confirm = tid
                        st.rerun()

                # 썸네일
                try:
                    b64 = _get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<div style="width:100%;height:110px;background:#111;'
                            f'border-radius:6px;margin-top:6px;overflow:hidden;'
                            f'border:1px solid rgba(255,255,255,0.08)">'
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;height:110px;object-fit:contain;'
                            f'object-position:top"></div>',
                            unsafe_allow_html=True,
                        )
                except Exception:
                    pass

        st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)
