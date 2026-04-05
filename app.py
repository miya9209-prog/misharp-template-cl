"""
app.py — 미샵 템플릿 OS
상세페이지 자동화를 위한 이미지 편집 템플릿 제공
Made by MISHARP COMPANY, MIYAWA, 2026
"""

import streamlit as st

# ── 페이지 설정 (가장 먼저 호출)
st.set_page_config(
    page_title="미샵 템플릿 OS",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 전역 CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Montserrat:wght@400;600;800&display=swap');

/* ── 전체 배경 */
[data-testid="stAppViewContainer"] {
    background: #0A0A0F;
    font-family: 'Noto Sans KR', sans-serif;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── 상단 헤더 */
.ms-header {
    background: linear-gradient(135deg, #0D0D1A 0%, #10102A 50%, #0D0D1A 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 18px 44px 0 44px;
    position: sticky; top: 0; z-index: 999;
}
.ms-logo-row { display:flex; align-items:center; gap:14px; margin-bottom:14px; }
.ms-logo {
    width:36px; height:36px;
    background: linear-gradient(135deg, #C8A876, #E8C99A);
    border-radius:8px;
    display:flex; align-items:center; justify-content:center;
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:13px;
    color:#0A0A0F; letter-spacing:-0.5px; flex-shrink:0;
}
.ms-title {
    font-family:'Montserrat',sans-serif; font-size:20px; font-weight:800;
    color:#FFFFFF; letter-spacing:-0.5px; line-height:1.1;
}
.ms-title span { color:#C8A876; }
.ms-sub { font-size:11px; color:rgba(255,255,255,0.3); letter-spacing:0.3px; margin-top:2px; }

/* ── 탭 네비게이션 */
.ms-tabs { display:flex; gap:0; }
.ms-tab {
    padding:10px 26px;
    font-size:13px; font-weight:500;
    color:rgba(255,255,255,0.4);
    border:none; background:none;
    border-bottom:2px solid transparent;
    cursor:pointer; white-space:nowrap;
    font-family:'Noto Sans KR',sans-serif;
    letter-spacing:0.2px;
    transition:color 0.2s;
}
.ms-tab:hover  { color:rgba(255,255,255,0.75); }
.ms-tab.active { color:#C8A876; border-bottom-color:#C8A876; font-weight:700; }

/* ── 메인 영역 */
.ms-main { padding:32px 44px 0 44px; min-height:calc(100vh - 130px); }

/* ── 섹션 헤더 */
.section-header { margin-bottom:28px; }
.section-title  { font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.5px; }
.section-desc   { font-size:13px; color:rgba(255,255,255,0.35); margin-top:5px; }

/* ── 공통 입력 스타일 */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(200,168,118,0.5) !important;
    box-shadow: 0 0 0 2px rgba(200,168,118,0.08) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {
    color: rgba(255,255,255,0.55) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* ── 버튼 (기본 = 골드) */
.stButton > button {
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.8) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.2) !important;
}
/* primary 버튼 = 골드 */
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg,#C8A876,#B8946A) !important;
    color: #0A0A0F !important;
    border: none !important;
    font-weight: 700 !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow: 0 4px 16px rgba(200,168,118,0.3) !important;
}
/* 다운로드 버튼 */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg,#22c55e,#16a34a) !important;
    color: #fff !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ── 파일 업로더 */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
}

/* ── 알림 박스 */
[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.07) !important;
    border: 1px solid rgba(34,197,94,0.18) !important;
    border-radius: 8px !important;
}
[data-testid="stInfo"] {
    background: rgba(200,168,118,0.06) !important;
    border: 1px solid rgba(200,168,118,0.18) !important;
    border-radius: 8px !important;
}
[data-testid="stWarning"] {
    background: rgba(251,191,36,0.06) !important;
    border: 1px solid rgba(251,191,36,0.18) !important;
    border-radius: 8px !important;
}
[data-testid="stError"] {
    background: rgba(239,68,68,0.06) !important;
    border: 1px solid rgba(239,68,68,0.18) !important;
    border-radius: 8px !important;
}

/* ── 익스팬더 */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary { color:rgba(255,255,255,0.7) !important; }

/* ── 메트릭 */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 16px;
}
[data-testid="stMetricValue"] { color:#C8A876 !important; }
[data-testid="stMetricLabel"] { color:rgba(255,255,255,0.4) !important; }

/* ── 텍스트 */
p, li { color:rgba(255,255,255,0.7); }
h1,h2,h3 { color:#FFFFFF; }
hr { border-color:rgba(255,255,255,0.07) !important; }

/* ── 스피너 */
[data-testid="stSpinner"] { color:rgba(255,255,255,0.5) !important; }

/* ── 색상 피커 */
[data-testid="stColorPicker"] > div > div {
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
}

/* ── 셀렉트박스 */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

/* ── 하단 푸터 */
.ms-footer {
    background: rgba(0,0,0,0.35);
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 14px 44px;
    margin-top: 48px;
    text-align: center;
}
.ms-footer-text {
    font-size: 11px;
    color: rgba(255,255,255,0.18);
    letter-spacing: 0.3px;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "create"

# ── URL 파라미터로 탭 전환
q = st.query_params.get("tab", "create")
valid_tabs = ["create", "use", "manage", "guide"]
if q in valid_tabs:
    st.session_state.active_tab = q

# ── 상단 헤더 렌더링
TABS = {
    "create":  "① 템플릿 생성",
    "use":     "② 템플릿 활용",
    "manage":  "③ 템플릿 관리",
    "guide":   "사용 가이드",
}

tab_buttons_html = "".join([
    f'<button class="ms-tab {"active" if st.session_state.active_tab == k else ""}" '
    f'onclick="location.href=\'?tab={k}\'">{v}</button>'
    for k, v in TABS.items()
])

st.markdown(f"""
<div class="ms-header">
  <div class="ms-logo-row">
    <div class="ms-logo">MS</div>
    <div>
      <div class="ms-title">미샵 <span>템플릿</span> OS</div>
      <div class="ms-sub">상세페이지 자동화를 위한 이미지 편집 템플릿 제공</div>
    </div>
  </div>
  <div class="ms-tabs">{tab_buttons_html}</div>
</div>
<div class="ms-main">
""", unsafe_allow_html=True)

# ── 탭 라우팅
active = st.session_state.active_tab

if active == "create":
    from pages.page_create import render
    render()
elif active == "use":
    from pages.page_use import render
    render()
elif active == "manage":
    from pages.page_manage import render
    render()
elif active == "guide":
    from pages.page_guide import render
    render()

st.markdown("</div>", unsafe_allow_html=True)

# ── 푸터
st.markdown("""
<div class="ms-footer">
  <div class="ms-footer-text">
    made by MISHARP COMPANY, MIYAWA, 2026<br>
    이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.
  </div>
</div>
""", unsafe_allow_html=True)
