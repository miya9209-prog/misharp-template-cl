"""
page_psd_use.py — PSD 템플릿 활용
템플릿 선택 → 오른쪽 미리보기에서 레이어 클릭
→ 왼쪽 활성 입력칸에 텍스트/이미지 입력
→ 새 PSD(JSX) + JPG 저장
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
from utils.composer import compose_preview


def make_interactive_viewer(prev_bytes, layers, active_idx, editable_idxs,
                             inputs, W_orig, H_orig, viewer_h=660):
    """
    오른쪽 인터랙티브 미리보기:
    - 각 레이어 박스 표시
    - 입력된 텍스트는 해당 위치에 실시간 오버레이
    - 클릭하면 해당 레이어 활성화 (URL param)
    """
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGBA")
    pW, pH = img.size
    sx = pW / W_orig; sy = pH / H_orig

    drw = ImageDraw.Draw(img)

    editable = [l for l in layers if l['idx'] in editable_idxs
                and l['w'] > 0 and l['h'] > 0]

    click_zones = []
    for l in editable:
        t,le,b,r = l['rect']
        x1,y1,x2,y2 = int(le*sx), int(t*sy), int(r*sx), int(b*sy)
        is_active = (l['idx'] == active_idx)
        inp = inputs.get(l['idx'], {})
        has_input = bool(inp.get('value'))
        ltype = l['type']

        if is_active:
            fill    = (255,200,0,80)   if ltype=='text' else (100,160,255,80)
            outline = (255,200,0,255)  if ltype=='text' else (100,160,255,255)
            width   = 4
        elif has_input:
            fill    = (50,200,50,50)
            outline = (50,200,50,180)
            width   = 2
        else:
            fill    = (255,200,0,18)   if ltype=='text' else (100,160,255,12)
            outline = (255,200,0,100)  if ltype=='text' else (100,160,255,70)
            width   = 1

        ov_layer = Image.new("RGBA", img.size, (0,0,0,0))
        ov_drw   = ImageDraw.Draw(ov_layer)
        ov_drw.rectangle([x1,y1,x2,y2], fill=fill, outline=outline, width=width)
        img = Image.alpha_composite(img, ov_layer)
        drw = ImageDraw.Draw(img)

        # 활성 레이어 라벨
        if is_active:
            label_h = min(30, y2-y1)
            drw.rectangle([x1,y1,x2,y1+label_h], fill=(0,0,0,200))
            drw.text((x1+6,y1+5), f"{'✏' if ltype=='text' else '🖼'} {l['name'][:28]}", fill=(255,255,255))

        # 입력된 텍스트 미리보기
        if has_input and ltype == 'text' and inp.get('value'):
            txt_preview = inp['value'][:20]
            drw.text((x1+4, y1+4), txt_preview, fill=(255,220,0,200))

        click_zones.append({
            "idx": l['idx'], "name": l['name'], "type": ltype,
            "px": [x1, y1, x2, y2],
        })

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    zones_js = json.dumps(click_zones)

    return f"""<!DOCTYPE html><html><head><style>
