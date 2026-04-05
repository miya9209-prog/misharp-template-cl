"""
page_guide.py
─────────────
사용 가이드 페이지
"""

import streamlit as st


def render():
    st.markdown("""
    <div class="section-header">
        <div class="section-title">사용 가이드</div>
        <div class="section-desc">미샵 템플릿 OS 사용 방법 안내</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 전체 흐름도
    st.markdown("### 전체 작업 흐름")
    st.markdown("""
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                border-radius:12px;padding:28px;margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <div style="background:rgba(200,168,118,0.12);border:1px solid rgba(200,168,118,0.3);
                        border-radius:8px;padding:16px 20px;text-align:center;min-width:140px">
                <div style="font-size:28px">📁</div>
                <div style="color:#C8A876;font-weight:700;font-size:13px;margin-top:6px">상세페이지 JPG 업로드</div>
                <div style="color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px">완성된 상세페이지 원본</div>
            </div>
            <div style="color:rgba(255,255,255,0.2);font-size:24px">→</div>
            <div style="background:rgba(100,160,230,0.08);border:1px solid rgba(100,160,230,0.25);
                        border-radius:8px;padding:16px 20px;text-align:center;min-width:140px">
                <div style="font-size:28px">🤖</div>
                <div style="color:#78a8f0;font-weight:700;font-size:13px;margin-top:6px">AI 자동 분석</div>
                <div style="color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px">GPT-4o Vision으로 존 감지</div>
            </div>
            <div style="color:rgba(255,255,255,0.2);font-size:24px">→</div>
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
                        border-radius:8px;padding:16px 20px;text-align:center;min-width:140px">
                <div style="font-size:28px">✏️</div>
                <div style="color:#FFFFFF;font-weight:700;font-size:13px;margin-top:6px">수동 수정·확정</div>
                <div style="color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px">존 위치·크기 조정</div>
            </div>
            <div style="color:rgba(255,255,255,0.2);font-size:24px">→</div>
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
                        border-radius:8px;padding:16px 20px;text-align:center;min-width:140px">
                <div style="font-size:28px">💾</div>
                <div style="color:#FFFFFF;font-weight:700;font-size:13px;margin-top:6px">템플릿 저장</div>
                <div style="color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px">재사용 가능한 구조로</div>
            </div>
            <div style="color:rgba(255,255,255,0.2);font-size:24px">→</div>
            <div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);
                        border-radius:8px;padding:16px 20px;text-align:center;min-width:140px">
                <div style="font-size:28px">📦</div>
                <div style="color:#4ade80;font-weight:700;font-size:13px;margin-top:6px">PSD + JPG 출력</div>
                <div style="color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px">포토샵 레이어 파일</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### ① 템플릿 생성")
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                    border-radius:10px;padding:20px;font-size:13px;color:rgba(255,255,255,0.6);line-height:2">
        <b style="color:#C8A876">1. 이미지 업로드</b><br>
        미샵에서 완성한 상세페이지 JPG를 업로드합니다.<br>
        900px 너비 기준 이미지 권장.<br><br>
        <b style="color:#C8A876">2. AI 자동 분석</b><br>
        OpenAI API 키 입력 후 "AI 자동 분석" 클릭.<br>
        GPT-4o Vision이 이미지 존·텍스트 존을 자동 감지.<br>
        API 키 없으면 "기본 구조 적용"으로 일반 레이아웃 적용.<br><br>
        <b style="color:#C8A876">3. 존 수정</b><br>
        감지된 존의 위치·크기·이름을 직접 수정.<br>
        누락된 존은 "직접 추가"로 수동 추가.<br>
        "미리보기 생성"으로 존 위치 확인.<br><br>
        <b style="color:#C8A876">4. 템플릿 저장</b><br>
        이름·배경색 입력 후 저장.<br>
        저장된 템플릿은 ② 활용 탭에서 사용 가능.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ③ 템플릿 관리")
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                    border-radius:10px;padding:20px;font-size:13px;color:rgba(255,255,255,0.6);line-height:2">
        · 저장된 전체 템플릿 목록 확인<br>
        · 각 템플릿의 존 구성 태그로 한눈에 파악<br>
        · 불필요한 템플릿 삭제 (삭제 확인 2단계)<br>
        · 메트릭 카드로 전체 현황 확인
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### ② 템플릿 활용")
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                    border-radius:10px;padding:20px;font-size:13px;color:rgba(255,255,255,0.6);line-height:2">
        <b style="color:#C8A876">1. 템플릿 선택</b><br>
        저장된 템플릿 카드를 클릭하여 선택.<br><br>
        <b style="color:#C8A876">2. 콘텐츠 입력</b><br>
        · 이미지 존: 새 제품 사진 JPG/PNG 업로드<br>
        · 텍스트 존: 카피 직접 입력, 폰트 크기·색상 설정<br><br>
        <b style="color:#C8A876">3. 미리보기 확인</b><br>
        "미리보기 생성"으로 합성 결과 확인.<br><br>
        <b style="color:#C8A876">4. 출력 다운로드</b><br>
        "PSD + JPG 생성" 클릭 → ZIP 파일 다운로드.<br>
        ZIP 안에 포함된 파일:<br>
        &nbsp;&nbsp;· <b>_preview.jpg</b> — 최종 확인용 JPG<br>
        &nbsp;&nbsp;· <b>.psd</b> — 포토샵 레이어 파일<br>
        &nbsp;&nbsp;· <b>README.txt</b> — 사용 안내<br><br>
        <b style="color:#C8A876">5. 포토샵 마무리</b><br>
        .psd 파일을 포토샵에서 열어 레이어 편집.<br>
        이미지 레이어에 File > Place로 고화질 원본 배치.<br>
        텍스트 레이어 더블클릭으로 내용 수정.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 좌표 확인 방법")
        st.markdown("""
        <div style="background:rgba(200,168,118,0.05);border:1px solid rgba(200,168,118,0.15);
                    border-radius:10px;padding:20px;font-size:13px;color:rgba(255,255,255,0.6);line-height:2">
        AI 분석 시 좌표는 자동 감지됩니다.<br>
        수동으로 좌표를 확인하려면:<br>
        · <b>포토샵</b>: 정보 패널(Window > Info)에서 픽셀 좌표 확인<br>
        · <b>미리보기(Mac)</b>: Tools > Show Inspector에서 좌표 확인<br>
        · <b>Figma/XD</b>: 레이어 선택 후 X, Y, W, H 값 확인<br><br>
        기준: X=왼쪽에서, Y=위쪽에서 픽셀 거리
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="text-align:center;color:rgba(255,255,255,0.15);font-size:12px;padding:8px">
        문의: 미샵컴퍼니 내부 채널 &nbsp;|&nbsp; 
        made by MISHARP COMPANY, MIYAWA, 2026
    </div>
    """, unsafe_allow_html=True)
