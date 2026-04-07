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
/* 버튼 텍스트 좌측 정렬 */
div[data-testid="stButton"] > button {
    width:100%;
}
div[data-testid="stButton"] > button > div {
    width:100%;
    display:flex;
    justify-content:flex-start !important;
    text-align:left !important;
}
div[data-testid="stButton"] > button > div > p {
    text-align:left !important;
    width:100%;
}
/* emotion cache 클래스 무관하게 버튼 내 모든 자식에 적용 */
[data-testid="stButton"] button * {
    text-align:left !important;
}
[data-testid="stButton"] button {
    text-align:left !important;
    justify-content:flex-start !important;
}
.ms-footer{text-align:center;padding:20px 0 8px 0;}
.ms-footer p{font-size:11px;color:#555 !important;line-height:1.7;margin:0;}

/* 헤더 로고 */
.ms-header{display:flex;align-items:center;gap:24px;margin-bottom:0;padding:10px 0;}
.ms-logo{width:72px;height:72px;background:linear-gradient(135deg,#C8A876,#E8C99A);border-radius:14px;display:flex;align-items:center;justify-content:center;font-family:'Montserrat',sans-serif;font-weight:800;font-size:26px;color:#0A0A0F;flex-shrink:0;}
.ms-title{font-family:'Montserrat',sans-serif;font-size:38px;font-weight:800;color:#FFF;letter-spacing:-0.8px;}
.ms-title span{color:#C8A876;}
.ms-sub{font-size:14px;color:#888;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

# ── 헤더 (클릭 링크 없음 - 버튼 차단 문제 방지)
st.markdown("""
<a href="/" target="_self" style="text-decoration:none;display:block;cursor:pointer;
   background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(255,255,255,0.06);
   margin:-20px -40px 16px -40px;padding:28px 40px 22px 40px;">
  <div class="ms-header">
    <div class="ms-logo">MS</div>
    <div>
      <div class="ms-title">미샵 <span>템플릿</span> OS
        <span style="color:rgba(255,255,255,0.3);font-size:11px;font-weight:400;margin-left:10px">↺ 처음으로</span>
      </div>
      <div class="ms-sub">온라인몰 상세페이지 자동화를 위한 이미지 편집 템플릿 생성, 활용, 관리 프로그램</div>
    </div>
  </div>
</a>
""", unsafe_allow_html=True)

# ── 세션 초기화
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

# ── 탭: 순서 변경 (불러오기→PSD생성→JPG생성→가이드)
tab1, tab2, tab3, tab4 = st.tabs([
    "① 템플릿 불러오기",
    "② PSD 템플릿 생성",
    "③ JPG 템플릿 생성",
    "④ 사용 가이드",
])

with tab1:
    from pages.page_psd_use import render; render()

with tab2:
    from pages.page_psd_create import render; render()

with tab3:
    from pages.page_create import render; render()

with tab4:
    from pages.page_guide import render; render()


st.divider()
st.markdown("""<div class="ms-footer">
  <p>made by MISHARP COMPANY, MIYAWA, 2026<br>
  이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.</p>
</div>""", unsafe_allow_html=True)
