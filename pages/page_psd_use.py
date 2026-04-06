"""
page_psd_use.py — PSD 템플릿 활용
"""
import streamlit as st
import streamlit.components.v1 as components
import io, sys, os, base64, json, zipfile
from datetime import datetime
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_thumb_b64, load_psd_info, get_psd_bytes
from utils.psd_parser import psd_to_preview_jpg
from utils.psd_jsx_builder import build_psd_edit_jsx


def _viewer_html(prev_bytes, editable_layers, active_idx, inputs, W_orig, H_orig, height=640):
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx, sy = pW / W_orig, pH / H_orig

    ov  = Image.new("RGBA", (pW, pH), (0,0,0,0))
    drw = ImageDraw.Draw(ov)
    zones = []

    for l in editable_layers:
        t,le,b,r = l['rect']
        x1,y1,x2,y2 = int(le*sx),int(t*sy),int(r*sx),int(b*sy)
        if x2-x1 < 4 or y2-y1 < 4: continue
        is_a  = (l['idx'] == active_idx)
        has_v = bool(inputs.get(l['idx'],{}).get('value'))
        lt    = l['type']
        if has_v:
            fill,outline,w = (50,220,80,55),(50,220,80,220),2
        elif is_a:
            fill    = (255,200,0,80)  if lt=='text' else (100,160,255,80)
            outline = (255,200,0,255) if lt=='text' else (100,160,255,255)
            w = 4
        else:
            fill    = (255,200,0,18)  if lt=='text' else (100,160,255,15)
            outline = (255,200,0,110) if lt=='text' else (100,160,255,80)
            w = 1
        drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=w)
        if is_a:
            lh = min(28,y2-y1)
            drw.rectangle([x1,y1,x2,y1+lh], fill=(0,0,0,190))
            drw.text((x1+5,y1+5), f"{'✏' if lt=='text' else '🖼'} {l['name'][:26]}", fill=(255,255,255,255))
        zones.append({"idx":l['idx'],"name":l['name'],"type":lt,"px":[x1,y1,x2,y2]})

    merged = Image.alpha_composite(img, ov).convert("RGB")
    buf = io.BytesIO(); merged.save(buf,"JPEG",quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    zjs = json.dumps(zones)

    return f"""<!DOCTYPE html><html><head><style>
body{{margin:0;background:#0a0a0f;}}
.w{{width:100%;height:{height}px;overflow-y:scroll;overflow-x:hidden;
    background:#111;border:1px solid rgba(255,255,255,0.12);border-radius:8px;cursor:crosshair;}}
img{{width:100%;display:block;}}
.h{{color:#888;font-size:11px;text-align:center;padding:4px;font-family:sans-serif;background:#0a0a0f;}}
</style></head><body>
<div class="w" id="v"><img src="data:image/jpeg;base64,{b64}" id="im" onclick="go(event)"/></div>
<div class="h">↕ 스크롤 | 클릭 → 레이어 선택 | 🟡 텍스트 🔵 이미지 🟢 입력완료</div>
<script>
var Z={zjs},im=document.getElementById('im');
function go(e){{
  var r=im.getBoundingClientRect(),sc=document.getElementById('v').scrollTop;
  var s=im.naturalWidth/im.offsetWidth;
  var px=(e.clientX-r.left)*s, py=(e.clientY-r.top+sc)*s;
  for(var i=Z.length-1;i>=0;i--){{
    var z=Z[i];
    if(px>=z.px[0]&&px<=z.px[2]&&py>=z.px[1]&&py<=z.px[3]){{
      var u=new URL(window.location.href,window.parent.location.href);
      u.searchParams.set('pu_active',z.idx);
      window.parent.location.href=u.toString(); return;
    }}
  }}
}}
</script></body></html>"""


def render():
    st.markdown('<div class="section-title">④ PSD 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 PSD 템플릿을 불러와 텍스트·이미지를 교체하고 새 PSD로 저장하세요</div>', unsafe_allow_html=True)

    for k,v in [("pu_selected",None),("pu_inputs",{}),("pu_active",None),("pu_prev",None)]:
        if k not in st.session_state: st.session_state[k] = v

    q = st.query_params.get("pu_active")
    if q and str(q).isdigit():
        st.session_state.pu_active = int(q); st.query_params.clear()

    all_tpl = {k:v for k,v in load_all().items() if v.get("template_type")=="psd"}
    if not all_tpl:
        st.info("저장된 PSD 템플릿이 없습니다. ③ PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택
    if not st.session_state.pu_selected:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row in range(0, len(tpl_list), 4):
            cols = st.columns(4, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row:row+4]):
                with cols[ci]:
                    # 이름 + 버튼 상단
                    st.markdown(f"**{meta['name']}**")
                    st.caption(f"PSD · {meta['canvas_size'][0]}×{meta['canvas_size'][1]}px · {meta['created_at'][:10]}")
                    if meta.get("description"): st.caption(meta["description"])
                    if st.button("사용 →", key=f"psel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.pu_selected = tid
                        st.session_state.pu_inputs = {}
                        st.session_state.pu_active = None
                        st.session_state.pu_prev = None
                        st.rerun()
                    # 썸네일 하단 (작게)
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}" '
                            f'style="width:100%;max-height:150px;object-fit:cover;'
                            f'object-position:top;border-radius:6px;'
                            f'border:1px solid rgba(255,255,255,0.08);margin-top:4px">',
                            unsafe_allow_html=True,
                        )
        return

    # ── 작업 화면
    tid = st.session_state.pu_selected
    meta = load_one(tid); info = load_psd_info(tid); psd_bytes = get_psd_bytes(tid)
    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_selected = None; return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_idxs = set(int(k) for k,v in info.get('editable_layers',{}).items() if v)
    editable_layers = [l for l in layers if l['idx'] in editable_idxs and l['w']>0 and l['h']>0]
    txt_layers = [l for l in editable_layers if l['type']=='text']
    img_layers = [l for l in editable_layers if l['type']=='pixel']

    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try: st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except: st.session_state.pu_prev = b""

    st.markdown(f"""<div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {meta['name']}</strong>
        <span style="color:#A0A0A0;font-size:12px;margin-left:12px">
        PSD | {W}×{H}px | ✏️ 텍스트 {len(txt_layers)}개 · 🖼️ 이미지 {len(img_layers)}개
        </span>
    </div>""", unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="pu_back"):
        st.session_state.pu_selected = None; st.rerun()
    st.divider()

    inputs = st.session_state.pu_inputs
    active = st.session_state.pu_active
    active_layer = next((l for l in layers if l['idx']==active), None)

    col_left, col_right = st.columns([1,1], gap="large")

    with col_left:
        st.markdown("### 레이어 교체 입력")
        st.caption("아래 목록 클릭 또는 오른쪽 미리보기 클릭 → 상단 입력칸 활성화")

        # ── 활성 레이어 입력칸
        if active_layer:
            lt    = active_layer['type']
            lname = active_layer['name']
            t_col = "#C8A876" if lt=='text' else "#78a8f0"
            bg    = "rgba(200,168,118,0.10)" if lt=='text' else "rgba(100,160,230,0.08)"
            icon  = "✏️" if lt=='text' else "🖼️"

            st.markdown(f"""
            <div style="background:{bg};border:2px solid {t_col};border-radius:10px;
                        padding:10px 14px 2px 14px;margin-bottom:4px;">
              <span style="color:{t_col};font-weight:700;font-size:14px">{icon} {lname}</span>
              <span style="color:#888;font-size:11px;margin-left:8px">{active_layer['w']}×{active_layer['h']}px</span>
            </div>
            """, unsafe_allow_html=True)

            inp = inputs.get(active_layer['idx'], {})

            if lt == 'text':
                orig = active_layer.get('text','').split('\n')[0][:60]
                if orig: st.caption(f"원본: {orig}")
                new_txt = st.text_area(
                    "새 텍스트", value=inp.get('value',''),
                    height=85, key=f"pu_txt_{active_layer['idx']}",
                    placeholder="교체할 텍스트 입력 (비우면 원본 유지)",
                )
                if new_txt.strip():
                    inputs[active_layer['idx']] = {'value': new_txt, 'type': 'text'}
                elif active_layer['idx'] in inputs:
                    del inputs[active_layer['idx']]
                st.session_state.pu_inputs = inputs

            else:  # 이미지
                st.caption(f"권장 크기: {active_layer['w']}×{active_layer['h']}px")
                up = st.file_uploader(
                    "교체할 이미지 파일 선택 (JPG / PNG)",
                    type=["jpg","jpeg","png"],
                    key=f"pu_img_{active_layer['idx']}",
                )
                if up:
                    raw_img = up.read()
                    inputs[active_layer['idx']] = {'value': raw_img, 'type': 'image'}
                    st.session_state.pu_inputs = inputs
                    th = Image.open(io.BytesIO(raw_img)); th.thumbnail((200,200))
                    st.image(th, width=160, caption="선택된 이미지")
                elif inp.get('value'):
                    st.success("✓ 이미지 교체 예정")

            st.markdown("---")
        else:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.03);border:1px dashed rgba(255,255,255,0.15);
                        border-radius:8px;padding:20px;text-align:center;color:#888;margin-bottom:12px">
                아래 목록 또는 오른쪽 미리보기에서 레이어를 선택하세요
            </div>
            """, unsafe_allow_html=True)

        # ── 레이어 목록
        txt_done = sum(1 for l in txt_layers if inputs.get(l['idx'],{}).get('value'))
        img_done = sum(1 for l in img_layers if inputs.get(l['idx'],{}).get('value'))
        st.markdown(
            f"**교체 대상 레이어 목록**"
            f"<span style='color:#C8A876;font-size:12px;margin-left:8px'>✏️ {txt_done}/{len(txt_layers)}</span>"
            f"<span style='color:#78a8f0;font-size:12px;margin-left:6px'>🖼️ {img_done}/{len(img_layers)}</span>",
            unsafe_allow_html=True,
        )

        # 텍스트 레이어 목록
        if txt_layers:
            st.markdown("<div style='color:#C8A876;font-size:12px;font-weight:600;margin:8px 0 4px'>✏️ 텍스트 레이어</div>", unsafe_allow_html=True)
            for l in txt_layers:
                is_a  = (l['idx'] == active)
                has_v = bool(inputs.get(l['idx'],{}).get('value'))
                status = "✅" if has_v else ("▶" if is_a else "○")
                if st.button(f"{status} ✏️  {l['name'][:30]}", key=f"pu_sel_{l['idx']}",
                             use_container_width=True,
                             type="primary" if is_a else "secondary"):
                    st.session_state.pu_active = l['idx']; st.rerun()

        # 이미지 레이어 목록
        if img_layers:
            st.markdown("<div style='color:#78a8f0;font-size:12px;font-weight:600;margin:12px 0 4px'>🖼️ 이미지 레이어</div>", unsafe_allow_html=True)
            for l in img_layers:
                is_a  = (l['idx'] == active)
                has_v = bool(inputs.get(l['idx'],{}).get('value'))
                status = "✅" if has_v else ("▶" if is_a else "○")
                size_label = f"({l['w']}×{l['h']})"
                if st.button(f"{status} 🖼️  {l['name'][:22]}  {size_label}", key=f"pu_sel_{l['idx']}",
                             use_container_width=True,
                             type="primary" if is_a else "secondary"):
                    st.session_state.pu_active = l['idx']; st.rerun()
        elif not img_layers:
            st.caption("※ 이미지 레이어가 교체 대상으로 지정되지 않았습니다. ③ PSD 템플릿 생성에서 다시 설정하세요.")

    with col_right:
        st.markdown("### 미리보기")
        st.caption("레이어 박스 클릭 → 왼쪽 입력칸 활성화")
        if st.session_state.pu_prev:
            html = _viewer_html(st.session_state.pu_prev, editable_layers,
                                active, inputs, W, H, height=640)
            components.html(html, height=680, scrolling=False)
        if active_layer:
            t_col = "#C8A876" if active_layer['type']=='text' else "#78a8f0"
            st.markdown(f'<div style="text-align:center;color:{t_col};font-size:12px;font-weight:600;margin-top:4px">선택: {active_layer["name"]}</div>', unsafe_allow_html=True)

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
                    txt_rep = {idx: v['value'] for idx,v in inputs.items() if v.get('type')=='text' and v.get('value')}
                    img_rep = {idx: v['value'] for idx,v in inputs.items() if v.get('type')=='image' and v.get('value')}
                    jsx = build_psd_edit_jsx(psd_filename=f"{meta['name']}.psd", psd_info=info,
                                            text_replacements=txt_rep, image_replacements=img_rep)
                    safe = meta['name'].replace(' ','_')[:30]
                    now  = datetime.now().strftime('%Y%m%d_%H%M')
                    zbuf = io.BytesIO()
                    with zipfile.ZipFile(zbuf,'w',zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{safe}_{now}.jsx", jsx.encode('utf-8'))
                        if st.session_state.pu_prev:
                            zf.writestr(f"{safe}_{now}_preview.jpg", st.session_state.pu_prev)
                        zf.writestr("README.txt", f"미샵 템플릿 OS\n템플릿: {meta['name']}\n생성: {now}\n교체: 텍스트 {len(txt_rep)} 이미지 {len(img_rep)}\n포토샵 File>Scripts>Browse에서 jsx 실행".encode('utf-8'))
                    st.download_button("⬇️ ZIP 다운로드 (JSX + 미리보기JPG)", data=zbuf.getvalue(),
                                       file_name=f"misharp_psd_{safe}_{now}.zip",
                                       mime="application/zip", use_container_width=True)
                    st.success("✅ 완료! 포토샵에서 .jsx 실행 → PSD 자동 저장")
                    st.caption("📌 File > Scripts > Browse → .jsx 선택 (CS5~CC 지원)")
                except Exception as e:
                    st.error(f"오류: {e}")
