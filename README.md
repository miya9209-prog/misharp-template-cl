# 미샵 템플릿 OS
**상세페이지 자동화를 위한 이미지 편집 템플릿 제공**

> made by MISHARP COMPANY, MIYAWA, 2026  
> 이 프로그램은 미샵컴퍼니 내부직원용이며 외부유출 및 무단 사용을 금합니다.

---

## 핵심 기능

| 탭 | 기능 |
|---|---|
| ① 템플릿 생성 | 완성된 상세페이지 JPG 업로드 → GPT-4o Vision 자동 분석 → 이미지/텍스트 존 수동 수정 → 템플릿 저장 |
| ② 템플릿 활용 | 저장된 템플릿 선택 → 새 제품 이미지·카피 입력 → PSD + JPG ZIP 출력 |
| ③ 템플릿 관리 | 저장 목록 확인 · 삭제 |
| 사용 가이드 | 전체 흐름 및 포토샵 연동 방법 안내 |

---

## 설치 방법

### 1. Python 환경
Python 3.11 이상 권장

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 사용 방법

### 템플릿 생성 (① 탭)

1. **이미지 업로드**: 미샵에서 완성한 상세페이지 JPG 업로드 (900px 너비 기준)
2. **AI 자동 분석**:
   - OpenAI API 키 입력 (sk-로 시작)
   - "AI 자동 분석" 클릭 → GPT-4o Vision이 이미지/텍스트 존 자동 감지
   - API 없을 경우 "기본 구조 적용"으로 일반 레이아웃 자동 배치
3. **존 수정**: 감지된 존의 위치·크기 확인 및 조정, 누락 존 수동 추가
4. **미리보기**: "존 위치 미리보기 생성"으로 확인
5. **저장**: 템플릿 이름·배경색 설정 후 저장

### 템플릿 활용 (② 탭)

1. 저장된 템플릿 선택
2. 이미지 존: 새 제품 사진 업로드
3. 텍스트 존: 카피 입력, 폰트 크기·색상 설정
4. 미리보기 확인
5. "PSD + JPG 생성" → ZIP 다운로드

### 출력 파일 구성 (ZIP)

```
misharp_[템플릿명].zip
├── [템플릿명]_preview_[날짜].jpg   ← 최종 확인용 JPG
├── [템플릿명]_[날짜].psd           ← 포토샵 레이어 파일
└── README.txt                       ← 사용 안내
```

### 포토샵 PSD 사용법

1. `.psd` 파일을 포토샵으로 열기
2. 레이어 패널 확인:
   - `배경색` — 배경 단색 레이어
   - `템플릿_원본` — 원본 상세페이지 이미지
   - `[이미지_교체]_존이름` — 새 이미지 삽입할 자리 (투명 플레이스홀더)
   - `텍스트_존이름` — 카피 텍스트 레이어
3. `[이미지_교체]` 레이어 선택 → File > Place Embedded로 고화질 이미지 삽입
4. 텍스트 레이어 더블클릭 → 내용 수정
5. 마무리 편집 후 File > Export > Save for Web으로 JPG 저장

---

## OpenAI API 키 발급

1. [platform.openai.com](https://platform.openai.com) 접속
2. API Keys 메뉴 → Create new secret key
3. GPT-4o 모델 사용 권한 필요 (유료 플랜)
4. 프로그램 내 API 키는 저장되지 않으며 분석에만 사용됨

---

## 기술 스택

- **Frontend/서버**: Streamlit
- **AI 분석**: OpenAI GPT-4o Vision API
- **이미지 처리**: Pillow (PIL)
- **PSD 생성**: 직접 바이너리 구현 (Adobe PSD 스펙 기반)
- **배포**: GitHub + Streamlit Cloud 또는 로컬 실행

---

## 파일 구조

```
misharp_template_os/
├── app.py                    # 메인 앱 (상단 탭 라우팅)
├── requirements.txt
├── .streamlit/
│   └── config.toml           # 테마 설정
├── pages/
│   ├── page_create.py        # ① 템플릿 생성
│   ├── page_use.py           # ② 템플릿 활용
│   ├── page_manage.py        # ③ 템플릿 관리
│   └── page_guide.py         # 사용 가이드
├── utils/
│   ├── ai_analyzer.py        # GPT-4o Vision 분석
│   ├── composer.py           # 이미지 합성 + PSD/ZIP 출력
│   ├── psd_writer.py         # PSD 바이너리 생성
│   └── template_manager.py  # 템플릿 저장·로드·삭제
└── templates/                # 저장된 템플릿 (자동 생성)
    ├── _meta.json
    └── tpl_YYYYMMDD_HHMMSS/
        ├── source.jpg
        └── thumb.jpg
```
