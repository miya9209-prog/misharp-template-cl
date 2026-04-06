"""
page_psd_use.py — PSD 템플릿 활용
- 텍스트/이미지 레이어 모두 목록에 표시
- 선택한 레이어의 입력칸이 상단에 크게 표시
- 오른쪽 미리보기 클릭으로 레이어 선택
"""
import streamlit as st
import streamlit.components.v1 as components
import io, sys, os, base64, json, zipfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
from utils.psd_parser import psd_to_preview_jpg
from utils.psd_jsx_builder import build_psd_edit_jsx


def make_viewer_html(prev_bytes, editable_layers, active_idx, inputs, W_orig, H_orig, height=660):
    """인터랙티브 미리보기 HTML — 클릭 시 레이어 활성화"""
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx = pW / W_orig
    sy = pH / H_orig

    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)

    click_zones = []
    for l in editable_layers:
        t, le, b, r = l['rect']
        x1, y1 = int(le*sx), int(t*sy)
        x2, y2 = int(r*sx),  int(b*sy)
        if x2-x1 < 4 or y2-y1 < 4:
            continue

        is_active = (l['idx'] == active_idx)
        has_input = bool(inputs.get(l['idx'], {}).get('value'))
        ltype = l['type']

        if has_input:
            fill, outline, w = (50,220,80,55), (50,220,80,220), 2
        elif is_active:
            fill    = (255,200,0,80)  if ltype=='text' else (100,160,255,80)
            outline = (255,200,0,255) if ltype=='text' else (100,160,255,255)
            w = 4
        else:
            fill    = (255,200,0,18)  if ltype=='text' else (100,160,255,15)
            outline = (255,200,0,110) if ltype=='text' else (100,160,255,80)
            w = 1

        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=w)

        if is_active:
            lh = min(28, y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,190))
            drw.text((x1+5, y1+5), f"{'✏' if ltype=='text' else '🖼'} {l['name'][:26]}", fill=(255,255,255,255))

        click_zones.append({
            "idx": l['idx'], "name": l['name'], "type": ltype,
            "px": [x1, y1, x2, y2],
        })

    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, "JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    zones_js = json.dumps(click_zones)

    return f"""<!DOCTYPE html><html><head><style>
body{{margin:0;background:#0a0a0f;}}
.wrap{{width:100%;height:{height}px;overflow-y:scroll;overflow-x:hidden;
       background:#111;border:1px solid rgba(255,255,255,0.12);
       border-radius:8px;cursor:crosshair;}}
img{{width:100%;display:block;}}
.hint{{color:#888;font-size:11px;text-align:center;padding:4px;
       font-family:sans-serif;background:#0a0a0f;}}
</style></head><body>
<div class="wrap" id="v">
  <img src="data:image/jpeg;base64,{b64}" id="img" onclick="onClick(event)"/>
</div>
<div class="hint">↕ 스크롤 | 클릭 → 레이어 선택 &nbsp;|&nbsp; 🟡 텍스트 &nbsp;🔵 이미지 &nbsp;🟢 입력완료</div>
<script>
var zones={zones_js};
var imgEl=document.getElementById('img');
function onClick(e){{
  var rect=imgEl.getBoundingClientRect();
  var sc=document.getElementById('v').scrollTop;
  var px=(e.clientX-rect.left)*(imgEl.naturalWidth/imgEl.offsetWidth);
  var py=(e.clientY-rect.top+sc)*(imgEl.naturalWidth/imgEl.offsetWidth);
  for(var i=zones.length-1;i>=0;i--){{
    var z=zones[i];
    if(px>=z.px[0]&&px<=z.px[2]&&py>=z.px[1]&&py<=z.px[3]){{
      var url=new URL(window.location.href,window.parent.location.href);
      url.searchParams.set('pu_active',z.idx);
      window.parent.location.href=url.toString();
      return;
    }}
  }}
}}
</script>
</body></html>"""


