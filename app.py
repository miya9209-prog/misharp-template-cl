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

for k, v in [("active_tab","create"),("openai_api_key","")]:
    if k not in st.session_state:
        st.session_state[k] = v

active = st.session_state.active_tab

TABS = [
    ("create",  "① JPG 템플릿 생성"),
    ("use",     "② JPG 템플릿 활용"),
    ("psd",     "③ PSD 직접 편집"),
    ("manage",  "④ 템플릿 관리"),
    ("guide",   "사용 가이드"),
]
active_label = next(label for tid, label in TABS if tid == active)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;900&family=Montserrat:wght@600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background:#0A0A0F !important; font-family:'Noto Sans KR',sans-serif;
}}
[data-testid="stHeader"]  {{ background:transparent !important; }}
[data-testid="stSidebar"] {{ display:none !important; }}
.block-container          {{ padding:20px 40px !important; max-width:100% !important; }}

button[kind="secondary"] {{
    background:rgba(255,255,255,0.05) !important;
    color:rgba(255,255,255,0.45) !important;
    border:none !important; border-bottom:3px solid transparent !important;
    border-radius:4px 4px 0 0 !important; box-shadow:none !important;
    font-size:13px !important; font-weight:500 !important;
    font-family:'Noto Sans KR',sans-serif !important;
    padding:10px 8px !important; transition:all 0.15s !important;
}}
button[kind="secondary"]:hover {{
    background:rgba(255,255,255,0.08) !important;
    color:rgba(255,255,255,0.85) !important;
    border-bottom:3px solid rgba(200,168,118,0.4) !important;
    box-shadow:none !important;
}}
button[aria-label="{active_label}"] {{
    background:rgba(200,168,118,0.12) !important;
    color:#C8A876 !important;
    border:1px solid rgba(200,168,118,0.25) !important;
    border-bottom:3px solid #C8A876 !important;
    font-weight:700 !important;
}}
button[kind="primary"] {{
    background:linear-gradient(135deg,#C8A876,#B8946A) !important;
    color:#0A0A0F !important; border:none !important;
    font-weight:700 !important; border-radius:8px !important;
    font-family:'Noto Sans KR',sans-serif !important;
}}
button[kind="primary"]:hover {{
    background:linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow:0 4px 18px rgba(200,168,118,0.3) !important;
}}
[data-testid="stDownloadButton"] button {{
    background:linear-gradient(135deg,#22c55e,#16a34a) !important;
    color:#fff !important; border:none !important;
    font-weight:700 !important; border-radius:8px !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background:#FFF !important; border:1.5px solid #D0D0D0 !important;
    border-radius:8px !important; color:#111 !important; font-size:14px !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color:#C8A876 !important;
    box-shadow:0 0 0 2px rgba(200,168,118,0.2) !important;
}}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
[data-testid="stColorPicker"] label {{
    color:#E0E0E0 !important; font-size:13px !important; font-weight:600 !important;
}}
[data-testid="stFileUploader"] {{
    background:rgba(255,255,255,0.04) !important;
    border:1.5px dashed rgba(200,168,118,0.4) !important; border-radius:10px !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background:#FFF !important; border:1.5px solid #D0D0D0 !important;
    border-radius:8px !important; color:#111 !important;
}}
[data-testid="stSuccess"] {{ background:rgba(34,197,94,0.1) !important; border:1px solid rgba(34,197,94,0.3) !important; border-radius:8px !important; color:#86efac !important; }}
[data-testid="stInfo"]    {{ background:rgba(200,168,118,0.08) !important; border:1px solid rgba(200,168,118,0.3) !important; border-radius:8px !important; color:#E8C99A !important; }}
[data-testid="stWarning"] {{ background:rgba(251,191,36,0.08) !important; border:1px solid rgba(251,191,36,0.3) !important; border-radius:8px !important; color:#fde68a !important; }}
[data-testid="stError"]   {{ background:rgba(239,68,68,0.08) !important; border:1px solid rgba(239,68,68,0.3) !important; border-radius:8px !important; color:#fca5a5 !important; }}
[data-testid="stExpander"] {{ background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.1) !important; border-radius:8px !important; }}
[data-testid="stExpander"] summary {{ color:#E0E0E0 !important; font-weight:600 !important; }}
[data-testid="stMetric"] {{ background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:16px; }}
[data-testid="stMetricValue"] {{ color:#C8A876 !important; font-weight:700 !important; }}
[data-testid="stMetricLabel"] {{ color:#B0B0B0 !important; }}
p    {{ color:#D0D0D0 !important; }}
li   {{ color:#D0D0D0 !important; }}
h1,h2,h3 {{ color:#FFF !important; }}
hr   {{ border-color:rgba(255,255,255,0.1) !important; margin:16px 0 !important; }}
.section-title {{ font-size:20px; font-weight:700; color:#FFF !important; letter-spacing:-0.4px; margin-bottom:6px; padding-bottom:8px; border-bottom:2px solid rgba(200,168,118,0.3); }}
.section-desc  {{ font-size:13px; color:#A0A0A0 !important; margin-bottom:20px; }}
.ms-logo-row   {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; }}
.ms-logo       {{ width:36px; height:36px; background:linear-gradient(135deg,#C8A876,#E8C99A); border-radius:8px; display:flex; align-items:center; justify-content:center; font-family:'Montserrat',sans-serif; font-weight:800; font-size:13px; color:#0A0A0F; }}
.ms-title      {{ font-family:'Montserrat',sans-serif; font-size:19px; font-weight:800; color:#FFF; letter-spacing:-0.4px; }}
.ms-title span {{ color:#C8A876; }}
.ms-sub        {{ font-size:11px; color:#888; margin-top:2px; }}
.step-header   {{ background:rgba(200,168,118,0.08); border-left:3px solid #C8A876; padding:10px 16px; border-radius:0 8px 8px 0; margin:20px 0 12px 0; font-size:15px; font-weight:700; color:#E8C99A !important; }}
.info-card     {{ background:rgba(200,168,118,0.07); border:1px solid rgba(200,168,118,0.2); border-radius:10px; padding:16px 20px; margin-bottom:16px; }}
[data-testid="stCaptionContainer"] p {{ color:#909090 !important; font-size:12px !important; }}
.ms-footer     {{ text-align:center; padding:20px 0 8px 0; }}
.ms-footer p   {{ font-size:11px; color:#555 !important; line-height:1.7; margin:0; }}
</style>
""", unsafe_allow_html=True)

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

cols = st.columns(len(TABS))
for col, (tid, tlabel) in zip(cols, TABS):
    with col:
        if st.button(tlabel, key=f"tab_{tid}", use_container_width=True):
            st.session_state.active_tab = tid
            st.rerun()

st.divider()

if active == "create":
    from pages.page_create import render; render()
elif active == "use":
    from pages.page_use import render; render()
elif active == "psd":
    from pages.page_psd import render; render()
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
