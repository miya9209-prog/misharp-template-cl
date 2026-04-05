import streamlit as st


def render():
    st.markdown('<div class="section-title">사용 가이드</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">미샵 템플릿 OS 사용 방법 안내</div>', unsafe_allow_html=True)

    st.markdown("### 전체 작업 흐름")
    st.markdown("""
    **상세페이지 JPG 업로드 → AI 자동 분석 → 수동 수정·확정 → 템플릿 저장 → 새 콘텐츠 입력 → PSD + JPG 출력**
    """)
    st.divider()

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### ① 템플릿 생성")
        st.markdown("""
**1. 이미지 업로드**
미샵에서 완성한 상세페이지 JPG 업로드 (900px 너비 기준 권장)

**2. AI 자동 분석**
OpenAI API 키 입력 후 "AI 자동 분석" 클릭
→ GPT-4o Vision이 이미지 존·텍스트 존 자동 감지
→ API 없으면 "기본 구조 적용"으로 일반 레이아웃 배치

**3. 존 수정**
감지된 존의 위치·크기·이름 조정
누락된 존은 "직접 추가"로 수동 추가
"미리보기 생성"으로 존 위치 확인

**4. 템플릿 저장**
이름·배경색 입력 후 저장
저장된 템플릿은 ② 활용 탭에서 재사용
""")

        st.markdown("### ③ 템플릿 관리")
        st.markdown("""
- 저장된 전체 템플릿 목록 확인
- 존 구성 태그로 한눈에 파악
- 불필요한 템플릿 삭제 (2단계 확인)
- 메트릭으로 전체 현황 확인
""")

    with col2:
        st.markdown("### ② 템플릿 활용")
        st.markdown("""
**1. 템플릿 선택**
저장된 템플릿 카드 클릭

**2. 콘텐츠 입력**
- 이미지 존: 새 제품 사진 JPG/PNG 업로드
- 텍스트 존: 카피 직접 입력, 폰트 크기·색상 설정

**3. 미리보기 확인**
"미리보기 생성"으로 합성 결과 확인

**4. 출력 다운로드**
"PSD + JPG 생성" → ZIP 파일 다운로드

ZIP 포함 파일:
- `_preview.jpg` — 최종 확인용 JPG
- `.psd` — 포토샵 레이어 파일
- `README.txt` — 사용 안내

**5. 포토샵 마무리**
.psd 파일을 포토샵에서 열어 레이어 편집
이미지 레이어에 File > Place로 고화질 원본 배치
텍스트 레이어 더블클릭으로 내용 수정
""")

        st.markdown("### 좌표 확인 방법")
        st.markdown("""
AI 분석 시 좌표는 자동 감지됩니다.
수동으로 좌표를 확인하려면:
- **포토샵**: Window > Info 패널에서 픽셀 좌표 확인
- **Figma/XD**: 레이어 선택 후 X, Y, W, H 값 확인
- 기준: X=왼쪽에서, Y=위쪽에서 픽셀 거리
""")

    st.divider()
    st.caption("문의: 미샵컴퍼니 내부 채널 | made by MISHARP COMPANY, MIYAWA, 2026")