body{{margin:0;background:#0a0a0f;}}
.wrap{{width:100%;height:{viewer_h}px;overflow-y:scroll;overflow-x:hidden;
       background:#111;border:1px solid rgba(255,255,255,0.12);
       border-radius:8px;cursor:crosshair;}}
img{{width:100%;display:block;}}
.hint{{color:#888;font-size:11px;text-align:center;padding:4px;
       font-family:sans-serif;background:#0a0a0f;}}
</style></head><body>
<div class="wrap" id="v">
  <img src="data:image/jpeg;base64,{b64}" id="img" onclick="onClick(event)"/>
</div>
<div class="hint">↕ 스크롤 확인 | 레이어 박스 클릭 → 왼쪽 입력칸 활성화 | 🟡 텍스트 🔵 이미지 🟢 입력완료</div>
<script>
var zones={zones_js};
var imgEl=document.getElementById('img');
function onClick(e){{
  var rect=imgEl.getBoundingClientRect();
  var scTop=document.getElementById('v').scrollTop;
  var cx=e.clientX-rect.left;
  var cy=e.clientY-rect.top+scTop;
  var scale=imgEl.naturalWidth/imgEl.offsetWidth;
  var px=cx*scale, py=cy*scale;
  for(var i=0;i<zones.length;i++){{
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

    for k,v in [("pu_selected",None),("pu_inputs",{}),("pu_active",None),("pu_prev",None)]:
        if k not in st.session_state: st.session_state[k] = v

    # URL 파라미터 수신
    q = st.query_params.get("pu_active")
    if q and q.isdigit():
        st.session_state.pu_active = int(q)
        st.query_params.clear()

    # PSD 템플릿만 필터
    all_tpl = {k:v for k,v in load_all().items() if v.get("template_type")=="psd"}

    if not all_tpl:
        st.info("저장된 PSD 템플릿이 없습니다. ③ PSD 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    # ── 템플릿 선택
    if not st.session_state.pu_selected:
        st.markdown("### PSD 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row_start in range(0, len(tpl_list), 3):
            cols = st.columns(3, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row_start:row_start+3]):
                with cols[ci]:
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1)">', unsafe_allow_html=True)
                    st.markdown(f"**{meta['name']}**")
                    st.caption(f"PSD | {meta['canvas_size'][0]}×{meta['canvas_size'][1]}px | {meta['created_at'][:10]}")
                    if meta.get('description'): st.caption(meta['description'])
                    if st.button("이 템플릿 사용 →", key=f"psel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.pu_selected = tid
                        st.session_state.pu_inputs   = {}
                        st.session_state.pu_active   = None
                        st.session_state.pu_prev     = None
                        st.rerun()
        return

    # ── 작업 화면
    tid  = st.session_state.pu_selected
    meta = load_one(tid)
    info = load_psd_info(tid)
    psd_bytes = get_psd_bytes(tid)

    if not meta or not info or not psd_bytes:
        st.error("템플릿 데이터를 불러오지 못했습니다")
        st.session_state.pu_selected = None; return

    layers = info['layers']
    W, H   = info['width'], info['height']
    editable_idxs = set(
        int(k) for k,v in info.get('editable_layers',{}).items() if v
    )
    editable_layers = [l for l in layers if l['idx'] in editable_idxs
                       and l['w'] > 0 and l['h'] > 0]

    # PSD 병합 미리보기
    if st.session_state.pu_prev is None:
        with st.spinner("미리보기 로딩..."):
            try:
                st.session_state.pu_prev = psd_to_preview_jpg(psd_bytes, max_width=900)
            except Exception:
                st.session_state.pu_prev = b""

    st.markdown(f"""<div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {meta['name']}</strong><br>
        <span style="color:#A0A0A0;font-size:12px">PSD | {W}×{H}px | 교체 레이어 {len(editable_idxs)}개</span>
    </div>""", unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="pu_back"):
        st.session_state.pu_selected = None; st.rerun()

    st.divider()

    active     = st.session_state.pu_active
    active_layer = next((l for l in layers if l['idx']==active), None)
    inputs     = st.session_state.pu_inputs

    col_form, col_prev = st.columns([1,1], gap="large")

    # ══════════════════════════════════
    # 왼쪽: 입력 패널
    # ══════════════════════════════════
    with col_form:
        st.markdown("### 레이어 교체 입력")
        st.caption("오른쪽 미리보기에서 박스를 클릭하거나 아래 목록에서 선택 → 내용 입력")

        # 활성 레이어 강조 입력 박스
        if active_layer:
            ltype  = active_layer['type']
            lname  = active_layer['name']
            t_col  = "#C8A876" if ltype=='text' else "#78a8f0"
            inp    = inputs.get(active_layer['idx'], {})

            st.markdown(f"""
            <div style="background:{'rgba(200,168,118,0.12)' if ltype=='text' else 'rgba(100,160,230,0.1)'};
                        border:2px solid {t_col};border-radius:10px;padding:14px 16px;margin-bottom:12px">
              <div style="color:{t_col};font-weight:700;font-size:14px;margin-bottom:8px">
                {'✏️' if ltype=='text' else '🖼️'} {lname}
                <span style="color:#888;font-size:11px;font-weight:400;margin-left:8px">
                  {active_layer['w']}×{active_layer['h']}px
                </span>
              </div>
            """, unsafe_allow_html=True)

            if ltype == 'text':
                orig = active_layer.get('text','').split('\n')[0][:60]
                if orig: st.caption(f"원본: {orig}")
                new_txt = st.text_area("새 텍스트 입력", value=inp.get('value',''),
                                       height=100, key=f"pu_txt_{active_layer['idx']}",
                                       placeholder="원본을 교체할 텍스트를 입력하세요")
                if new_txt != inp.get('value',''):
                    inputs[active_layer['idx']] = {'value': new_txt, 'type': 'text'}
                    st.session_state.pu_inputs = inputs
            else:
                up = st.file_uploader(f"교체 이미지 (권장 {active_layer['w']}×{active_layer['h']}px)",
                                      type=["jpg","jpeg","png"],
                                      key=f"pu_img_{active_layer['idx']}")
                if up:
                    raw_img = up.read()
                    inputs[active_layer['idx']] = {'value': raw_img, 'type': 'image'}
                    st.session_state.pu_inputs  = inputs
                    th = Image.open(io.BytesIO(raw_img)); th.thumbnail((180,180))
                    st.image(th, width=140)
                elif inputs.get(active_layer['idx'],{}).get('value'):
                    st.success("✓ 이미지 교체 예정")

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # 전체 레이어 목록
        st.markdown("**교체 대상 레이어 전체 목록**")
        txt_done  = sum(1 for l in editable_layers if l['type']=='text'
                        and inputs.get(l['idx'],{}).get('value'))
        img_done  = sum(1 for l in editable_layers if l['type']=='pixel'
                        and inputs.get(l['idx'],{}).get('value'))
        txt_total = sum(1 for l in editable_layers if l['type']=='text')
        img_total = sum(1 for l in editable_layers if l['type']=='pixel')
        st.caption(f"✏️ 텍스트 {txt_done}/{txt_total} · 🖼️ 이미지 {img_done}/{img_total} 입력됨")

        for l in editable_layers:
            ltype = l['type']
            icon  = "✏️" if ltype=='text' else "🖼️"
            is_a  = (l['idx'] == active)
            has_v = bool(inputs.get(l['idx'],{}).get('value'))
            t_col = "#C8A876" if ltype=='text' else "#78a8f0"
            status_icon = "✅" if has_v else ("▶" if is_a else "○")
            border = f"2px solid {t_col}" if is_a else "1px solid rgba(255,255,255,0.07)"
            bg     = f"rgba({'200,168,118' if ltype=='text' else '100,160,230'},0.08)" if is_a else "rgba(255,255,255,0.02)"

            col_s, col_n = st.columns([1,8])
            with col_s:
                st.markdown(f'<div style="font-size:16px;padding-top:6px;text-align:center">{status_icon}</div>', unsafe_allow_html=True)
            with col_n:
                if st.button(f"{icon} {l['name'][:30]}", key=f"pu_sel_{l['idx']}",
                             use_container_width=True,
                             type="primary" if is_a else "secondary"):
                    st.session_state.pu_active = l['idx']; st.rerun()

    # ══════════════════════════════════
    # 오른쪽: 인터랙티브 미리보기
    # ══════════════════════════════════
    with col_prev:
        st.markdown("### 미리보기")
        st.caption("레이어 박스 클릭 → 왼쪽 입력칸 활성화")

        if st.session_state.pu_prev:
            html = make_interactive_viewer(
                st.session_state.pu_prev, editable_layers,
                active, editable_idxs, inputs, W, H, viewer_h=660
            )
            components.html(html, height=700, scrolling=False)

        if active_layer:
            t_col = "#C8A876" if active_layer['type']=='text' else "#78a8f0"
            st.markdown(f'<div style="text-align:center;color:{t_col};font-size:12px;font-weight:600">선택: {active_layer["name"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 출력
    st.markdown('<div class="step-header">STEP · 출력</div>', unsafe_allow_html=True)

    n_inputs = sum(1 for v in inputs.values() if v.get('value'))
    if n_inputs == 0:
        st.warning("교체할 내용을 먼저 입력해주세요")
    else:
        st.success(f"{n_inputs}개 레이어 교체 준비 완료")

        out_cols = st.columns(2, gap="medium")
        with out_cols[0]:
            if st.button("🖼️ JPG 미리보기 생성", use_container_width=True, key="pu_jpg"):
                # JPG 합성 미리보기 (PIL)
                with st.spinner("JPG 합성 중..."):
                    try:
                        # PSD 병합 이미지 + 텍스트 오버레이
                        base_img = Image.open(io.BytesIO(st.session_state.pu_prev)).convert("RGBA")
                        from PIL import ImageFont
                        drw = ImageDraw.Draw(base_img)
                        for l in editable_layers:
                            inp = inputs.get(l['idx'],{})
                            if not inp.get('value'): continue
                            if l['type'] == 'text':
                                # 텍스트 위치에 오버레이
                                pW, pH = base_img.size
                                sx = pW/W; sy = pH/H
                                t,le,b,r = l['rect']
                                x1,y1 = int(le*sx), int(t*sy)
                                font_size = max(10, int(20*sx))
                                try:
                                    font = ImageFont.load_default()
                                except: font = None
                                drw.rectangle([x1,y1,int(r*sx),int(b*sy)], fill=(255,255,255,200))
                                drw.text((x1+4,y1+4), inp['value'][:40], fill=(0,0,0,255), font=font)
                        buf = io.BytesIO()
                        base_img.convert("RGB").save(buf,"JPEG",quality=88)
                        st.session_state.pu_prev = buf.getvalue()
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")

        with out_cols[1]:
            if st.button("⚙️ PSD 스크립트 + JPG 저장", use_container_width=True, type="primary", key="pu_save"):
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
                            readme = f"""미샵 템플릿 OS - PSD 출력 패키지
==========================================
템플릿: {meta['name']}  |  생성일: {now}

포토샵 사용법
-----------
1. File > Scripts > Browse
2. {safe}_{now}.jsx 선택 후 실행
3. 원본 PSD 위치 지정 → 레이어 자동 교체
4. 완성 PSD가 원본 폴더에 저장됨

교체 내역
---------
텍스트: {len(txt_rep)}개  |  이미지: {len(img_rep)}개

made by MISHARP COMPANY, MIYAWA, 2026
"""
                            zf.writestr("README.txt", readme.encode('utf-8'))

                        st.download_button(
                            "⬇️ ZIP 다운로드 (JSX + 미리보기JPG)",
                            data=zbuf.getvalue(),
                            file_name=f"misharp_psd_{safe}_{now}.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
                        st.success("✅ 완료! 포토샵에서 jsx 실행하면 PSD 자동 저장됩니다")
                        st.info("📌 File > Scripts > Browse → .jsx 파일 선택 (CS5~CC 지원)")
                    except Exception as e:
                        st.error(f"오류: {e}")
