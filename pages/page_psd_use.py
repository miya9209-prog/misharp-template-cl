"""
page_psd_use.py — PSD 템플릿 활용
우측: PSD 이미지를 레이어 구간별로 잘라 표시 + 각 구간 옆에 st.button
      → 버튼 클릭 시 좌측 입력칸 100% 활성화 (iframe 통신 없음)
"""
import streamlit as st
import io, sys, os, base64, json, zipfile
from datetime import datetime
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
from utils.psd_parser import psd_to_preview_jpg
from utils.psd_jsx_builder import build_psd_edit_jsx


# ──────────────────────────────────────────────────────────
# 이미지 슬라이스 생성
# ──────────────────────────────────────────────────────────

def draw_layer_on_img(img_rgba: Image.Image, layer, active_idx, inputs, sx, sy):
    """이미지 위에 레이어 박스 오버레이 그리기"""
    t, le, b, r = layer['rect']
    x1, y1 = int(le*sx), int(t*sy)
    x2, y2 = int(r*sx),  int(b*sy)
    if x2-x1 < 2 or y2-y1 < 2:
        return
    lt    = layer['type']
    is_a  = (layer['idx'] == active_idx)
    has_v = bool(inputs.get(layer['idx'], {}).get('value'))

    ov  = Image.new("RGBA", img_rgba.size, (0,0,0,0))
    drw = ImageDraw.Draw(ov)

    if has_v:
        fill, outline, w = (50,220,80,55), (50,220,80,230), 3
    elif is_a:
        fill    = (255,200,0,90)  if lt=='text' else (100,160,255,90)
        outline = (255,200,0,255) if lt=='text' else (100,160,255,255)
        w = 4
    else:
        fill    = (255,200,0,20)  if lt=='text' else (100,160,255,15)
        outline = (255,200,0,120) if lt=='text' else (100,160,255,90)
        w = 1

    drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=w)
    if is_a:
        lh = min(30, y2-y1)
        drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
        drw.text((x1+5, y1+6), f"{'✏' if lt=='text' else '🖼'} {layer['name'][:26]}", fill=(255,255,255))
    elif has_v:
        drw.text((x1+4, y1+4), "✓", fill=(50,220,80,230))

    img_rgba.alpha_composite(ov)


