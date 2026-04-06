import streamlit as st


def render():
    st.markdown('<div class="section-title">사용 가이드</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">미샵 템플릿 OS 사용 방법 안내</div>', unsafe_allow_html=True)

    st.markdown("### 전체 작업 흐름")
    st.markdown("""
**① 상세페이지 JPG 업로드 → ② AI 자동 분석 → ③ 존 수동 수정 → ④ 템플릿 저장 → ⑤ 새 콘텐츠 입력 → ⑥ PSD + JPG 출력**
    """)
    st.divider()

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### ① 템플릿 생성")
        st.markdown("""
**1. 이미지 업로드**
완성된 상세페이지 JPG 업로드 (900px 너비 권장, 세로 길이 제한 없음)

**2. AI 자동 분석**
- OpenAI API 키를 한 번 입력하면 세션 동안 유지됩니다 (재입력 불필요)
- "AI 자동 분석" → GPT-4o Vision이 존 자동 감지
- API 없으면 "기본 구조 적용"으로 일반 레이아웃 배치

**3. 존 수정**
- 감지된 존의 좌표·크기·이름 조정
- 누락된 존은 "직접 추가"로 수동 추가
- "미리보기 생성"으로 존 위치 확인

**4. 템플릿 저장**
이름·배경색 설정 후 저장 → ② 활용 탭에서 재사용
""")

        st.markdown("### ③ 템플릿 관리")
        st.markdown("""
- 저장된 전체 템플릿 목록 + 썸네일 확인
- 존 구성 태그로 한눈에 파악
- 불필요한 템플릿 2단계 확인 후 삭제
""")

    with col2:
        st.markdown("### ② 템플릿 활용")
        st.markdown("""
**1. 템플릿 선택**
저장된 템플릿 카드에서 선택

**2. 콘텐츠 입력**
- 🖼️ 이미지 존: 새 제품 사진 JPG/PNG 업로드
- ✏️ 텍스트 존: 카피 입력, 폰트 크기·색상·정렬 설정

**3. 미리보기 확인**
"미리보기 생성"으로 합성 결과 확인

**4. 출력 다운로드**
"PSD + JPG 생성" → ZIP 파일 다운로드

ZIP 포함 파일:
- `_preview.jpg` — 최종 확인용 JPG
- `.psd` — 포토샵 레이어 파일 (레이어 구분됨)
- `README.txt` — 사용 안내

**5. 포토샵 마무리**
`.psd` 파일 열기 → 이미지 레이어에 File > Place로 원본 배치 → 텍스트 더블클릭 편집
""")

        st.markdown("### OpenAI API 키 발급")
        st.markdown("""
1. [platform.openai.com](https://platform.openai.com) 접속
2. API Keys 메뉴 → Create new secret key
3. GPT-4o 모델 권한 필요 (유료 플랜)
4. **API 키는 저장되지 않으며 분석에만 사용됩니다**
5. 세션 동안 유지되므로 탭 이동해도 재입력 불필요
""")

    st.divider()
    st.caption("문의: 미샵컴퍼니 내부 채널 | made by MISHARP COMPANY, MIYAWA, 2026")
