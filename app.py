"""
app.py - 미샵 템플릿 OS
Made by MISHARP COMPANY, MIYAWA, 2026
"""
import streamlit as st

st.set_page_config(
    page_title="미샵 템플릿 OS", page_icon="🎨",
    layout="wide", initial_sidebar_state="collapsed",
)

# ── CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;900&family=Montserrat:wght@600;800&display=swap');

html,body,[data-testid="stAppViewContainer"]{background:#0A0A0F !important;font-family:'Noto Sans KR',sans-serif;}
[data-testid="stHeader"]{background:transparent !important;}
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding:20px 40px !important;max-width:100% !important;}

/* 네이티브 st.tabs 스타일 */
[data-testid="stTabs"] [role="tablist"]{
    background:rgba(255,255,255,0.03);
    border-bottom:1px solid rgba(255,255,255,0.08);
    padding:0 8px;
}
[data-testid="stTabs"] [role="tab"]{
    color:rgba(255,255,255,0.45) !important;
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:13px !important;
    font-weight:500 !important;
    padding:10px 20px !important;
    border:none !important;
    border-bottom:3px solid transparent !important;
}
[data-testid="stTabs"] [role="tab"]:hover{
    color:rgba(255,255,255,0.85) !important;
    background:rgba(255,255,255,0.04) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{
    color:#C8A876 !important;
    border-bottom:3px solid #C8A876 !important;
    font-weight:700 !important;
    background:transparent !important;
}
[data-testid="stTabsContent"]{padding-top:24px;}

button[kind="primary"]{
    background:linear-gradient(135deg,#C8A876,#B8946A) !important;
    color:#0A0A0F !important;border:none !important;
    font-weight:700 !important;border-radius:8px !important;
    font-family:'Noto Sans KR',sans-serif !important;
}
button[kind="primary"]:hover{
    background:linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow:0 4px 18px rgba(200,168,118,0.3) !important;
}
[data-testid="stDownloadButton"] button{
    background:linear-gradient(135deg,#22c55e,#16a34a) !important;
    color:#fff !important;border:none !important;
    font-weight:700 !important;border-radius:8px !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input{
    background:#FFF !important;border:1.5px solid #D0D0D0 !important;
    border-radius:8px !important;color:#111 !important;font-size:14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus{
    border-color:#C8A876 !important;
    box-shadow:0 0 0 2px rgba(200,168,118,0.2) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
[data-testid="stColorPicker"] label,
[data-testid="stCheckbox"] label{
    color:#E0E0E0 !important;font-size:13px !important;font-weight:600 !important;
}
[data-testid="stFileUploader"]{
    background:rgba(255,255,255,0.04) !important;
    border:1.5px dashed rgba(200,168,118,0.4) !important;border-radius:10px !important;
}
[data-testid="stSelectbox"]>div>div{
    background:#FFF !important;border:1.5px solid #D0D0D0 !important;
    border-radius:8px !important;color:#111 !important;
}
[data-testid="stSuccess"]{background:rgba(34,197,94,0.1) !important;border:1px solid rgba(34,197,94,0.3) !important;border-radius:8px !important;color:#86efac !important;}
[data-testid="stInfo"]   {background:rgba(200,168,118,0.08) !important;border:1px solid rgba(200,168,118,0.3) !important;border-radius:8px !important;color:#E8C99A !important;}
[data-testid="stWarning"]{background:rgba(251,191,36,0.08) !important;border:1px solid rgba(251,191,36,0.3) !important;border-radius:8px !important;color:#fde68a !important;}
[data-testid="stError"]  {background:rgba(239,68,68,0.08) !important;border:1px solid rgba(239,68,68,0.3) !important;border-radius:8px !important;color:#fca5a5 !important;}
[data-testid="stExpander"]{background:rgba(255,255,255,0.04) !important;border:1px solid rgba(255,255,255,0.1) !important;border-radius:8px !important;}
[data-testid="stExpander"] summary{color:#E0E0E0 !important;font-weight:600 !important;}
[data-testid="stMetric"]{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:16px;}
[data-testid="stMetricValue"]{color:#C8A876 !important;font-weight:700 !important;}
[data-testid="stMetricLabel"]{color:#B0B0B0 !important;}
p{color:#D0D0D0 !important;}li{color:#D0D0D0 !important;}
h1,h2,h3{color:#FFF !important;}
hr{border-color:rgba(255,255,255,0.1) !important;margin:16px 0 !important;}
.section-title{font-size:20px;font-weight:700;color:#FFF !important;letter-spacing:-0.4px;margin-bottom:6px;padding-bottom:8px;border-bottom:2px solid rgba(200,168,118,0.3);}
.section-desc{font-size:13px;color:#A0A0A0 !important;margin-bottom:20px;}
.step-header{background:rgba(200,168,118,0.08);border-left:3px solid #C8A876;padding:10px 16px;border-radius:0 8px 8px 0;margin:20px 0 12px 0;font-size:15px;font-weight:700;color:#E8C99A !important;}
.info-card{background:rgba(200,168,118,0.07);border:1px solid rgba(200,168,118,0.2);border-radius:10px;padding:16px 20px;margin-bottom:16px;}
[data-testid="stCaptionContainer"] p{color:#909090 !important;font-size:12px !important;}
.ms-footer{text-align:center;padding:20px 0 8px 0;}
.ms-footer p{font-size:11px;color:#555 !important;line-height:1.7;margin:0;}

/* 헤더 로고 */
.ms-header{display:flex;align-items:center;gap:12px;margin-bottom:16px;}
.ms-logo{width:36px;height:36px;background:linear-gradient(135deg,#C8A876,#E8C99A);border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:'Montserrat',sans-serif;font-weight:800;font-size:13px;color:#0A0A0F;flex-shrink:0;}
.ms-title{font-family:'Montserrat',sans-serif;font-size:19px;font-weight:800;color:#FFF;letter-spacing:-0.4px;}
.ms-title span{color:#C8A876;}
.ms-sub{font-size:11px;color:#888;margin-top:2px;}
</style>
""", unsafe_allow_html=True)

# ── 헤더 (클릭 링크 없음 - 버튼 차단 문제 방지)
st.markdown("""
<a href="/" target="_self" style="text-decoration:none;display:block;cursor:pointer">
  <div class="ms-header">
    <div class="ms-logo">MS</div>
    <div>
      <div class="ms-title">미샵 <span>템플릿</span> OS
        <span style="color:rgba(255,255,255,0.25);font-size:11px;font-weight:400;margin-left:8px">↺ 처음으로</span>
      </div>
      <div class="ms-sub">상세페이지 자동화를 위한 이미지 편집 템플릿 제공</div>
    </div>
  </div>
</a>
""", unsafe_allow_html=True)

# ── 세션 초기화
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

# ── 탭: st.tabs() 네이티브 사용 (클릭 100% 보장)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "① PSD 템플릿 생성",
    "② JPG 템플릿 생성",
    "③ 템플릿 불러오기",
    "④ 템플릿 관리",
    "⑤ 사용 가이드",
])

with tab1:
    from pages.page_psd_create import render; render()

with tab2:
    from pages.page_create import render; render()

with tab3:
    from pages.page_psd_use import render; render()

with tab4:
    # ── 템플릿 관리 (인라인 - 파일 캐시 문제 우회)
    import json as _json
    from pathlib import Path as _Path
    import base64 as _b64

    def _mgr_load():
        result = {}
        try:
            mf = _Path("templates/_meta.json")
            if not mf.exists():
                return result
            data = _json.loads(mf.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return result
            for k, v in data.items():
                try:
                    if isinstance(v, dict) and isinstance(v.get("name"), str) and v.get("name"):
                        result[str(k)] = v
                except Exception:
                    continue
        except Exception:
            pass
        return result

    def _mgr_thumb(tid):
        try:
            p = _Path(f"templates/{tid}/thumb.jpg")
            if p.exists():
                return _b64.b64encode(p.read_bytes()).decode()
        except Exception:
            pass
        return None

    def _mgr_delete(tid):
        import shutil
        try:
            mf = _Path("templates/_meta.json")
            data = _json.loads(mf.read_text(encoding="utf-8"))
            data.pop(tid, None)
            mf.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            td = _Path(f"templates/{tid}")
            if td.exists():
                shutil.rmtree(td)
        except Exception as e:
            st.error(f"삭제 오류: {e}")

    st.markdown('<div class="section-title">④ 템플릿 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 JPG·PSD 템플릿을 확인하고 관리합니다</div>', unsafe_allow_html=True)

    with st.expander("🔧 데이터 오류 발생 시", expanded=False):
        st.caption("템플릿 목록이 깨진 경우 초기화하세요.")
        if st.button("⚠️ 메타데이터 초기화", key="reset_meta_btn"):
            try:
                _Path("templates/_meta.json").write_text("{}", encoding="utf-8")
                st.success("완료. 새로고침하세요.")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    _all = _mgr_load()

    if not _all:
        st.info("저장된 템플릿이 없습니다")
    else:
        _total = len(_all)
        _psd = sum(1 for m in _all.values() if m.get("template_type") == "psd")
        _jpg = _total - _psd
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("총 템플릿", f"{_total}개")
        mc2.metric("JPG 템플릿", f"{_jpg}개")
        mc3.metric("PSD 템플릿", f"{_psd}개")
        st.divider()

        if "del_confirm" not in st.session_state:
            st.session_state.del_confirm = None

        _tlist = list(_all.items())
        for _row in range(0, len(_tlist), 4):
            _cols = st.columns(4, gap="medium")
            for _ci, (_tid, _meta) in enumerate(_tlist[_row:_row+4]):
                with _cols[_ci]:
                    try:
                        _tt = str(_meta.get("template_type", "jpg")).upper()
                        _cv = _meta.get("canvas_size", [0, 0])
                        _W = _cv[0] if isinstance(_cv, list) and len(_cv) > 0 else 0
                        _H = _cv[1] if isinstance(_cv, list) and len(_cv) > 1 else 0
                        _nm = str(_meta.get("name", "이름없음"))
                        _dt = str(_meta.get("created_at", ""))[:10]
                        _bc = "#C8A876" if _tt == "PSD" else "#78a8f0"
                        st.markdown(f'<span style="background:rgba(200,168,118,0.12);color:{_bc};font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px">{_tt}</span>', unsafe_allow_html=True)
                        st.markdown(f"**{_nm}**")
                        if _tt == "PSD":
                            st.caption(f"{_W}×{_H}px · {_dt}")
                        else:
                            _zs = _meta.get("zones", [])
                            if not isinstance(_zs, list): _zs = []
                            _iz = sum(1 for z in _zs if isinstance(z, dict) and z.get("type") == "image")
                            _tz = sum(1 for z in _zs if isinstance(z, dict) and z.get("type") == "text")
                            st.caption(f"🖼️{_iz} ✏️{_tz} · {_W}×{_H}px · {_dt}")
                        _dc = _meta.get("description", "")
                        if _dc: st.caption(str(_dc))
                    except Exception as _e:
                        st.caption(f"표시 오류: {_e}")

                    if st.session_state.del_confirm == _tid:
                        st.warning("정말 삭제?")
                        _dd1, _dd2 = st.columns(2)
                        with _dd1:
                            if st.button("삭제", key=f"cfm_{_tid}", type="primary", use_container_width=True):
                                _mgr_delete(_tid)
                                st.session_state.del_confirm = None
                                st.rerun()
                        with _dd2:
                            if st.button("취소", key=f"cnc_{_tid}", use_container_width=True):
                                st.session_state.del_confirm = None
                                st.rerun()
                    else:
                        if st.button("🗑️ 삭제", key=f"del_{_tid}", use_container_width=True):
                            st.session_state.del_confirm = _tid
                            st.rerun()

                    try:
                        _tb = _mgr_thumb(_tid)
                        if _tb:
                            st.markdown(f'<img src="data:image/jpeg;base64,{_tb}" style="width:100%;max-height:140px;object-fit:cover;object-position:top;border-radius:6px;border:1px solid rgba(255,255,255,0.08);margin-top:6px">', unsafe_allow_html=True)
                    except Exception:
                        pass

            st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

with tab5:
    from pages.page_guide import render; render()

st.divider()
st.markdown("""<div class="ms-footer">
  <p>made by MISHARP COMPANY, MIYAWA, 2026<br>
  이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.</p>
</div>""", unsafe_allow_html=True)
