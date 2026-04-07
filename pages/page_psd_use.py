"""
page_psd_use.py — ③ 템플릿 불러오기
수정사항:
  - _make_overlay 캐싱 → 로딩 속도 개선
  - 이미지 레이어 목록에 썸네일 표시 (세로 약 60px)
  - 이미지 레이어 선택 시 우측 오버레이에서 해당 위치 강조
  - 좌측 입력부 좌측 정렬
  - col_right 내 st.button/st.columns 없음 유지
"""
import streamlit as st
import io, sys, os, base64, zipfile
from datetime import datetime
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import (
    load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
)
from utils.psd_parser import psd_to_preview_jpg, parse_psd
from utils.psd_jsx_builder import build_psd_edit_jsx


@st.cache_data(show_spinner=False)
def _make_overlay_cached(prev_bytes: bytes, editable_json: str,
                          active_idx, inp_json: str,
                          W_orig: int, H_orig: int) -> str:
    """
    오버레이 이미지 생성 - 캐싱 적용으로 속도 개선.
    editable_json, inp_json은 JSON 직렬화된 문자열로 캐시 키 사용.
    """
    import json
    editable = json.loads(editable_json)
    inputs   = json.loads(inp_json)

    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0, 0, 0, 0))
    drw = ImageDraw.Draw(ov)

    for l in editable:
        t, le, b, r = l['rect']
        x1, y1 = int(le*sx), int(t*sy)
        x2, y2 = int(r*sx),  int(b*sy)
        if x2-x1 < 3 or y2-y1 < 3:
            continue
        lt    = l['type']
        is_a  = (l['idx'] == active_idx)
        has_v = str(l['idx']) in inputs and bool(inputs[str(l['idx'])].get('has_value'))

        if has_v:
            fill, outline, lw = (50,220,80,55), (50,220,80,220), 3
        elif is_a:
            fill    = (255,200,0,90)  if lt=='text' else (100,160,255,90)
            outline = (255,200,0,255) if lt=='text' else (100,160,255,255)
            lw = 5
        else:
            fill    = (255,200,0,18)  if lt=='text' else (100,160,255,13)
            outline = (255,200,0,110) if lt=='text' else (100,160,255,80)
            lw = 1

        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=lw)

        if is_a:
            lh = min(30, y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
            drw.text((x1+5, y1+6),
                     f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}",
                     fill=(255,255,255))
        elif has_v:
            drw.text((x1+4, y1+4), "✓", fill=(50,220,80,230))

    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


