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
# API 키 세션 유지
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

active = st.session_state.active_tab
TABS = [
    ("create", "① 템플릿 생성"),
    ("use",    "② 템플릿 활용"),
    ("manage", "③ 템플릿 관리"),
    ("guide",  "사용 가이드"),
]
active_label = next(label for tid, label in TABS if tid == active)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;900&family=Montserrat:wght@600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: #0A0A0F !important;
    font-family: 'Noto Sans KR', sans-serif;
}}
[data-testid="stHeader"]  {{ background: transparent !important; }}
[data-testid="stSidebar"] {{ display: none !important; }}
.block-container          {{ padding: 20px 40px !important; max-width: 100% !important; }}

/* ── 탭 버튼 */
button[kind="secondary"] {{
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.5) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 6px 6px 0 0 !important;
    box-shadow: none !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    padding: 10px 8px !important;
    transition: all 0.15s !important;
}}
button[kind="secondary"]:hover {{
    background: rgba(255,255,255,0.1) !important;
    color: #FFF !important;
    border-bottom: 3px solid rgba(200,168,118,0.5) !important;
    box-shadow: none !important;
}}
button[aria-label="{active_label}"] {{
    background: rgba(200,168,118,0.15) !important;
    color: #C8A876 !important;
    border: 1px solid rgba(200,168,118,0.3) !important;
    border-bottom: 3px solid #C8A876 !important;
    font-weight: 700 !important;
}}