def slice_and_display(prev_bytes, editable_layers, active_idx, inputs, W_orig, H_orig, display_w=440):
    """
    PSD 이미지를 레이어 Y좌표 기준으로 구간 분할.
    각 구간 이미지 + 해당 레이어 버튼을 나란히 표시.
    버튼 클릭 → session_state.pu_active 변경 → rerun
    """
    full_img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH   = full_img.size
    sx = pW / W_orig
    sy = pH / H_orig

    # 모든 레이어 오버레이
    for l in editable_layers:
        draw_layer_on_img(full_img, l, active_idx, inputs, sx, sy)

    full_rgb = full_img.convert("RGB")

    # 레이어를 Y 위치 기준으로 정렬
    sorted_layers = sorted(editable_layers, key=lambda l: l['rect'][0])

    # 구간 계산: 레이어들을 그룹핑 (겹치거나 가까운 것끼리)
    # → 간단하게 각 레이어마다 ±패딩 구간의 이미지 슬라이스 제공
    shown_slices = set()  # 중복 표시 방지

    for l in sorted_layers:
        t, le, b, r = l['rect']
        lt    = l['type']
        is_a  = (l['idx'] == active_idx)
        has_v = bool(inputs.get(l['idx'], {}).get('value'))

        # 슬라이스 Y 범위 (패딩 포함)
        pad   = 30
        y_top = max(0, int(t*sy) - pad)
        y_bot = min(pH, int(b*sy) + pad)

        # 너무 얇은 슬라이스는 최소 높이 보장
        if y_bot - y_top < 60:
            mid = (y_top + y_bot) // 2
            y_top = max(0, mid - 40)
            y_bot = min(pH, mid + 40)

        # 슬라이스 이미지
        slice_img = full_rgb.crop((0, y_top, pW, y_bot))
        # display_w 기준으로 리사이즈
        ratio     = display_w / pW
        new_h     = max(30, int((y_bot-y_top)*ratio))
        slice_img = slice_img.resize((display_w, new_h), Image.LANCZOS)

        # 버튼 색상
        t_col    = "#C8A876"    if lt=='text' else "#78a8f0"
        icon     = "✏️"         if lt=='text' else "🖼️"
        status   = "✅" if has_v else ("▶ 선택됨" if is_a else "")
        btn_type = "primary" if is_a else "secondary"

        # 이미지 + 버튼 나란히 (2열)
        img_col, btn_col = st.columns([3, 2], gap="small")

        with img_col:
            buf = io.BytesIO()
            slice_img.save(buf, "JPEG", quality=82)
            b64 = base64.b64encode(buf.getvalue()).decode()
            border = f"2px solid {t_col}" if is_a else "1px solid rgba(255,255,255,0.1)"
            st.markdown(
                f'<img src="data:image/jpeg;base64,{b64}" '
                f'style="width:100%;border-radius:6px;border:{border};display:block">',
                unsafe_allow_html=True,
            )

        with btn_col:
            st.markdown(f'<div style="height:8px"></div>', unsafe_allow_html=True)
            # 레이어 정보
            st.markdown(
                f'<div style="color:{t_col};font-size:11px;font-weight:700;margin-bottom:4px">'
                f'{icon} {l["name"][:20]}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f'{l["w"]}×{l["h"]}px')
            if status:
                st.markdown(f'<div style="color:{t_col};font-size:11px">{status}</div>', unsafe_allow_html=True)

            # ★ 핵심: 순수 st.button → 클릭 100% 보장
            if st.button(
                "여기 편집 →" if not is_a else "✏ 편집 중",
                key=f"pu_slice_{l['idx']}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.pu_active = l['idx']
                st.rerun()

        st.markdown('<div style="margin-bottom:6px"></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# 메인 렌더
# ──────────────────────────────────────────────────────────

def render():
    st.markdown('<div class="section-title">③ 템플릿 불러오기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 PSD 템플릿을 불러와 텍스트·이미지를 교체하고 새 PSD로 저장하세요</div>', unsafe_allow_html=True)

    for k, v in [("pu_selected",None),("pu_inputs",{}),("pu_active",None),("pu_prev",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    all_tpl = {k:v for k,v in load_all().items() if v.get("template_type")=="psd"}
    if not all_tpl:
        st.info("저장된 PSD 템플릿이 없습니다. ① PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택
    if not st.session_state.pu_selected:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row in range(0, len(tpl_list), 4):
            cols = st.columns(4, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row:row+4]):
                with cols[ci]:
                    st.markdown(f"**{meta['name']}**")
                    w, h = meta.get("canvas_size",[0,0])
                    st.caption(f"PSD · {w}×{h}px · {meta['created_at'][:10]}")
                    if meta.get("description"): st.caption(meta["description"])
                    if st.button("사용 →", key=f"psel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.pu_selected = tid
                        st.session_state.pu_inputs   = {}
                        st.session_state.pu_active   = None
                        st.session_state.pu_prev     = None
                        st.rerun()
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;max-height:150px;object-fit:cover;object-position:top;'
                            f'border-radius:6px;border:1px solid rgba(255,255,255,0.08);margin-top:4px">',
                            unsafe_allow_html=True,
                        )
        return

    # ── 작업 화면
    tid       = st.session_state.pu_selected
    meta      = load_one(tid)
    info      = load_psd_info(tid)
    psd_bytes = get_psd_bytes(tid)

    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_selected = None; return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_idxs = set(int(k) for k,v in info.get('editable_layers',{}).items() if v)
    editable_layers = [l for l in layers
                       if l['idx'] in editable_idxs and l['w']>0 and l['h']>0]
    txt_layers = [l for l in editable_layers if l['type']=='text']
    img_layers = [l for l in editable_layers if l['type']=='pixel']

    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try:
                st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except Exception:
                st.session_state.pu_prev = b""

    # 상단 정보 바
    st.markdown(f"""<div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {meta['name']}</strong>
        <span style="color:#A0A0A0;font-size:12px;margin-left:12px">
        PSD | {W}×{H}px | ✏️ {len(txt_layers)} · 🖼️ {len(img_layers)}
        </span>
    </div>""", unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="pu_back"):
        st.session_state.pu_selected = None; st.rerun()

    st.divider()

    inputs       = st.session_state.pu_inputs
    active       = st.session_state.pu_active
    active_layer = next((l for l in layers if l['idx']==active), None)

    # ══════════════════════════════════════════════════════════
    # 2열 레이아웃
    # 왼쪽: 활성 입력칸 + 레이어 목록 버튼
    # 오른쪽: 이미지 슬라이스 + 편집 버튼 (레이어 위치별)
    # ══════════════════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1], gap="large")

    # ── 왼쪽
    with col_left:
        st.markdown("### 입력")

        # 활성 레이어 입력칸
        if active_layer:
            lt    = active_layer['type']
            lname = active_layer['name']
            t_col = "#C8A876" if lt=='text' else "#78a8f0"
            bg    = "rgba(200,168,118,0.10)" if lt=='text' else "rgba(100,160,230,0.08)"
            icon  = "✏️" if lt=='text' else "🖼️"

            st.markdown(
                f'<div style="background:{bg};border:2px solid {t_col};border-radius:10px;'
                f'padding:10px 14px 4px 14px;margin-bottom:6px">'
                f'<span style="color:{t_col};font-weight:700;font-size:14px">{icon} {lname}</span>'
                f'<span style="color:#888;font-size:11px;margin-left:8px">'
                f'{active_layer["w"]}×{active_layer["h"]}px</span></div>',
                unsafe_allow_html=True,
            )

            inp = inputs.get(active_layer['idx'], {})

            if lt == 'text':
                orig = active_layer.get('text','').split('\n')[0][:60]
                if orig: st.caption(f"원본: {orig}")
                new_txt = st.text_area(
                    "새 텍스트",
                    value=inp.get('value',''),
                    height=90,
                    key=f"pu_txt_{active_layer['idx']}",
                    placeholder="교체할 텍스트 입력 (비우면 원본 유지)",
                )
                if new_txt.strip():
                    inputs[active_layer['idx']] = {'value': new_txt, 'type': 'text'}
                elif active_layer['idx'] in inputs:
                    del inputs[active_layer['idx']]
                st.session_state.pu_inputs = inputs

            else:
                st.caption(f"권장: {active_layer['w']}×{active_layer['h']}px")
                up = st.file_uploader(
                    "교체할 이미지 (JPG / PNG)",
                    type=["jpg","jpeg","png"],
                    key=f"pu_img_{active_layer['idx']}",
                )
                if up:
                    raw_img = up.read()
                    inputs[active_layer['idx']] = {'value': raw_img, 'type': 'image'}
                    st.session_state.pu_inputs = inputs
                    th = Image.open(io.BytesIO(raw_img)); th.thumbnail((200,160))
                    st.image(th, width=160, caption="선택된 이미지")
                elif inp.get('value'):
                    st.success("✓ 이미지 교체 예정")

        else:
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border:1.5px dashed rgba(255,255,255,0.15);'
                'border-radius:8px;padding:20px;text-align:center;color:#888;">'
                '오른쪽에서 <b style="color:#C8A876">여기 편집 →</b> 버튼을 클릭하면<br>'
                '입력칸이 여기에 표시됩니다</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # 완료 현황
        txt_done = sum(1 for l in txt_layers if inputs.get(l['idx'],{}).get('value'))
        img_done = sum(1 for l in img_layers if inputs.get(l['idx'],{}).get('value'))
        st.markdown(
            f"**입력 현황** "
            f"<span style='color:#C8A876'>✏️ {txt_done}/{len(txt_layers)}</span> "
            f"<span style='color:#78a8f0;margin-left:6px'>🖼️ {img_done}/{len(img_layers)}</span>",
            unsafe_allow_html=True,
        )

        # 레이어 전체 목록 (빠른 이동용)
        with st.expander("전체 레이어 목록 (빠른 선택)", expanded=False):
            if txt_layers:
                st.markdown('<div style="color:#C8A876;font-size:11px;font-weight:700;margin-bottom:3px">✏️ 텍스트</div>', unsafe_allow_html=True)
                for l in txt_layers:
                    is_a  = (l['idx'] == active)
                    has_v = bool(inputs.get(l['idx'],{}).get('value'))
                    s     = "✅" if has_v else ("▶" if is_a else "○")
                    if st.button(f"{s} {l['name'][:30]}", key=f"pu_list_t_{l['idx']}",
                                 use_container_width=True,
                                 type="primary" if is_a else "secondary"):
                        st.session_state.pu_active = l['idx']; st.rerun()
            if img_layers:
                st.markdown('<div style="color:#78a8f0;font-size:11px;font-weight:700;margin:8px 0 3px">🖼️ 이미지</div>', unsafe_allow_html=True)
                for l in img_layers:
                    is_a  = (l['idx'] == active)
                    has_v = bool(inputs.get(l['idx'],{}).get('value'))
                    s     = "✅" if has_v else ("▶" if is_a else "○")
                    if st.button(f"{s} {l['name'][:20]} ({l['w']}×{l['h']})", key=f"pu_list_i_{l['idx']}",
                                 use_container_width=True,
                                 type="primary" if is_a else "secondary"):
                        st.session_state.pu_active = l['idx']; st.rerun()

    # ── 오른쪽: 이미지 구간 + 편집 버튼
    with col_right:
        st.markdown("### 미리보기 — 위치별 편집")
        st.caption("각 레이어 위치 이미지 옆 **여기 편집 →** 클릭 → 왼쪽 입력칸 활성화")
        st.caption("🟡 텍스트  🔵 이미지  🟢 입력완료  ★ 선택중")

        if st.session_state.pu_prev and editable_layers:
            slice_and_display(
                st.session_state.pu_prev,
                editable_layers, active, inputs, W, H,
                display_w=440,
            )
        else:
            st.info("미리보기를 불러오지 못했습니다")

    st.divider()

    # ── 출력
    st.markdown('<div class="step-header">출력 · PSD 스크립트 + JPG 저장</div>', unsafe_allow_html=True)

    n_txt = sum(1 for l in txt_layers if inputs.get(l['idx'],{}).get('value'))
    n_img = sum(1 for l in img_layers if inputs.get(l['idx'],{}).get('value'))

    if n_txt + n_img == 0:
        st.warning("교체할 내용을 먼저 입력하세요")
    else:
        st.success(f"✏️ 텍스트 {n_txt}개 · 🖼️ 이미지 {n_img}개 교체 준비 완료")
        if st.button("⚙️ PSD 스크립트 + JPG 생성", use_container_width=True, type="primary", key="pu_save"):
            with st.spinner("생성 중..."):
                try:
                    txt_rep = {idx: v['value'] for idx,v in inputs.items()
                               if v.get('type')=='text' and v.get('value')}
                    img_rep = {idx: v['value'] for idx,v in inputs.items()
                               if v.get('type')=='image' and v.get('value')}
                    jsx = build_psd_edit_jsx(
                        psd_filename=f"{meta['name']}.psd",
                        psd_info=info,
                        text_replacements=txt_rep,
                        image_replacements=img_rep,
                    )
                    safe = meta['name'].replace(' ','_')[:30]
                    now  = datetime.now().strftime('%Y%m%d_%H%M')
                    zbuf = io.BytesIO()
                    with zipfile.ZipFile(zbuf,'w',zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{safe}_{now}.jsx", jsx.encode('utf-8'))
                        if st.session_state.pu_prev:
                            zf.writestr(f"{safe}_{now}_preview.jpg", st.session_state.pu_prev)
                        zf.writestr("README.txt",
                            f"미샵 템플릿 OS | {meta['name']} | {now}\n"
                            f"교체: 텍스트 {len(txt_rep)} 이미지 {len(img_rep)}\n"
                            f"포토샵 File>Scripts>Browse에서 jsx 실행 (CS5~CC)".encode('utf-8'))
                    st.download_button(
                        "⬇️ ZIP 다운로드 (JSX + 미리보기JPG)",
                        data=zbuf.getvalue(),
                        file_name=f"misharp_psd_{safe}_{now}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 완료! 포토샵에서 .jsx 실행 → PSD 자동 저장")
                    st.caption("📌 File > Scripts > Browse → .jsx 선택 (CS5~CC 지원)")
                except Exception as e:
                    st.error(f"오류: {e}")
