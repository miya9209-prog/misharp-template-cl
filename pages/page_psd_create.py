"""
page_psd_create.py — PSD 템플릿 생성
PSD 업로드 → 레이어 자동 분석 → 교체 대상 지정 → 템플릿 저장
"""
import streamlit as st
import streamlit.components.v1 as components
import io, sys, os, base64, json
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.psd_parser import parse_psd, psd_to_preview_jpg
from utils.template_manager import save_psd_template, load_all


def make_layer_map_html(prev_bytes, layers, active_idx, W_orig, H_orig, viewer_h=640):
    """
    레이어 위치를 시각적으로 표시하는 인터랙티브 HTML.
    레이어 박스 클릭 → Streamlit으로 선택 신호 전달 (URL param).
    """
    img = Image.open(io.BytesIO(prev_bytes)).convert("RGB")
    pW, pH = img.size
    sx = pW / W_orig
    sy = pH / H_orig

    # 레이어 박스 오버레이 그리기
    ov  = img.convert("RGBA")
    drw = ImageDraw.Draw(ov)

    editable = [l for l in layers
                if (l['type'] in ('text','pixel'))
                and l['w'] > 30 and l['h'] > 10
                and l['idx'] != 0]  # Background 제외

    for l in editable:
        t,le,b,r = l['rect']
        px = [int(le*sx), int(t*sy), int(r*sx), int(b*sy)]
        is_active = (l['idx'] == active_idx)
        if l['type'] == 'text':
            fill    = (255,200,0,70)  if is_active else (255,200,0,25)
            outline = (255,200,0,255) if is_active else (255,200,0,100)
        else:
            fill    = (100,160,255,70)  if is_active else (100,160,255,20)
            outline = (100,160,255,255) if is_active else (100,160,255,80)
        drw.rectangle([px[0],px[1],px[2],px[3]], fill=fill, outline=outline,
                      width=3 if is_active else 1)
        if is_active:
            drw.rectangle([px[0],px[1],px[2],px[1]+28], fill=(0,0,0,180))
            drw.text((px[0]+5, px[1]+6), l['name'][:30], fill=(255,255,255,255))

    merged = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    buf = io.BytesIO(); merged.save(buf,"JPEG",quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # 레이어 클릭 영역 JS map
    area_js = json.dumps([{
        "idx": l['idx'],
        "name": l['name'],
        "type": l['type'],
        "px": [int(l['rect'][1]*sx), int(l['rect'][0]*sy),
               int(l['rect'][3]*sx), int(l['rect'][2]*sy)],
    } for l in editable])

    return f"""<!DOCTYPE html><html><head><style>
body{{margin:0;background:#0a0a0f;}}
.wrap{{position:relative;width:100%;height:{viewer_h}px;overflow-y:scroll;
       overflow-x:hidden;background:#111;border:1px solid rgba(255,255,255,0.12);
       border-radius:8px;}}
.wrap img{{width:100%;display:block;}}
.hint{{color:#888;font-size:11px;text-align:center;padding:4px;
       font-family:sans-serif;background:#0a0a0f;}}
</style></head><body>
<div class="wrap" id="viewer">
  <img src="data:image/jpeg;base64,{b64}" id="psdimg" onclick="handleClick(event)"/>
</div>
<div class="hint">↕ 스크롤 | 레이어 박스 클릭하면 왼쪽 입력칸 활성화</div>
<script>
var layers = {area_js};
var imgEl  = document.getElementById('psdimg');
function handleClick(e) {{
  var rect   = imgEl.getBoundingClientRect();
  var scTop  = document.getElementById('viewer').scrollTop;
  var cx     = e.clientX - rect.left;
  var cy     = e.clientY - rect.top + scTop;
  var scale  = imgEl.naturalWidth / imgEl.offsetWidth;
  var px = cx * scale, py = cy * scale;
  for(var i=0;i<layers.length;i++) {{
    var l = layers[i];
    if(px>=l.px[0] && px<=l.px[2] && py>=l.px[1] && py<=l.px[3]) {{
      var url = new URL(window.location.href, window.parent.location.href);
      url.searchParams.set('psd_active', l.idx);
      window.parent.location.href = url.toString();
      break;
    }}
  }}
}}
</script>
</body></html>"""


def render():
    st.markdown('<div class="section-title">③ PSD 템플릿 생성</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">PSD 파일을 업로드하면 레이어를 자동 분석하여 템플릿으로 저장합니다</div>', unsafe_allow_html=True)

    for k, v in [("pc_info",None),("pc_bytes",None),("pc_prev",None),
                 ("pc_fname",""),("pc_editable",{}),("pc_active",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # URL 파라미터로 클릭된 레이어 수신
    q_active = st.query_params.get("psd_active")
    if q_active and q_active.isdigit():
        st.session_state.pc_active = int(q_active)
        st.query_params.clear()

    # ── STEP 1
    st.markdown('<div class="step-header">STEP 1 · PSD 업로드</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("PSD 파일 업로드", type=["psd"], key="pc_upload")
    if uploaded:
        with st.spinner("레이어 분석 중..."):
            raw = uploaded.read()
            try:
                info = parse_psd(raw)
                prev = psd_to_preview_jpg(raw, max_width=900)
                st.session_state.pc_info  = info
                st.session_state.pc_bytes = raw
                st.session_state.pc_prev  = prev
                st.session_state.pc_fname = uploaded.name
                st.session_state.pc_editable = {}
                st.session_state.pc_active    = None
                n_txt = sum(1 for l in info['layers'] if l['type']=='text' and l['w']>0)
                n_pix = sum(1 for l in info['layers'] if l['type']=='pixel' and l['w']>80)
                st.success(f"✅ {info['width']}×{info['height']}px | 텍스트 {n_txt}개 · 이미지 {n_pix}개 레이어 감지")
            except Exception as e:
                st.error(f"PSD 파싱 오류: {e}"); return

    if not st.session_state.pc_info:
        st.info("PSD 파일을 올리면 레이어 구조를 자동으로 분석합니다")
        return

    info    = st.session_state.pc_info
    layers  = info['layers']
    W, H    = info['width'], info['height']
    active  = st.session_state.pc_active
    editable_flags = st.session_state.pc_editable  # {idx: True/False}

    editable_layers = [l for l in layers
                       if l['type'] in ('text','pixel')
                       and l['w'] > 30 and l['h'] > 10
                       and l['idx'] != 0]

    st.divider()

    # ── STEP 2: 레이어 지정
    st.markdown('<div class="step-header">STEP 2 · 교체 대상 레이어 지정</div>', unsafe_allow_html=True)
    st.caption("오른쪽 미리보기에서 레이어 박스를 클릭하거나, 왼쪽 목록에서 체크하세요")

    col_list, col_prev = st.columns([1, 1], gap="large")

    with col_list:
        st.markdown("**레이어 목록** — 교체 가능하게 할 레이어를 체크하세요")

        # 텍스트 레이어
        txt_layers = [l for l in editable_layers if l['type']=='text']
        if txt_layers:
            st.markdown("**✏️ 텍스트 레이어**")
            for l in txt_layers:
                is_active = (active == l['idx'])
                checked   = editable_flags.get(l['idx'], True)
                orig_text = l['text'].split('\n')[0][:35] if l['text'] else l['name']

                border = "2px solid #C8A876" if is_active else "1px solid rgba(255,255,255,0.08)"
                bg     = "rgba(200,168,118,0.1)" if is_active else "rgba(255,255,255,0.02)"

                col_ck, col_info = st.columns([1,6])
                with col_ck:
                    new_checked = st.checkbox("", value=checked, key=f"ck_{l['idx']}")
                    editable_flags[l['idx']] = new_checked
                with col_info:
                    st.markdown(f"""
                    <div style="background:{bg};border:{border};border-radius:6px;
                                padding:6px 10px;margin:2px 0;cursor:pointer"
                         onclick="void(0)">
                        <span style="color:#C8A876;font-size:12px;font-weight:600">✏️ {l['name'][:25]}</span><br>
                        <span style="color:#888;font-size:11px">원본: {orig_text}</span>
                    </div>""", unsafe_allow_html=True)
                    if st.button("👁", key=f"focus_txt_{l['idx']}", help="미리보기에서 확인"):
                        st.session_state.pc_active = l['idx']; st.rerun()

        st.divider()

        # 픽셀(이미지) 레이어
        pix_layers = [l for l in editable_layers if l['type']=='pixel'
                      and l['w'] > 80 and l['h'] > 80]
        if pix_layers:
            st.markdown("**🖼️ 이미지 레이어**")
            for l in pix_layers:
                is_active = (active == l['idx'])
                checked   = editable_flags.get(l['idx'], False)  # 이미지는 기본 미체크
                border = "2px solid #78a8f0" if is_active else "1px solid rgba(255,255,255,0.08)"
                bg     = "rgba(100,160,230,0.1)" if is_active else "rgba(255,255,255,0.02)"

                col_ck, col_info = st.columns([1,6])
                with col_ck:
                    new_checked = st.checkbox("", value=checked, key=f"ck_{l['idx']}")
                    editable_flags[l['idx']] = new_checked
                with col_info:
                    st.markdown(f"""
                    <div style="background:{bg};border:{border};border-radius:6px;
                                padding:6px 10px;margin:2px 0">
                        <span style="color:#78a8f0;font-size:12px;font-weight:600">🖼️ {l['name'][:25]}</span><br>
                        <span style="color:#888;font-size:11px">{l['w']}×{l['h']}px | ({l['rect'][1]},{l['rect'][0]})</span>
                    </div>""", unsafe_allow_html=True)
                    if st.button("👁", key=f"focus_pix_{l['idx']}", help="미리보기에서 확인"):
                        st.session_state.pc_active = l['idx']; st.rerun()

        st.session_state.pc_editable = editable_flags

        checked_count = sum(1 for v in editable_flags.values() if v)
        st.divider()
        if checked_count:
            st.success(f"✅ {checked_count}개 레이어가 교체 대상으로 지정됨")
        else:
            st.warning("교체할 레이어를 1개 이상 체크하세요")

    with col_prev:
        st.markdown("**PSD 미리보기 — 클릭하면 레이어 선택**")
        if st.session_state.pc_prev:
            html = make_layer_map_html(
                st.session_state.pc_prev, editable_layers,
                active, W, H, viewer_h=640
            )
            components.html(html, height=680, scrolling=False)
            if active is not None:
                al = next((l for l in layers if l['idx']==active), None)
                if al:
                    color = "#C8A876" if al['type']=='text' else "#78a8f0"
                    st.markdown(f'<div style="text-align:center;color:{color};font-size:12px;font-weight:600;margin-top:4px">선택됨: {al["name"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ── STEP 3: 저장
    st.markdown('<div class="step-header">STEP 3 · 템플릿 저장</div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns([3,1], gap="medium")
    with sc1:
        tpl_name = st.text_input("템플릿 이름 *", placeholder="예: 에코레더자켓_상세v1", key="pc_name")
        tpl_desc = st.text_input("설명 (선택)", placeholder="시즌, 카테고리 등", key="pc_desc")
    with sc2:
        st.write(""); st.write("")
        if st.button("💾 PSD 템플릿 저장", type="primary", use_container_width=True, key="pc_save"):
            if not tpl_name.strip():
                st.error("템플릿 이름을 입력하세요")
            elif not any(editable_flags.values()):
                st.error("교체할 레이어를 1개 이상 선택하세요")
            else:
                # 선택된 레이어만 editable로 표시
                save_info = dict(info)
                save_info['editable_layers'] = {
                    str(idx): True for idx, v in editable_flags.items() if v
                }
                with st.spinner("저장 중..."):
                    tid = save_psd_template(
                        name        = tpl_name.strip(),
                        psd_bytes   = st.session_state.pc_bytes,
                        psd_info    = save_info,
                        description = tpl_desc.strip(),
                    )
                st.success(f"✅ PSD 템플릿 저장 완료! ID: {tid}")
                st.balloons()
                for k in ["pc_info","pc_bytes","pc_prev","pc_fname","pc_editable","pc_active"]:
                    st.session_state[k] = None if k != "pc_editable" else {}
                st.rerun()

    st.caption(f"현재 저장된 템플릿: {len(load_all())}개")
