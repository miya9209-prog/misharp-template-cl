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

TABS = [
    ("create", "① 템플릿 생성"),
    ("use",    "② 템플릿 활용"),
    ("manage", "③ 템플릿 관리"),
    ("guide",  "사용 가이드"),
]
active_label = next(label for tid, label in TABS if tid == active)

# ── CSS (div 래퍼 없이 순수 st 컴포넌트에만 적용)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;900&family=Montserrat:wght@600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: #0A0A0F !important;
    font-family: 'Noto Sans KR', sans-serif;
}}
[data-testid="stHeader"]  {{ background: transparent !important; }}
[data-testid="stSidebar"] {{ display: none !important; }}
.block-container          {{ padding: 16px 40px !important; max-width: 100% !important; }}

/* 탭 버튼 — 기본 */
button[kind="secondary"] {{
    background: rgba(255,255,255,0.05) !important;
    color: rgba(255,255,255,0.45) !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 4px 4px 0 0 !important;
    box-shadow: none !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    padding: 10px 8px !important;
    transition: all 0.15s !important;
}}
button[kind="secondary"]:hover {{
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.85) !important;
    border-bottom: 3px solid rgba(200,168,118,0.4) !important;
    box-shadow: none !important;
}}
/* 활성 탭 */
button[aria-label="{active_label}"] {{
    background: rgba(200,168,118,0.12) !important;
    color: #C8A876 !important;
    border-bottom: 3px solid #C8A876 !important;
    font-weight: 700 !important;
}}

/* Primary 버튼 = 골드 */
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

/* 다운로드 버튼 */
[data-testid="stDownloadButton"] button {{
    background: linear-gradient(135deg,#22c55e,#16a34a) !important;
    color: #fff !important; border: none !important;
    font-weight: 700 !important; border-radius: 8px !important;
}}

/* 입력 필드 */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #FFF !important;
}}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {{
    color: rgba(255,255,255,0.55) !important;
    font-size: 12px !important;
}}

/* 파일 업로더 */
[data-testid="stFileUploader"] {{
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
}}

/* 알림 */
[data-testid="stSuccess"] {{ background:rgba(34,197,94,0.08) !important; border:1px solid rgba(34,197,94,0.2) !important; border-radius:8px !important; }}
[data-testid="stInfo"]    {{ background:rgba(200,168,118,0.07) !important; border:1px solid rgba(200,168,118,0.2) !important; border-radius:8px !important; }}
[data-testid="stWarning"] {{ background:rgba(251,191,36,0.07) !important; border:1px solid rgba(251,191,36,0.2) !important; border-radius:8px !important; }}
[data-testid="stError"]   {{ background:rgba(239,68,68,0.07) !important;  border:1px solid rgba(239,68,68,0.2) !important;  border-radius:8px !important; }}

/* 익스팬더 */
[data-testid="stExpander"] {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary {{ color: rgba(255,255,255,0.75) !important; }}

/* 메트릭 */
[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 16px;
}}
[data-testid="stMetricValue"] {{ color: #C8A876 !important; }}
[data-testid="stMetricLabel"] {{ color: rgba(255,255,255,0.4) !important; }}

/* 셀렉트박스 */
[data-testid="stSelectbox"] > div > div {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important; color: #FFF !important;
}}

/* 색상피커 */
[data-testid="stColorPicker"] label {{ color: rgba(255,255,255,0.55) !important; font-size:12px !important; }}

/* 텍스트 */
p, li, span {{ color: rgba(255,255,255,0.72); }}
h1, h2, h3  {{ color: #FFF !important; }}
hr          {{ border-color: rgba(255,255,255,0.08) !important; margin: 12px 0 !important; }}

/* 구분선 위 헤더 영역 흉내 */
.ms-logo-row {{ display:flex; align-items:center; gap:12px; margin-bottom:4px; }}
.ms-logo {{
    width:36px; height:36px;
    background:linear-gradient(135deg,#C8A876,#E8C99A);
    border-radius:8px; display:flex; align-items:center; justify-content:center;
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:13px; color:#0A0A0F;
}}
.ms-title {{ font-family:'Montserrat',sans-serif; font-size:19px; font-weight:800; color:#FFF; letter-spacing:-0.4px; }}
.ms-title span {{ color:#C8A876; }}
.ms-sub {{ font-size:11px; color:rgba(255,255,255,0.28); margin-top:1px; }}
.section-title {{ font-size:20px; font-weight:700; color:#FFF; letter-spacing:-0.4px; margin-bottom:4px; }}
.section-desc  {{ font-size:12px; color:rgba(255,255,255,0.35); margin-bottom:20px; }}
.ms-footer     {{ text-align:center; padding:24px 0 8px 0; }}
.ms-footer p   {{ font-size:11px; color:rgba(255,255,255,0.15); line-height:1.7; margin:0; }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 헤더 — HTML div 없이 st 컴포넌트로만
# ══════════════════════════════════════════════
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

# ══════════════════════════════════════════════
# 탭 버튼 — st.columns + st.button 만 사용
# st.markdown div 래퍼 절대 없음
# ══════════════════════════════════════════════
tab_cols = st.columns(len(TABS))
for col, (tid, tlabel) in zip(tab_cols, TABS):
    with col:
        if st.button(tlabel, key=f"tab_{tid}", use_container_width=True):
            st.session_state.active_tab = tid
            st.rerun()

st.divider()

# ══════════════════════════════════════════════
# 페이지 컨텐츠 — div 래퍼 없이 직접 render()
# ══════════════════════════════════════════════
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

# ══════════════════════════════════════════════
# 푸터
# ══════════════════════════════════════════════
st.divider()
st.markdown("""
<div class="ms-footer">
  <p>made by MISHARP COMPANY, MIYAWA, 2026<br>
  이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.</p>
</div>
""", unsafe_allow_html=True)