def render():
    st.markdown('<div class="section-title">④ PSD 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 PSD 템플릿을 불러와 텍스트·이미지를 교체하고 새 PSD로 저장하세요</div>', unsafe_allow_html=True)

    for k, v in [("pu_selected",None),("pu_inputs",{}),("pu_active",None),("pu_prev",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # URL 파라미터 수신 (미리보기 클릭)
    q = st.query_params.get("pu_active")
    if q and str(q).isdigit():
        st.session_state.pu_active = int(q)
        st.query_params.clear()

    # PSD 템플릿만 필터
    all_tpl = {k: v for k, v in load_all().items() if v.get("template_type") == "psd"}

    if not all_tpl:
        st.info("저장된 PSD 템플릿이 없습니다. ③ PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택 화면
    if not st.session_state.pu_selected:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row_start in range(0, len(tpl_list), 3):
            cols = st.columns(3, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row_start:row_start+3]):
                with cols[ci]:
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1)">',
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"**{meta['name']}**")
                    st.caption(f"PSD | {meta['canvas_size'][0]}×{meta['canvas_size'][1]}px | {meta['created_at'][:10]}")
                    if meta.get("description"):
                        st.caption(meta["description"])
                    if st.button("이 템플릿 사용 →", key=f"psel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.pu_selected = tid
                        st.session_state.pu_inputs   = {}
                        st.session_state.pu_active   = None
                        st.session_state.pu_prev     = None
                        st.rerun()
        return

    # ── 작업 화면
    tid       = st.session_state.pu_selected
    meta      = load_one(tid)
    info      = load_psd_info(tid)
    psd_bytes = get_psd_bytes(tid)

    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_selected = None
        return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_idxs = set(int(k) for k, v in info.get('editable_layers', {}).items() if v)
    editable_layers = [l for l in layers
                       if l['idx'] in editable_idxs and l['w'] > 0 and l['h'] > 0]

    # 텍스트 / 이미지 분리
    txt_layers = [l for l in editable_layers if l['type'] == 'text']
    img_layers = [l for l in editable_layers if l['type'] == 'pixel']

    # 병합 미리보기
    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try:
                st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except Exception:
                st.session_state.pu_prev = b""

    # 템플릿 정보 바
    st.markdown(f"""<div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {meta['name']}</strong>
        <span style="color:#A0A0A0;font-size:12px;margin-left:12px">
        PSD | {W}×{H}px | ✏️ 텍스트 {len(txt_layers)}개 · 🖼️ 이미지 {len(img_layers)}개
        </span>
    </div>""", unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="pu_back"):
        st.session_state.pu_selected = None
        st.rerun()

    st.divider()

    inputs       = st.session_state.pu_inputs
    active       = st.session_state.pu_active
    active_layer = next((l for l in layers if l['idx'] == active), None)

    col_left, col_right = st.columns([1, 1], gap="large")

    # ══════════════════════════════════════════
    # 왼쪽 패널
    # ══════════════════════════════════════════
    with col_left:

        # ── 활성 레이어 입력칸 (상단 고정)
        if active_layer:
            ltype = active_layer['type']
            lname = active_layer['name']
            t_col = "#C8A876" if ltype == 'text' else "#78a8f0"
            bg_col = "rgba(200,168,118,0.10)" if ltype == 'text' else "rgba(100,160,230,0.08)"
            icon   = "✏️" if ltype == 'text' else "🖼️"

            st.markdown(f"""
            <div style="background:{bg_col};border:2px solid {t_col};
                        border-radius:10px;padding:12px 16px 4px 16px;margin-bottom:4px;">
              <div style="color:{t_col};font-weight:700;font-size:14px;">
                {icon} {lname}
                <span style="color:#888;font-size:11px;font-weight:400;margin-left:8px">
                  {active_layer['w']}×{active_layer['h']}px
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            inp = inputs.get(active_layer['idx'], {})

            if ltype == 'text':
                orig = active_layer.get('text', '').split('\n')[0][:60]
                if orig:
                    st.caption(f"원본: {orig}")
                new_txt = st.text_area(
                    "새 텍스트",
                    value=inp.get('value', ''),
                    height=90,
                    key=f"pu_txt_{active_layer['idx']}",
                    placeholder="교체할 텍스트 입력 (비우면 원본 유지)",
                )
                if new_txt.strip():
                    inputs[active_layer['idx']] = {'value': new_txt, 'type': 'text'}
                elif active_layer['idx'] in inputs:
                    del inputs[active_layer['idx']]
                st.session_state.pu_inputs = inputs

            else:  # pixel = 이미지
                st.caption(f"교체할 이미지를 업로드하세요 (권장: {active_layer['w']}×{active_layer['h']}px)")
                up = st.file_uploader(
                    "이미지 파일 선택 (JPG / PNG)",
                    type=["jpg", "jpeg", "png"],
                    key=f"pu_img_{active_layer['idx']}",
                )
                if up:
                    raw_img = up.read()
                    inputs[active_layer['idx']] = {'value': raw_img, 'type': 'image'}
                    st.session_state.pu_inputs  = inputs
                    th = Image.open(io.BytesIO(raw_img))
                    th.thumbnail((200, 200))
                    st.image(th, width=160, caption="업로드된 이미지")
                elif inp.get('value'):
                    st.success("✓ 이미지 교체 예정")

            st.markdown("---")

        else:
            st.info("👉 오른쪽 미리보기에서 레이어를 클릭하거나, 아래 목록에서 선택하세요")
            st.markdown("---")

        # ── 레이어 목록 (텍스트 + 이미지 구분하여 표시)
        txt_done = sum(1 for l in txt_layers if inputs.get(l['idx'], {}).get('value'))
        img_done = sum(1 for l in img_layers if inputs.get(l['idx'], {}).get('value'))
        st.markdown(
            f"**교체 대상 레이어** &nbsp;"
            f"<span style='color:#C8A876;font-size:12px'>✏️ {txt_done}/{len(txt_layers)}</span>"
            f" &nbsp; "
            f"<span style='color:#78a8f0;font-size:12px'>🖼️ {img_done}/{len(img_layers)}</span>",
            unsafe_allow_html=True,
        )

        # 텍스트 레이어
        if txt_layers:
            st.markdown("<div style='color:#C8A876;font-size:12px;font-weight:600;margin:6px 0 2px'>✏️ 텍스트 레이어</div>", unsafe_allow_html=True)
            for l in txt_layers:
                is_a   = (l['idx'] == active)
                has_v  = bool(inputs.get(l['idx'], {}).get('value'))
                status = "✅" if has_v else ("▶" if is_a else "○")
                btn_type = "primary" if is_a else "secondary"
                label = f"{status} ✏️  {l['name'][:28]}"
                if st.button(label, key=f"pu_sel_{l['idx']}", use_container_width=True, type=btn_type):
                    st.session_state.pu_active = l['idx']
                    st.rerun()

        # 이미지 레이어
        if img_layers:
            st.markdown("<div style='color:#78a8f0;font-size:12px;font-weight:600;margin:10px 0 2px'>🖼️ 이미지 레이어</div>", unsafe_allow_html=True)
            for l in img_layers:
                is_a   = (l['idx'] == active)
                has_v  = bool(inputs.get(l['idx'], {}).get('value'))
                status = "✅" if has_v else ("▶" if is_a else "○")
                btn_type = "primary" if is_a else "secondary"
                label = f"{status} 🖼️  {l['name'][:20]}  ({l['w']}×{l['h']})"
                if st.button(label, key=f"pu_sel_{l['idx']}", use_container_width=True, type=btn_type):
                    st.session_state.pu_active = l['idx']
                    st.rerun()

    # ══════════════════════════════════════════
    # 오른쪽 패널: 인터랙티브 미리보기
    # ══════════════════════════════════════════
    with col_right:
        st.markdown("### 미리보기")
        st.caption("레이어 박스 클릭 → 왼쪽 입력칸 활성화")

        if st.session_state.pu_prev:
            html = make_viewer_html(
                st.session_state.pu_prev,
                editable_layers, active, inputs, W, H, height=660,
            )
            components.html(html, height=700, scrolling=False)
        else:
            st.warning("미리보기를 불러오지 못했습니다")

        if active_layer:
            t_col = "#C8A876" if active_layer['type'] == 'text' else "#78a8f0"
            st.markdown(
                f'<div style="text-align:center;color:{t_col};font-size:12px;font-weight:600;margin-top:4px">'
                f'선택: {active_layer["name"]}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── 출력 섹션
    st.markdown('<div class="step-header">출력 · PSD 스크립트 + JPG 저장</div>', unsafe_allow_html=True)

    n_txt_inp = sum(1 for l in txt_layers if inputs.get(l['idx'], {}).get('value'))
    n_img_inp = sum(1 for l in img_layers if inputs.get(l['idx'], {}).get('value'))
    n_total   = n_txt_inp + n_img_inp

    if n_total == 0:
        st.warning("교체할 내용을 먼저 입력하세요 (텍스트 또는 이미지)")
    else:
        st.success(f"✏️ 텍스트 {n_txt_inp}개 · 🖼️ 이미지 {n_img_inp}개 교체 준비 완료")

        if st.button("⚙️ PSD 스크립트 + JPG 생성 후 다운로드", use_container_width=True, type="primary", key="pu_save"):
            with st.spinner("생성 중..."):
                try:
                    txt_rep = {idx: v['value'] for idx, v in inputs.items()
                               if v.get('type') == 'text' and v.get('value')}
                    img_rep = {idx: v['value'] for idx, v in inputs.items()
                               if v.get('type') == 'image' and v.get('value')}

                    jsx = build_psd_edit_jsx(
                        psd_filename=f"{meta['name']}.psd",
                        psd_info=info,
                        text_replacements=txt_rep,
                        image_replacements=img_rep,
                    )

                    safe = meta['name'].replace(' ', '_')[:30]
                    now  = datetime.now().strftime('%Y%m%d_%H%M')

                    zbuf = io.BytesIO()
                    with zipfile.ZipFile(zbuf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{safe}_{now}.jsx", jsx.encode('utf-8'))
                        if st.session_state.pu_prev:
                            zf.writestr(f"{safe}_{now}_preview.jpg", st.session_state.pu_prev)
                        readme = f"""미샵 템플릿 OS - PSD 출력 패키지
==========================================
템플릿: {meta['name']} | 생성일: {now}

포토샵 사용법
-----------
1. File > Scripts > Browse
2. {safe}_{now}.jsx 선택 실행
3. 원본 PSD 위치 지정 → 레이어 자동 교체
4. 완성 PSD가 원본 폴더에 저장됨 (CS5~CC 지원)

교체 내역: 텍스트 {len(txt_rep)}개 | 이미지 {len(img_rep)}개

made by MISHARP COMPANY, MIYAWA, 2026
"""
                        zf.writestr("README.txt", readme.encode('utf-8'))

                    st.download_button(
                        "⬇️ ZIP 다운로드 (JSX 스크립트 + 미리보기JPG)",
                        data=zbuf.getvalue(),
                        file_name=f"misharp_psd_{safe}_{now}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                    st.success("✅ 완료! 포토샵에서 .jsx 파일을 실행하면 PSD가 자동 저장됩니다")
                    st.caption("📌 File > Scripts > Browse → .jsx 파일 선택 (CS5~CC 전버전 지원)")

                except Exception as e:
                    st.error(f"오류: {e}")
