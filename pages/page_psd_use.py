"""
page_psd_use.py
규칙:
  1. col_right 안에 st.button / st.columns 절대 없음
  2. st.markdown으로 여는 <div>는 반드시 같은 호출 안에서 닫음
  3. 버튼 key는 모두 명시적으로 지정
"""
import streamlit as st
import io, sys, os, base64, zipfile
from datetime import datetime
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import (
    load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
)
from utils.psd_parser import psd_to_preview_jpg
from utils.psd_jsx_builder import build_psd_edit_jsx


def _overlay_b64(prev_bytes, editable_layers, active_idx, inputs, W_orig, H_orig):
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig
    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1,y1,x2,y2 = int(le*sx),int(t*sy),int(r*sx),int(b*sy)
        if x2-x1 < 3 or y2-y1 < 3:
            continue
        lt   = l['type']
        is_a = (l['idx'] == active_idx)
        has_v= bool(inputs.get(l['idx'],{}).get('value'))
        if has_v:
            fill,outline,lw = (50,220,80,55),(50,220,80,230),3
        elif is_a:
            fill    = (255,200,0,90) if lt=='text' else (100,160,255,90)
            outline = (255,200,0,255) if lt=='text' else (100,160,255,255)
            lw = 5
        else:
            fill    = (255,200,0,20) if lt=='text' else (100,160,255,15)
            outline = (255,200,0,120) if lt=='text' else (100,160,255,90)
            lw = 1
        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=lw)
        if is_a:
            lh = min(30, y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,200))
            drw.text((x1+5,y1+6),
                     f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}",
                     fill=(255,255,255))
        elif has_v:
            drw.text((x1+4,y1+4), "✓", fill=(50,220,80,230))
    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def render():
    st.markdown('<div class="section-title">③ 템플릿 불러오기</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 템플릿을 불러와 텍스트·이미지를 교체하고 새 PSD로 저장하세요</div>',
                unsafe_allow_html=True)

    # ── 세션 초기화 (key 없을 때만)
    for k, v in [("pu_sel",None),("pu_inp",{}),("pu_act",None),("pu_prev",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    all_tpl = {k:v for k,v in load_all().items() if v.get("template_type")=="psd"}
    if not all_tpl:
        st.info("PSD 템플릿이 없습니다. ① PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택 화면
    if not st.session_state.pu_sel:
        st.markdown("### PSD 템플릿 선택")
        for row in range(0, len(all_tpl), 4):
            cols = st.columns(4, gap="medium")
            for ci, (tid, meta) in enumerate(list(all_tpl.items())[row:row+4]):
                with cols[ci]:
                    st.markdown(f"**{meta['name']}**")
                    w,h = meta.get("canvas_size",[0,0])
                    st.caption(f"PSD · {w}×{h}px · {meta['created_at'][:10]}")
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
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;max-height:150px;object-fit:cover;'
                            f'object-position:top;border-radius:6px;margin-top:4px">',
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

    inp = st.session_state.pu_inp
    act = st.session_state.pu_act
    act_layer = next((l for l in layers if l['idx']==act), None)

    # 상단 바
    st.info(f"📋 **{meta['name']}** | PSD {W}×{H}px | ✏️ {len(txt_lays)} · 🖼️ {len(img_lays)}")
    if st.button("← 다른 템플릿 선택", key="pu_back_btn"):
        st.session_state.pu_sel = None
        st.rerun()
    st.divider()

    # ══════════════════════════════════════════════════════════
    # 2열: col_left(입력+버튼), col_right(이미지만)
    # ══════════════════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1], gap="large")

    # ─── 왼쪽 ───────────────────────────────────────────────
    with col_left:
        st.markdown("### 입력")

        # 활성 레이어 입력칸
        if act_layer:
            lt   = act_layer['type']
            t_col= "#C8A876" if lt=='text' else "#78a8f0"
            icon = "✏️" if lt=='text' else "🖼️"
            cur_inp = inp.get(act_layer['idx'], {})

            # 타이틀 (div 열고 닫기 한 번에)
            st.markdown(
                f'<p style="background:{"rgba(200,168,118,0.10)" if lt=="text" else "rgba(100,160,230,0.08)"};'
                f'border:2px solid {t_col};border-radius:8px;padding:8px 12px;margin:0 0 8px 0;'
                f'color:{t_col};font-weight:700;font-size:14px">'
                f'{icon} {act_layer["name"]}'
                f'<span style="color:#888;font-size:11px;font-weight:400;margin-left:8px">'
                f'{act_layer["w"]}×{act_layer["h"]}px</span></p>',
                unsafe_allow_html=True,
            )

            if lt == 'text':
                orig = act_layer.get('text','').split('\n')[0][:60]
                if orig:
                    st.caption(f"원본: {orig}")
                new_txt = st.text_area(
                    "새 텍스트",
                    value=cur_inp.get('value',''),
                    height=90,
                    key=f"ptxt{act_layer['idx']}",
                    placeholder="교체할 텍스트 (비우면 원본 유지)",
                )
                if new_txt.strip():
                    inp[act_layer['idx']] = {'value':new_txt, 'type':'text'}
                elif act_layer['idx'] in inp:
                    del inp[act_layer['idx']]
                st.session_state.pu_inp = inp
            else:
                st.caption(f"권장 크기: {act_layer['w']}×{act_layer['h']}px")
                up = st.file_uploader(
                    "교체할 이미지 (JPG / PNG)",
                    type=["jpg","jpeg","png"],
                    key=f"pimg{act_layer['idx']}",
                )
                if up:
                    raw_img = up.read()
                    inp[act_layer['idx']] = {'value':raw_img, 'type':'image'}
                    st.session_state.pu_inp = inp
                    th = Image.open(io.BytesIO(raw_img))
                    th.thumbnail((200,160))
                    st.image(th, width=160, caption="선택된 이미지")
                elif cur_inp.get('value'):
                    st.success("✓ 이미지 교체 예정")
        else:
            st.info("아래 레이어 버튼을 클릭하면 입력칸이 표시됩니다")

        st.divider()

        # 레이어 버튼 목록
        td = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
        id_ = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))
        st.write(f"**레이어 목록** | ✏️ {td}/{len(txt_lays)}  🖼️ {id_}/{len(img_lays)}")
        st.caption("버튼 클릭 → 위 입력칸 활성화 | ✅완료 ▶선택중 ○미입력")

        if txt_lays:
            st.write("✏️ **텍스트 레이어**")
            for l in txt_lays:
                is_a = (l['idx']==act)
                has_v= bool(inp.get(l['idx'],{}).get('value'))
                s    = "✅" if has_v else ("▶" if is_a else "○")
                if st.button(
                    f"{s}  ✏️  {l['name'][:32]}",
                    key=f"ptb{l['idx']}",
                    use_container_width=True,
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pu_act = l['idx']
                    st.rerun()

        if img_lays:
            st.write("🖼️ **이미지 레이어**")
            for l in img_lays:
                is_a = (l['idx']==act)
                has_v= bool(inp.get(l['idx'],{}).get('value'))
                s    = "✅" if has_v else ("▶" if is_a else "○")
                if st.button(
                    f"{s}  🖼️  {l['name'][:22]}  ({l['w']}×{l['h']})",
                    key=f"pib{l['idx']}",
                    use_container_width=True,
                    type="primary" if is_a else "secondary",
                ):
                    st.session_state.pu_act = l['idx']
                    st.rerun()
        elif not img_lays:
            st.caption("이미지 레이어 없음. ① PSD 생성에서 이미지 레이어 체크 후 재저장 필요.")

    # ─── 오른쪽: 이미지만 (st.button/st.columns 없음) ────────
    with col_right:
        st.markdown("**선택된 레이어**")
        if act_layer:
            t_col = "#C8A876" if act_layer['type']=='text' else "#78a8f0"
            icon  = "✏️" if act_layer['type']=='text' else "🖼️"
            st.markdown(
                f'<p style="background:{"rgba(200,168,118,0.1)" if act_layer[chr(39)+"type"+chr(39)]=="text" else "rgba(100,160,230,0.08)"};'
                f'border:2px solid {t_col};border-radius:8px;padding:12px 16px;'
                f'color:{t_col};font-weight:700;font-size:14px;margin-bottom:8px">'
                f'{icon} {act_layer["name"]}<br>'
                f'<span style="color:#888;font-size:11px;font-weight:400">'
                f'{act_layer["w"]}×{act_layer["h"]}px</span></p>',
                unsafe_allow_html=True,
            )
        else:
            st.info("왼쪽 레이어 버튼을 클릭하면 정보가 표시됩니다")

        td = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
        id_ = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))
        st.write(f"**입력 현황** | ✏️ {td}/{len(txt_lays)}  🖼️ {id_}/{len(img_lays)}")

    # ── columns 밖: 전체 PSD 이미지 (높이 제한 없음)
    st.divider()
    st.markdown("**PSD 미리보기** — 🟡 텍스트  🔵 이미지  🟢 입력완료  ★ 선택")
    if st.session_state.pu_prev:
        b64 = _overlay_b64(
            st.session_state.pu_prev,
            editable, act, inp, W, H,
        )
        st.markdown(
            f'<img src="data:image/jpeg;base64,{b64}" '
            f'style="width:100%;display:block;border-radius:8px;'
            f'border:1px solid rgba(255,255,255,0.12);">',
            unsafe_allow_html=True,
        )
        st.caption(f"{W}×{H}px 전체 이미지 | 페이지 스크롤로 확인")

    st.divider()

    # ── 출력
    st.markdown('<div class="step-header">출력</div>', unsafe_allow_html=True)
    n_t = sum(1 for l in txt_lays if inp.get(l['idx'],{}).get('value'))
    n_i = sum(1 for l in img_lays if inp.get(l['idx'],{}).get('value'))

    if n_t + n_i == 0:
        st.warning("교체할 내용을 먼저 입력하세요")
    else:
        st.success(f"✏️ 텍스트 {n_t}개 · 🖼️ 이미지 {n_i}개 교체 준비 완료")
        if st.button("⚙️ PSD 스크립트 + JPG 생성",
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
                    st.caption("포토샵 File > Scripts > Browse → .jsx 선택 (CS5~CC)")
                except Exception as e:
                    st.error(f"오류: {e}")