@st.cache_data(show_spinner=False)
def _extract_layer_thumb(psd_bytes: bytes, layer_idx: int,
                          rect: tuple, thumb_h: int = 60) -> str | None:
    """
    레이어 영역을 PSD 병합 이미지에서 정확히 잘라 썸네일로 반환.
    thumb_size × thumb_size 정사각형 박스에 cover 방식으로 맞춤.
    """
    try:
        import struct
        prev = psd_to_preview_jpg(psd_bytes, max_width=900)
        full = Image.open(io.BytesIO(prev)).convert("RGB")
        pW, pH = full.size

        t, le, b, r = rect
        W_orig = struct.unpack('>I', psd_bytes[18:22])[0]
        H_orig = struct.unpack('>I', psd_bytes[14:18])[0]

        sx, sy = pW / W_orig, pH / H_orig
        x1, y1 = max(0, int(le*sx)), max(0, int(t*sy))
        x2, y2 = min(pW, int(r*sx)),  min(pH, int(b*sy))

        if x2-x1 < 5 or y2-y1 < 5:
            return None

        crop = full.crop((x1, y1, x2, y2))
        cW, cH = crop.size

        # 정사각형(thumb_h) cover: 짧은 쪽이 thumb_h가 되도록 리사이즈 후 중앙 크롭
        scale = thumb_h / min(cW, cH)
        new_w = max(1, int(cW * scale))
        new_h = max(1, int(cH * scale))
        crop  = crop.resize((new_w, new_h), Image.LANCZOS)

        # 중앙 크롭
        cx, cy = new_w // 2, new_h // 2
        half   = thumb_h // 2
        left   = max(0, cx - half)
        top    = max(0, cy - half)
        crop   = crop.crop((left, top, left + thumb_h, top + thumb_h))

        buf = io.BytesIO()
        crop.save(buf, "JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def render():
    # 버튼 텍스트 좌측 정렬 강제 (인라인 스타일)
    st.markdown("""
<style>
div[data-testid="stButton"] button {
    text-align: left !important;
    justify-content: flex-start !important;
}
div[data-testid="stButton"] button > div {
    justify-content: flex-start !important;
    width: 100%;
}
div[data-testid="stButton"] button p {
    text-align: left !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">③ 템플릿 불러오기</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 템플릿을 불러와 텍스트·이미지를 교체하고 새 PSD로 저장하세요</div>', unsafe_allow_html=True)

    for k, v in [("pu_sel",None),("pu_inp",{}),("pu_act",None),("pu_prev",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    all_tpl = {}
    try:
        all_tpl = {k:v for k,v in load_all().items()
                   if isinstance(v, dict) and v.get("template_type")=="psd"}
    except Exception:
        pass

    if not all_tpl:
        st.info("PSD 템플릿이 없습니다. ① PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택
    if not st.session_state.pu_sel:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row in range(0, len(tpl_list), 4):
            cols = st.columns(4, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row:row+4]):
                with cols[ci]:
                    st.markdown(f"**{meta.get('name','')}**")
                    w, h = meta.get("canvas_size",[0,0])
                    st.caption(f"PSD · {w}×{h}px · {meta.get('created_at','')[:10]}")
                    if meta.get("description"):
                        st.caption(meta["description"])
                    if st.button("사용 →", key=f"tsel_{tid}",
                                 use_container_width=True, type="primary"):
                        st.session_state.pu_sel  = tid
                        st.session_state.pu_inp  = {}
                        st.session_state.pu_act  = None
                        st.session_state.pu_prev = None
                        st.rerun()
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<div style="width:100%;height:300px;background:#0d0d0d;'
                            f'border-radius:8px;margin-top:6px;overflow:hidden;'
                            f'border:1px solid rgba(255,255,255,0.1)">'
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;height:300px;object-fit:cover;'
                            f'object-position:top;display:block;"></div>',
                            unsafe_allow_html=True)
        return

    # ── 데이터 로드
    tid       = st.session_state.pu_sel
    meta      = load_one(tid)
    info      = load_psd_info(tid)
    psd_bytes = get_psd_bytes(tid)

    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_sel = None
        return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_idxs = set(int(k) for k,v in info.get('editable_layers',{}).items() if v)
    editable = sorted(
        [l for l in layers if l['idx'] in editable_idxs and l['w']>0 and l['h']>0],
        key=lambda l: l['rect'][0]
    )
    txt_lays = [l for l in editable if l['type']=='text']
    img_lays = [l for l in editable if l['type']=='pixel']

    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try:
                st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except Exception:
                st.session_state.pu_prev = b""

    inp       = st.session_state.pu_inp
    act       = st.session_state.pu_act
    act_layer = next((l for l in layers if l['idx']==act), None)

    # 상단
    st.info(f"📋 **{meta['name']}** | {W}×{H}px | ✏️ {len(txt_lays)}개 · 🖼️ {len(img_lays)}개")
    if st.button("← 다른 템플릿 선택", key="pu_back_btn"):
        st.session_state.pu_sel = None
        st.rerun()
    st.divider()

    # ══════════════════════════════════════════════
    # 2열: 왼쪽(입력+목록) | 오른쪽(이미지)
    # ══════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1], gap="large")

    # ── 왼쪽
    with col_left:
        # ══════════════════════════════════════════
        # 순서: 이미지 레이어 → 텍스트 레이어
        # 각 버튼 바로 아래 입력칸 (헤매지 않도록)
        # ══════════════════════════════════════════

        id_ = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))
        td  = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
        st.caption(f"✅ 완료  ▶ 선택중  ○ 미입력 | 🖼️ {id_}/{len(img_lays)}  ✏️ {td}/{len(txt_lays)}")

        # ── 🖼️ 이미지 레이어 먼저
        if img_lays:
            st.markdown(
                '<div style="color:#78a8f0;font-weight:700;font-size:13px;'
                'padding:6px 10px;background:rgba(100,160,230,0.08);'
                'border-radius:6px;margin-bottom:6px">🖼️ 이미지 레이어</div>',
                unsafe_allow_html=True,
            )
            for l in img_lays:
                is_a  = (l['idx'] == act)
                has_v = bool(inp.get(l['idx'],{}).get('value'))
                s     = "✅" if has_v else ("▶" if is_a else "○")
                bg    = "rgba(100,160,230,0.10)" if is_a else "rgba(255,255,255,0.02)"
                border= "2px solid #78a8f0" if is_a else "1px solid rgba(255,255,255,0.07)"

                # 썸네일 (작게, 카드 내)
                thumb_b64 = _extract_layer_thumb(
                    psd_bytes, l['idx'], tuple(l['rect']), thumb_h=48
                )
                th_html = (
                    f'<img src="data:image/jpeg;base64,{thumb_b64}" '
                    f'style="width:48px;height:48px;object-fit:cover;'
                    f'border-radius:4px;flex-shrink:0;margin-right:8px">'
                    if thumb_b64 else
                    f'<div style="width:48px;height:48px;background:rgba(255,255,255,0.05);'
                    f'border-radius:4px;flex-shrink:0;margin-right:8px;'
                    f'display:flex;align-items:center;justify-content:center;font-size:16px">🖼️</div>'
                )
                st.markdown(
                    f'<div style="background:{bg};border:{border};border-radius:8px;'
                    f'padding:6px 10px;margin-bottom:2px;display:flex;align-items:center">'
                    f'{th_html}'
                    f'<div style="flex:1;min-width:0">'
                    f'<div style="color:{"#78a8f0" if is_a else "#bbb"};font-size:12px;'
                    f'font-weight:{"700" if is_a else "400"};'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                    f'{s} {l["name"][:22]}</div>'
                    f'<div style="color:#666;font-size:10px">{l["w"]}×{l["h"]}px</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                # 선택 버튼
                if st.button(
                    "▶ 이미지 교체하기" if not is_a else "📂 이미지 파일 선택 ↓",
                    key=f"pib{l['idx']}",
                    use_container_width=True,
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pu_act = l['idx']
                    st.rerun()

                # 선택된 레이어 → 파일 업로더 바로 아래 표시
                if is_a:
                    cur = inp.get(l['idx'], {})
                    st.caption(f"권장: {l['w']}×{l['h']}px")
                    up = st.file_uploader(
                        "이미지 파일 선택 (JPG / PNG)",
                        type=["jpg","jpeg","png"],
                        key=f"pimg{l['idx']}",
                    )
                    if up:
                        raw_img = up.read()
                        inp[l['idx']] = {'value': raw_img, 'type': 'image'}
                        st.session_state.pu_inp = inp
                        th = Image.open(io.BytesIO(raw_img))
                        th.thumbnail((200, 100))
                        st.image(th, caption="교체할 이미지")
                    elif cur.get('value'):
                        st.success("✓ 이미지 교체 예정")
                    st.markdown("---")

        elif not img_lays:
            st.caption("이미지 레이어 없음 — ① PSD 생성에서 이미지 레이어 체크 후 재저장")

        # ── ✏️ 텍스트 레이어 (이미지 다음)
        if txt_lays:
            st.markdown(
                '<div style="color:#C8A876;font-weight:700;font-size:13px;'
                'padding:6px 10px;background:rgba(200,168,118,0.08);'
                'border-radius:6px;margin:8px 0 6px">✏️ 텍스트 레이어</div>',
                unsafe_allow_html=True,
            )
            for l in txt_lays:
                is_a  = (l['idx'] == act)
                has_v = bool(inp.get(l['idx'],{}).get('value'))
                s     = "✅" if has_v else ("▶" if is_a else "○")
                if st.button(
                    f"{s}  ✏️  {l['name'][:32]}",
                    key=f"ptb{l['idx']}",
                    use_container_width=True,
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pu_act = l['idx']
                    st.rerun()

                # 선택된 텍스트 레이어 → 입력칸 바로 아래
                if is_a:
                    cur = inp.get(l['idx'], {})
                    orig = l.get('text','').split('\n')[0][:60]
                    if orig:
                        st.caption(f"원본: {orig}")
                    new_txt = st.text_area(
                        "새 텍스트",
                        value=cur.get('value',''),
                        height=80,
                        key=f"ptxt{l['idx']}",
                        placeholder="교체할 텍스트 (비우면 원본 유지)",
                    )
                    if new_txt.strip():
                        inp[l['idx']] = {'value': new_txt, 'type': 'text'}
                    elif l['idx'] in inp:
                        del inp[l['idx']]
                    st.session_state.pu_inp = inp
                    st.markdown("---")


    # ── 오른쪽: 이미지만 (st.button/st.columns 없음)
    with col_right:
        st.write("**PSD 미리보기**")
        st.caption("🟡 텍스트  🔵 이미지  🟢 입력완료  ★ 선택중 | ↕ 스크롤")

        if st.session_state.pu_prev:
            import json
            # 캐시용 직렬화 (value는 제외, 유무만)
            editable_json = json.dumps([
                {'idx': l['idx'], 'type': l['type'],
                 'rect': list(l['rect']), 'name': l['name'],
                 'w': l['w'], 'h': l['h']}
                for l in editable
            ])
            inp_json = json.dumps({
                str(idx): {'has_value': bool(v.get('value'))}
                for idx, v in inp.items()
            })

            b64 = _make_overlay_cached(
                st.session_state.pu_prev,
                editable_json, act, inp_json, W, H,
            )
            st.markdown(f"""
<div style="height:700px;overflow-y:scroll;overflow-x:hidden;
            border:1px solid rgba(255,255,255,0.12);border-radius:8px;
            background:#111;">
  <img src="data:image/jpeg;base64,{b64}" style="width:100%;display:block;">
</div>
<div style="color:#888;font-size:11px;text-align:center;margin-top:4px">
  ↕ 스크롤 전체 확인 | {W}×{H}px
</div>""", unsafe_allow_html=True)

        if act_layer:
            t_col = "#C8A876" if act_layer['type']=='text' else "#78a8f0"
            st.markdown(
                f'<div style="color:{t_col};font-weight:700;margin-top:6px;'
                f'padding:6px;background:rgba(255,255,255,0.04);'
                f'border-radius:6px;text-align:center">'
                f'선택: {act_layer["name"]}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── 출력
    st.markdown('<div class="step-header">출력 · PSD 스크립트 생성</div>', unsafe_allow_html=True)
    n_t = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
    n_i = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))

    if n_t + n_i == 0:
        st.warning("교체할 내용을 먼저 입력하세요")
    else:
        st.success(f"✏️ 텍스트 {n_t}개 · 🖼️ 이미지 {n_i}개 교체 준비 완료")
        if st.button("⚙️ PSD 스크립트 + 미리보기JPG 생성",
                     use_container_width=True, type="primary", key="pu_gen_btn"):
            with st.spinner("생성 중..."):
                try:
                    txt_rep = {idx: v['value'] for idx,v in inp.items()
                               if v.get('type')=='text' and v.get('value')}
                    img_rep = {idx: v['value'] for idx,v in inp.items()
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
                            zf.writestr(f"{safe}_{now}_preview.jpg",
                                        st.session_state.pu_prev)
                        zf.writestr("README.txt",
                            (f"미샵 템플릿 OS | {meta['name']} | {now}\n"
                             f"교체: 텍스트 {len(txt_rep)}개 이미지 {len(img_rep)}개\n"
                             "포토샵 File>Scripts>Browse에서 jsx 실행 (CS5~CC)")
                            .encode('utf-8'))
                    st.download_button(
                        "⬇️ ZIP 다운로드 (JSX + 미리보기JPG)",
                        data=zbuf.getvalue(),
                        file_name=f"misharp_{safe}_{now}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 완료!")
                    st.caption("File > Scripts > Browse → .jsx 선택 (CS5~CC 지원)")
                except Exception as e:
                    st.error(f"오류: {e}")
