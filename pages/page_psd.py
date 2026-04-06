"""
page_psd.py — ② PSD 템플릿 활용
PSD 파일을 업로드하면 레이어 구조를 자동 파악하고
텍스트/이미지를 교체하는 JSX 스크립트를 생성합니다.
"""

import streamlit as st
import streamlit.components.v1 as components
import io, sys, os, base64, zipfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.psd_jsx_builder import build_psd_edit_jsx


# ─────────────────────────────────────────────
def scrollable_img(img_bytes, height=600):
    b64 = base64.b64encode(img_bytes).decode()
    html = f"""<!DOCTYPE html><html><head><style>
        body{{margin:0;background:#0a0a0f;}}
        .v{{width:100%;height:{height}px;overflow-y:scroll;overflow-x:hidden;
            background:#111;border:1px solid rgba(255,255,255,0.12);border-radius:8px;}}
        img{{width:100%;display:block;}}
        .info{{color:#888;font-size:11px;text-align:center;padding:4px;font-family:sans-serif;}}
    </style></head><body>
    <div class="v"><img src="data:image/jpeg;base64,{b64}"/></div>
    <div class="info">↕ 스크롤하여 전체 확인</div>
    </body></html>"""
    components.html(html, height=height+30, scrolling=False)


def render():
    st.markdown('<div class="section-title">② PSD 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">기존 PSD 파일을 업로드하면 레이어를 자동 분석합니다. 텍스트·이미지를 교체하고 포토샵 스크립트로 저장하세요.</div>', unsafe_allow_html=True)

    for k, v in [("psd_info",None),("psd_bytes",None),("psd_preview",None),
                 ("psd_txt_rep",{}),("psd_img_rep",{}),("psd_fname","")]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── STEP 1: PSD 업로드
    st.markdown('<div class="step-header">STEP 1 · PSD 파일 업로드</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "PSD 파일 업로드 (포토샵 CS5 이상에서 저장된 파일)",
        type=["psd"], key="psd_upload",
    )

    if uploaded:
        with st.spinner("PSD 파싱 중... 레이어 구조 분석 중입니다"):
            raw = uploaded.read()
            try:
                info = parse_psd(raw)
                st.session_state.psd_info   = info
                st.session_state.psd_bytes  = raw
                st.session_state.psd_fname  = uploaded.name
                st.session_state.psd_txt_rep = {}
                st.session_state.psd_img_rep = {}
                # 병합 이미지 추출
                try:
                    prev = psd_to_preview_jpg(raw, max_width=700)
                    st.session_state.psd_preview = prev
                except Exception as e:
                    st.session_state.psd_preview = None
                    st.warning(f"미리보기 추출 실패: {e}")
                n_txt = sum(1 for l in info['layers'] if l['type']=='text')
                n_pix = sum(1 for l in info['layers'] if l['type']=='pixel')
                st.success(f"✅ 파싱 완료 | {info['width']}×{info['height']}px | 레이어 {info['num_layers']}개 (텍스트 {n_txt} · 이미지 {n_pix})")
            except Exception as e:
                st.error(f"PSD 파싱 오류: {e}")
                return

    if not st.session_state.psd_info:
        st.info("PSD 파일을 업로드하면 레이어 구조가 자동으로 분석됩니다")
        return

    info   = st.session_state.psd_info
    layers = info['layers']
    text_layers  = [l for l in layers if l['type']=='text'   and l['w']>0]
    pixel_layers = [l for l in layers if l['type']=='pixel'  and l['w']>0 and l['h']>0
                    and l['w']*l['h'] > 100]  # 너무 작은 건 제외

    st.divider()

    # ── STEP 2: 레이어 편집
    st.markdown('<div class="step-header">STEP 2 · 텍스트 · 이미지 교체</div>', unsafe_allow_html=True)

    col_edit, col_prev = st.columns([1,1], gap="large")

    with col_edit:
        # ── 텍스트 레이어
        st.markdown(f"**✏️ 텍스트 레이어 ({len(text_layers)}개)**")
        st.caption("교체할 텍스트를 입력하세요. 비워두면 원본 유지.")

        txt_rep = dict(st.session_state.psd_txt_rep)
        for l in text_layers:
            orig = l['text'].split('\n')[0][:50] if l['text'] else l['name']
            with st.expander(f"✏️ {l['name']}  ← {repr(orig)}", expanded=False):
                st.caption(f"위치: ({l['rect'][1]},{l['rect'][0]}) | 크기: {l['w']}×{l['h']}px")
                if l['text']:
                    st.markdown(f"**원본:**")
                    st.code(l['text'].replace('\n','↵'), language=None)
                new_val = st.text_area(
                    "새 텍스트 (줄바꿈 포함 가능)",
                    value=txt_rep.get(l['idx'], ''),
                    height=80, key=f"psd_txt_{l['idx']}",
                    placeholder="비워두면 원본 유지",
                )
                if new_val.strip():
                    txt_rep[l['idx']] = new_val
                elif l['idx'] in txt_rep:
                    del txt_rep[l['idx']]
        st.session_state.psd_txt_rep = txt_rep

        st.divider()

        # ── 픽셀(이미지) 레이어
        st.markdown(f"**🖼️ 이미지 레이어 ({len(pixel_layers)}개)**")
        st.caption("교체할 이미지를 업로드하세요. 업로드하지 않으면 원본 유지.")

        img_rep = dict(st.session_state.psd_img_rep)
        # 주요 이미지 레이어만 (너무 많으면 UX 복잡)
        show_layers = [l for l in pixel_layers if l['w'] > 100 and l['h'] > 100][:12]
        for l in show_layers:
            with st.expander(f"🖼️ {l['name']}  {l['w']}×{l['h']}px", expanded=False):
                st.caption(f"위치: ({l['rect'][1]},{l['rect'][0]}) | 크기: {l['w']}×{l['h']}px")
                up = st.file_uploader(
                    f"교체 이미지 (권장: {l['w']}×{l['h']}px)",
                    type=["jpg","jpeg","png"], key=f"psd_img_{l['idx']}",
                )
                if up:
                    raw_img = up.read()
                    img_rep[l['idx']] = raw_img
                    th = Image.open(io.BytesIO(raw_img)); th.thumbnail((160,160))
                    st.image(th, width=130)
                elif l['idx'] in img_rep:
                    st.success("✓ 이미지 교체 예정")
        st.session_state.psd_img_rep = img_rep

        # 교체 현황
        st.divider()
        n_txt_rep = len(st.session_state.psd_txt_rep)
        n_img_rep = len(st.session_state.psd_img_rep)
        if n_txt_rep or n_img_rep:
            st.success(f"교체 예정: 텍스트 {n_txt_rep}개 · 이미지 {n_img_rep}개")
        else:
            st.info("교체할 내용을 입력하면 여기에 표시됩니다")

    with col_prev:
        st.markdown("**PSD 원본 미리보기**")
        st.caption("병합(Flatten) 이미지 | 스크롤로 전체 확인")
        if st.session_state.psd_preview:
            scrollable_img(st.session_state.psd_preview, height=620)
        else:
            st.info("미리보기를 불러올 수 없습니다")

        st.divider()

        # 레이어 구조 요약
        st.markdown("**레이어 구조**")
        for l in layers:
            if l['type'] == 'group_close': continue
            icon  = {'text':'✏️','pixel':'🖼️','group_open':'📁'}.get(l['type'],'❓')
            indent = "　" if l['type'] != 'group_open' else ""
            is_txt = l['idx'] in st.session_state.psd_txt_rep
            is_img = l['idx'] in st.session_state.psd_img_rep
            badge  = " 🔄" if (is_txt or is_img) else ""
            name_show = l['name'][:28]
            color = "#C8A876" if is_txt or is_img else "rgba(255,255,255,0.6)"
            st.markdown(
                f'<div style="font-size:12px;color:{color};padding:2px 0">'
                f'{indent}{icon} {name_show}{badge}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── STEP 3: 출력
    st.markdown('<div class="step-header">STEP 3 · 포토샵 스크립트 생성 및 다운로드</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
    <strong style="color:#C8A876">📌 사용 방법</strong><br>
    <span style="color:#C0C0C0;font-size:13px">
    1. 아래 버튼으로 ZIP 다운로드<br>
    2. ZIP 안의 <code>.jsx</code> 파일을 포토샵에서 실행<br>
       &nbsp;&nbsp;&nbsp;(File > Scripts > Browse → jsx 파일 선택)<br>
    3. 원본 PSD 파일 위치를 지정하면 자동으로 레이어 교체<br>
    4. 교체 완료된 PSD가 원본 폴더에 저장됨 (CS5~CC 전버전 지원)
    </span>
    </div>
    """, unsafe_allow_html=True)

    if not (st.session_state.psd_txt_rep or st.session_state.psd_img_rep):
        st.warning("교체할 텍스트 또는 이미지를 먼저 입력해주세요")
    else:
        if st.button("⚙️ 포토샵 스크립트 생성", use_container_width=True, type="primary", key="psd_genbtn"):
            with st.spinner("스크립트 생성 중..."):
                try:
                    jsx = build_psd_edit_jsx(
                        psd_filename  = st.session_state.psd_fname,
                        psd_info      = info,
                        text_replacements = st.session_state.psd_txt_rep,
                        image_replacements = st.session_state.psd_img_rep,
                    )
                    safe = st.session_state.psd_fname.replace('.psd','').replace(' ','_')[:30]
                    from datetime import datetime
                    now = datetime.now().strftime('%Y%m%d_%H%M')

                    # ZIP 생성
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{safe}_교체스크립트_{now}.jsx", jsx.encode('utf-8'))
                        readme = f"""미샵 템플릿 OS - PSD 레이어 교체 패키지
==========================================
원본 PSD: {st.session_state.psd_fname}
생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}

교체 내역
---------
텍스트: {len(st.session_state.psd_txt_rep)}개 레이어
이미지: {len(st.session_state.psd_img_rep)}개 레이어

사용 방법
---------
1. 포토샵 실행
2. File > Scripts > Browse
3. {safe}_교체스크립트_{now}.jsx 선택
4. 원본 PSD 파일 위치 지정
5. 자동으로 레이어 교체 후 저장

지원 버전: Photoshop CS5 ~ CC 전버전

────────────────────────────────
made by MISHARP COMPANY, MIYAWA, 2026
"""
                        zf.writestr("README.txt", readme.encode('utf-8'))

                    st.download_button(
                        "⬇️ ZIP 다운로드 (JSX 스크립트 + README)",
                        data=buf.getvalue(),
                        file_name=f"misharp_psd_{safe}_{now}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 스크립트 생성 완료!")
                except Exception as e:
                    st.error(f"생성 오류: {e}")
