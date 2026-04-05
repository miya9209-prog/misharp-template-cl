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

# 활성 탭 라벨
active_label = next(label for tid, label in TABS if tid == active)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Montserrat:wght@400;600;800&display=swap');

/* ── 전체 배경 */
[data-testid="stAppViewContainer"] {{ background:#0A0A0F !important; font-family:'Noto Sans KR',sans-serif; }}
[data-testid="stHeader"]  {{ background:transparent !important; }}
[data-testid="stSidebar"] {{ display:none !important; }}
.block-container          {{ padding:0 !important; max-width:100% !important; }}

/* ── 헤더 영역 */
.ms-header {{
    background:linear-gradient(135deg,#0D0D1A 0%,#10102A 60%,#0D0D1A 100%);
    padding:20px 44px 0 44px;
    border-bottom:1px solid rgba(255,255,255,0.06);
    margin-bottom:0;
}}
.ms-logo-row {{ display:flex; align-items:center; gap:14px; margin-bottom:14px; }}
.ms-logo {{
    width:38px; height:38px;
    background:linear-gradient(135deg,#C8A876,#E8C99A);
    border-radius:8px; display:flex; align-items:center; justify-content:center;
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:14px;
    color:#0A0A0F; flex-shrink:0;
}}
.ms-title {{ font-family:'Montserrat',sans-serif; font-size:20px; font-weight:800; color:#FFF; letter-spacing:-0.5px; }}
.ms-title span {{ color:#C8A876; }}
.ms-sub {{ font-size:11px; color:rgba(255,255,255,0.3); margin-top:2px; }}

/* ── 탭 컨테이너: block-container 첫 번째 row */
/* 탭 행 배경을 헤더와 이어지게 */
div[data-testid="stHorizontalBlock"]:first-of-type {{
    background:linear-gradient(135deg,#0D0D1A 0%,#10102A 60%,#0D0D1A 100%);
    border-bottom:1px solid rgba(255,255,255,0.07);
    padding:0 40px !important;
    gap:0 !important;
    margin:0 !important;
}}
div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"] {{
    padding:0 !important;
}}

/* ── 탭 버튼 전체 (첫 번째 row 안의 버튼) */
div[data-testid="stHorizontalBlock"]:first-of-type button {{
    background:transparent !important;
    border:none !important;
    border-bottom:3px solid transparent !important;
    border-radius:0 !important;
    box-shadow:none !important;
    color:rgba(255,255,255,0.4) !important;
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:13px !important;
    font-weight:500 !important;
    padding:10px 4px 11px !important;
    width:100% !important;
    letter-spacing:0.2px !important;
    transition:color 0.15s, border-color 0.15s !important;
}}
div[data-testid="stHorizontalBlock"]:first-of-type button:hover {{
    background:transparent !important;
    color:rgba(255,255,255,0.85) !important;
    border-bottom:3px solid rgba(255,255,255,0.18) !important;
    box-shadow:none !important;
}}

/* ── 활성 탭 버튼: aria-label로 타겟팅 */
div[data-testid="stHorizontalBlock"]:first-of-type button[aria-label="{active_label}"] {{
    color:#C8A876 !important;
    border-bottom:3px solid #C8A876 !important;
    font-weight:700 !important;
    background:transparent !important;
}}

/* ── 메인 컨텐츠 */
.ms-main {{ padding:32px 44px 0 44px; min-height:calc(100vh - 150px); }}
.section-header {{ margin-bottom:28px; }}
.section-title  {{ font-size:22px; font-weight:700; color:#FFF; letter-spacing:-0.5px; }}
.section-desc   {{ font-size:13px; color:rgba(255,255,255,0.35); margin-top:5px; }}

/* ── 입력 필드 */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.11) !important;
    border-radius:8px !important; color:#FFF !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color:rgba(200,168,118,0.55) !important;
    box-shadow:0 0 0 2px rgba(200,168,118,0.09) !important;
}}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {{
    color:rgba(255,255,255,0.5) !important; font-size:12px !important;
}}

/* ── 일반 버튼 */
button[kind="secondary"] {{
    background:rgba(255,255,255,0.06) !important;
    color:rgba(255,255,255,0.82) !important;
    border:1px solid rgba(255,255,255,0.13) !important;
    border-radius:8px !important;
    font-family:'Noto Sans KR',sans-serif !important;
    font-size:13px !important;
    transition:all 0.18s !important;
}}
button[kind="secondary"]:hover {{
    background:rgba(255,255,255,0.1) !important;
    border-color:rgba(255,255,255,0.22) !important;
}}

/* ── Primary 버튼 = 골드 */
button[kind="primary"] {{
    background:linear-gradient(135deg,#C8A876,#B8946A) !important;
    color:#0A0A0F !important; border:none !important;
    font-weight:700 !important; border-radius:8px !important;
}}
button[kind="primary"]:hover {{
    background:linear-gradient(135deg,#D9BA8A,#C8A876) !important;
    box-shadow:0 4px 18px rgba(200,168,118,0.28) !important;
}}

/* ── 다운로드 버튼 */
[data-testid="stDownloadButton"] button {{
    background:linear-gradient(135deg,#22c55e,#16a34a) !important;
    color:#fff !important; border:none !important;
    font-weight:700 !important; border-radius:8px !important;
}}

/* ── 파일 업로더 */
[data-testid="stFileUploader"] {{
    background:rgba(255,255,255,0.03) !important;
    border:1.5px dashed rgba(255,255,255,0.13) !important;
    border-radius:10px !important;
}}

/* ── 알림 */
[data-testid="stSuccess"] {{ background:rgba(34,197,94,0.07) !important; border:1px solid rgba(34,197,94,0.2) !important; border-radius:8px !important; }}
[data-testid="stInfo"]    {{ background:rgba(200,168,118,0.06) !important; border:1px solid rgba(200,168,118,0.2) !important; border-radius:8px !important; }}
[data-testid="stWarning"] {{ background:rgba(251,191,36,0.06) !important; border:1px solid rgba(251,191,36,0.2) !important; border-radius:8px !important; }}
[data-testid="stError"]   {{ background:rgba(239,68,68,0.06) !important;  border:1px solid rgba(239,68,68,0.2) !important;  border-radius:8px !important; }}

/* ── 익스팬더 */
[data-testid="stExpander"] {{
    background:rgba(255,255,255,0.025) !important;
    border:1px solid rgba(255,255,255,0.07) !important; border-radius:8px !important;
}}
[data-testid="stExpander"] summary {{ color:rgba(255,255,255,0.7) !important; }}

/* ── 메트릭 */
[data-testid="stMetric"] {{
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
    border-radius:10px; padding:16px;
}}
[data-testid="stMetricValue"] {{ color:#C8A876 !important; }}
[data-testid="stMetricLabel"] {{ color:rgba(255,255,255,0.4) !important; }}

/* ── 셀렉트박스 */
[data-testid="stSelectbox"] > div > div {{
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.11) !important;
    border-radius:8px !important; color:#FFF !important;
}}

p, li {{ color:rgba(255,255,255,0.72); }}
h1,h2,h3 {{ color:#FFF; }}
hr {{ border-color:rgba(255,255,255,0.07) !important; }}

/* ── 푸터 */
.ms-footer {{
    background:rgba(0,0,0,0.35); border-top:1px solid rgba(255,255,255,0.05);
    padding:14px 44px; margin-top:48px; text-align:center;
}}
.ms-footer p {{ font-size:11px; color:rgba(255,255,255,0.18); line-height:1.7; margin:0; }}
</style>
""", unsafe_allow_html=True)

# ── 로고/타이틀 헤더
st.markdown("""
<div class="ms-header">
  <div class="ms-logo-row">
    <div class="ms-logo">MS</div>
    <div>
      <div class="ms-title">미샵 <span>템플릿</span> OS</div>
      <div class="ms-sub">상세페이지 자동화를 위한 이미지 편집 템플릿 제공</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 탭 버튼 행 ─────────────────────────────────
# 핵심: st.markdown div 래퍼 절대 사용 안 함
# st.columns + st.button 만으로 구성 → 클릭 100% 보장
cols = st.columns(len(TABS))
for col, (tid, tlabel) in zip(cols, TABS):
    with col:
        if st.button(tlabel, key=f"tab_{tid}", use_container_width=True):
            st.session_state.active_tab = tid
            st.rerun()

# ── 구분선
st.markdown("<hr style='margin:0 0 0 0;'>", unsafe_allow_html=True)

# ── 메인 컨텐츠
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
  <p>made by MISHARP COMPANY, MIYAWA, 2026<br>
  이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.</p>
</div>
""", unsafe_allow_html=True)