/* ── Primary 버튼 */
button[kind="primary"] {{
    background: linear-gradient(135deg,#C8A876,#B8946A) !important;
    color: #0A0A0F !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}}
button[kind="primary"]:hover {{
    background: linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow: 0 4px 18px rgba(200,168,118,0.3) !important;
}}

/* ── 다운로드 버튼 */
[data-testid="stDownloadButton"] button {{
    background: linear-gradient(135deg,#22c55e,#16a34a) !important;
    color: #fff !important; border: none !important;
    font-weight: 700 !important; border-radius: 8px !important;
}}

/* ── 입력 필드 — 흰 배경 + 검정 글씨로 확실한 대비 */
[data-testid="stTextInput"] input {{
    background: #FFFFFF !important;
    border: 1.5px solid #D0D0D0 !important;
    border-radius: 8px !important;
    color: #111111 !important;
    font-size: 14px !important;
}}
[data-testid="stTextInput"] input::placeholder {{ color: #999999 !important; }}
[data-testid="stTextInput"] input:focus {{
    border-color: #C8A876 !important;
    box-shadow: 0 0 0 2px rgba(200,168,118,0.2) !important;
}}

[data-testid="stTextArea"] textarea {{
    background: #FFFFFF !important;
    border: 1.5px solid #D0D0D0 !important;
    border-radius: 8px !important;
    color: #111111 !important;
    font-size: 14px !important;
}}
[data-testid="stTextArea"] textarea::placeholder {{ color: #999999 !important; }}
[data-testid="stTextArea"] textarea:focus {{
    border-color: #C8A876 !important;
    box-shadow: 0 0 0 2px rgba(200,168,118,0.2) !important;
}}

[data-testid="stNumberInput"] input {{
    background: #FFFFFF !important;
    border: 1.5px solid #D0D0D0 !important;
    border-radius: 8px !important;
    color: #111111 !important;
    font-size: 14px !important;
}}
[data-testid="stNumberInput"] input:focus {{
    border-color: #C8A876 !important;
}}

/* ── 레이블 — 밝은 색으로 잘 보이게 */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
[data-testid="stColorPicker"] label {{
    color: #E0E0E0 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
}}

/* ── 패스워드 입력 (API 키) */
[data-testid="stTextInput"] input[type="password"] {{
    background: #FFFFFF !important;
    color: #111111 !important;
    border: 1.5px solid #D0D0D0 !important;
}}

/* ── 셀렉트박스 */
[data-testid="stSelectbox"] > div > div {{
    background: #FFFFFF !important;
    border: 1.5px solid #D0D0D0 !important;
    border-radius: 8px !important;
    color: #111111 !important;
    font-size: 14px !important;
}}

/* ── 파일 업로더 */
[data-testid="stFileUploader"] {{
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px dashed rgba(200,168,118,0.4) !important;
    border-radius: 10px !important;
}}
[data-testid="stFileUploader"] > div > div > div > span {{
    color: rgba(255,255,255,0.7) !important;
}}

/* ── 알림 박스 */
[data-testid="stSuccess"] {{
    background: rgba(34,197,94,0.1) !important;
    border: 1px solid rgba(34,197,94,0.3) !important;
    border-radius: 8px !important;
    color: #86efac !important;
}}
[data-testid="stInfo"] {{
    background: rgba(200,168,118,0.08) !important;
    border: 1px solid rgba(200,168,118,0.3) !important;
    border-radius: 8px !important;
    color: #E8C99A !important;
}}
[data-testid="stWarning"] {{
    background: rgba(251,191,36,0.08) !important;
    border: 1px solid rgba(251,191,36,0.3) !important;
    border-radius: 8px !important;
    color: #fde68a !important;
}}
[data-testid="stError"] {{
    background: rgba(239,68,68,0.08) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    border-radius: 8px !important;
    color: #fca5a5 !important;
}}

/* ── 익스팬더 */
[data-testid="stExpander"] {{
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary {{
    color: #E0E0E0 !important;
    font-weight: 600 !important;
}}

/* ── 메트릭 */
[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 16px;
}}
[data-testid="stMetricValue"] {{ color: #C8A876 !important; font-weight: 700 !important; }}
[data-testid="stMetricLabel"] {{ color: #B0B0B0 !important; }}

/* ── 체크박스 / 라디오 */
[data-testid="stCheckbox"] span,
[data-testid="stRadio"] span {{ color: #E0E0E0 !important; }}

/* ── 일반 텍스트 */
p    {{ color: #D0D0D0 !important; }}
li   {{ color: #D0D0D0 !important; }}
h1,h2,h3 {{ color: #FFFFFF !important; }}
hr   {{ border-color: rgba(255,255,255,0.1) !important; margin: 16px 0 !important; }}
caption {{ color: #A0A0A0 !important; }}

/* ── 섹션 타이틀 */
.section-title {{
    font-size: 20px; font-weight: 700;
    color: #FFFFFF !important;
    letter-spacing: -0.4px; margin-bottom: 6px;
    padding-bottom: 8px;
    border-bottom: 2px solid rgba(200,168,118,0.3);
}}
.section-desc {{
    font-size: 13px; color: #A0A0A0 !important; margin-bottom: 20px;
}}

/* ── 로고/헤더 */
.ms-logo-row {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; }}
.ms-logo {{
    width:36px; height:36px;
    background: linear-gradient(135deg,#C8A876,#E8C99A);
    border-radius:8px; display:flex; align-items:center; justify-content:center;
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:13px; color:#0A0A0F;
}}
.ms-title {{ font-family:'Montserrat',sans-serif; font-size:19px; font-weight:800; color:#FFF; letter-spacing:-0.4px; }}
.ms-title span {{ color:#C8A876; }}
.ms-sub {{ font-size:11px; color:#888; margin-top:2px; }}

/* ── 스텝 헤더 */
.step-header {{
    background: rgba(200,168,118,0.08);
    border-left: 3px solid #C8A876;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0 12px 0;
    font-size: 15px; font-weight: 700; color: #E8C99A !important;
}}

/* ── 정보 카드 */
.info-card {{
    background: rgba(200,168,118,0.07);
    border: 1px solid rgba(200,168,118,0.2);
    border-radius: 10px; padding: 16px 20px;
    margin-bottom: 16px;
}}

/* ── 색상피커 레이블 */
[data-testid="stColorPicker"] > div > label {{
    color: #E0E0E0 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}}

/* ── caption */
[data-testid="stCaptionContainer"] p {{
    color: #909090 !important;
    font-size: 12px !important;
}}

/* ── number input 버튼 */
[data-testid="stNumberInput"] button {{
    background: rgba(255,255,255,0.08) !important;
    color: #FFF !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}}

/* ── 푸터 */
.ms-footer {{ text-align:center; padding:20px 0 8px 0; }}
.ms-footer p {{ font-size:11px; color:#555 !important; line-height:1.7; margin:0; }}
</style>
""", unsafe_allow_html=True)

# ── 헤더
st.markdown("""
<div class="ms-logo-row">
  <div class="ms-logo">MS</div>
  <div>
    <div class="ms-title">미샵 <span>템플릿</span> OS</div>
    <div class="ms-sub">상세페이지 자동화를 위한 이미지 편집 템플릿 제공</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── 탭 버튼
cols = st.columns(len(TABS))
for col, (tid, tlabel) in zip(cols, TABS):
    with col:
        if st.button(tlabel, key=f"tab_{tid}", use_container_width=True):
            st.session_state.active_tab = tid
            st.rerun()

st.divider()

# ── 컨텐츠
if active == "create":
    from pages.page_create import render; render()
elif active == "use":
    from pages.page_use import render; render()
elif active == "manage":
    from pages.page_manage import render; render()
elif active == "guide":
    from pages.page_guide import render; render()

st.divider()
st.markdown("""
<div class="ms-footer">
  <p>made by MISHARP COMPANY, MIYAWA, 2026<br>
  이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.</p>
</div>
""", unsafe_allow_html=True)
