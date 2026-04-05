"""
app.py - 미샵 템플릿 OS
Made by MISHARP COMPANY, MIYAWA, 2026
"""

import streamlit as st

st.set_page_config(
    page_title="미샵 템플릿 OS",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "create"

active = st.session_state.active_tab

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Montserrat:wght@400;600;800&display=swap');

[data-testid="stAppViewContainer"] { background:#0A0A0F; font-family:'Noto Sans KR',sans-serif; }
[data-testid="stHeader"]  { background:transparent !important; }
[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }

.ms-header-box {
    background:linear-gradient(135deg,#0D0D1A 0%,#10102A 50%,#0D0D1A 100%);
    border-bottom:1px solid rgba(255,255,255,0.06);
    padding:18px 44px 0 44px;
}
.ms-logo-row { display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.ms-logo {
    width:36px; height:36px;
    background:linear-gradient(135deg,#C8A876,#E8C99A);
    border-radius:8px; display:flex; align-items:center; justify-content:center;
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:13px;
    color:#0A0A0F; letter-spacing:-0.5px; flex-shrink:0;
}
.ms-title { font-family:'Montserrat',sans-serif; font-size:20px; font-weight:800; color:#FFFFFF; letter-spacing:-0.5px; }
.ms-title span { color:#C8A876; }
.ms-sub { font-size:11px; color:rgba(255,255,255,0.3); letter-spacing:0.3px; margin-top:2px; }

/* 탭 버튼 영역 */
.ms-tab-bar {
    background:linear-gradient(135deg,#0D0D1A 0%,#10102A 50%,#0D0D1A 100%);
    border-bottom:1px solid rgba(255,255,255,0.06);
    padding:0 44px;
}
/* st.columns gap 제거 */
.ms-tab-bar [data-testid="stHorizontalBlock"] { gap:0 !important; }
.ms-tab-bar [data-testid="stColumn"] { padding:0 !important; min-width:0; }

/* 탭 버튼 공통 — 일반 상태 */
.ms-tab-bar .stButton > button {
    background:none !important;
    border:none !important;
    border-bottom:2px solid transparent !important;
    border-radius:0 !important;
    box-shadow:none !important;
    color:rgba(255,255,255,0.38) !important;
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:13px !important;
    font-weight:500 !important;
    padding:10px 0 10px 0 !important;
    width:100% !important;
    transition:color 0.15s, border-color 0.15s !important;
}
.ms-tab-bar .stButton > button:hover {
    color:rgba(255,255,255,0.85) !important;
    background:none !important;
    border-bottom:2px solid rgba(255,255,255,0.18) !important;
    box-shadow:none !important;
}

/* 활성 탭 */
.ms-tab-active .stButton > button,
.ms-tab-active .stButton > button:hover,
.ms-tab-active .stButton > button:focus {
    color:#C8A876 !important;
    border-bottom:2px solid #C8A876 !important;
    font-weight:700 !important;
    background:none !important;
    box-shadow:none !important;
}

.ms-main { padding:32px 44px 0 44px; min-height:calc(100vh - 140px); }
.section-header { margin-bottom:28px; }
.section-title { font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.5px; }
.section-desc { font-size:13px; color:rgba(255,255,255,0.35); margin-top:5px; }

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:8px !important; color:#FFFFFF !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color:rgba(200,168,118,0.5) !important;
    box-shadow:0 0 0 2px rgba(200,168,118,0.08) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {
    color:rgba(255,255,255,0.55) !important;
    font-size:12px !important; font-weight:500 !important;
}

/* 일반 버튼 */
.ms-main .stButton > button {
    background:rgba(255,255,255,0.06) !important;
    color:rgba(255,255,255,0.8) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:8px !important;
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:13px !important; font-weight:500 !important;
    transition:all 0.2s !important;
}
.ms-main .stButton > button:hover {
    background:rgba(255,255,255,0.1) !important;
    border-color:rgba(255,255,255,0.2) !important;
}
[data-testid="stBaseButton-primary"] {
    background:linear-gradient(135deg,#C8A876,#B8946A) !important;
    color:#0A0A0F !important; border:none !important; font-weight:700 !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background:linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow:0 4px 16px rgba(200,168,118,0.3) !important;
}
[data-testid="stDownloadButton"] button {
    background:linear-gradient(135deg,#22c55e,#16a34a) !important;
    color:#fff !important; border:none !important; font-weight:700 !important;
}
[data-testid="stFileUploader"] {
    background:rgba(255,255,255,0.03) !important;
    border:1.5px dashed rgba(255,255,255,0.12) !important;
    border-radius:10px !important;
}
[data-testid="stSuccess"] { background:rgba(34,197,94,0.07) !important; border:1px solid rgba(34,197,94,0.18) !important; border-radius:8px !important; }
[data-testid="stInfo"]    { background:rgba(200,168,118,0.06) !important; border:1px solid rgba(200,168,118,0.18) !important; border-radius:8px !important; }
[data-testid="stWarning"] { background:rgba(251,191,36,0.06) !important; border:1px solid rgba(251,191,36,0.18) !important; border-radius:8px !important; }
[data-testid="stError"]   { background:rgba(239,68,68,0.06) !important; border:1px solid rgba(239,68,68,0.18) !important; border-radius:8px !important; }

[data-testid="stExpander"] {
    background:rgba(255,255,255,0.025) !important;
    border:1px solid rgba(255,255,255,0.07) !important;
    border-radius:8px !important;
}
[data-testid="stExpander"] summary { color:rgba(255,255,255,0.7) !important; }

[data-testid="stMetric"] {
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:10px; padding:16px;
}
[data-testid="stMetricValue"] { color:#C8A876 !important; }
[data-testid="stMetricLabel"] { color:rgba(255,255,255,0.4) !important; }

p, li { color:rgba(255,255,255,0.7); }
h1,h2,h3 { color:#FFFFFF; }
hr { border-color:rgba(255,255,255,0.07) !important; }

[data-testid="stSelectbox"] > div > div {
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:8px !important; color:#FFFFFF !important;
}

.ms-footer {
    background:rgba(0,0,0,0.35);
    border-top:1px solid rgba(255,255,255,0.05);
    padding:14px 44px; margin-top:48px; text-align:center;
}
.ms-footer-text { font-size:11px; color:rgba(255,255,255,0.18); letter-spacing:0.3px; line-height:1.7; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── 로고/타이틀 헤더
st.markdown("""
<div class="ms-header-box">
  <div class="ms-logo-row">
    <div class="ms-logo">MS</div>
    <div>
      <div class="ms-title">미샵 <span>템플릿</span> OS</div>
      <div class="ms-sub">상세페이지 자동화를 위한 이미지 편집 템플릿 제공</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 탭 버튼 행 (st.button + columns — HTML onclick 대신)
TABS = [
    ("create",  "① 템플릿 생성"),
    ("use",     "② 템플릿 활용"),
    ("manage",  "③ 템플릿 관리"),
    ("guide",   "사용 가이드"),
]

st.markdown('<div class="ms-tab-bar">', unsafe_allow_html=True)
tab_cols = st.columns(len(TABS))
for col, (tab_id, tab_label) in zip(tab_cols, TABS):
    wrap_class = "ms-tab-active" if active == tab_id else ""
    with col:
        st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
        if st.button(tab_label, key=f"tabkey_{tab_id}", use_container_width=True):
            st.session_state.active_tab = tab_id
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 컨텐츠
st.markdown('<div class="ms-main">', unsafe_allow_html=True)
if active == "create":
    from pages.page_create import render; render()
elif active == "use":
    from pages.page_use import render; render()
elif active == "manage":
    from pages.page_manage import render; render()
elif active == "guide":
    from pages.page_guide import render; render()
st.markdown('</div>', unsafe_allow_html=True)

# ── 푸터
st.markdown("""
<div class="ms-footer">
  <div class="ms-footer-text">
    made by MISHARP COMPANY, MIYAWA, 2026<br>
    이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.
  </div>
</div>
""", unsafe_allow_html=True)
