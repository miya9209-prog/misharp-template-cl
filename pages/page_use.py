import streamlit as st
import io, sys, os, base64
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.template_manager import load_all, load_one, get_source_bytes, get_thumb_b64
from utils.composer import compose_preview, build_output_zip


def make_scrollable_viewer(img_bytes: bytes, highlight_zone: dict = None, all_zones: list = None, height: int = 650) -> str:
    """
    스크롤 가능한 이미지 뷰어 HTML 반환.
    st.components.v1.html()로 렌더링하면 실제 스크롤 동작.
    존 오버레이는 PIL로 이미지 위에 직접 그림.
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    W, H = img.size

    if all_zones:
        ov  = img.copy().convert("RGBA")
        drw = ImageDraw.Draw(ov)
        for zone in all_zones:
            zx, zy, zw, zh = zone["x"], zone["y"], zone["w"], zone["h"]
            ztype = zone["type"]
            active = highlight_zone and zone["label"] == highlight_zone["label"]
            if active:
                fill    = (255,200,0,65) if ztype=="image" else (0,160,255,65)
                outline = (255,200,0,255) if ztype=="image" else (0,160,255,255)
                drw.rectangle([zx,zy,zx+zw,zy+zh], fill=fill, outline=outline, width=5)
                drw.rectangle([zx,zy,zx+zw,zy+38], fill=(0,0,0,170))
                drw.text((zx+8,zy+9), f"{'[IMG]' if ztype=='image' else '[TXT]'} {zone['label']}", fill=(255,255,255,255))
            else:
                col = (200,168,118,80) if ztype=="image" else (100,160,230,80)
                drw.rectangle([zx,zy,zx+zw,zy+zh], outline=col, width=2)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    return f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin:0; padding:0; background:#0a0a0f; }}
  .viewer {{
    width:100%; height:{height}px;
    overflow-y:scroll; overflow-x:hidden;
    background:#111; border:1px solid rgba(255,255,255,0.12);
    border-radius:8px; box-sizing:border-box;
  }}
  .viewer img {{ width:100%; display:block; }}
  .info {{
    color:#888; font-size:11px; text-align:center;
    padding:4px; font-family:sans-serif;
    background:#0a0a0f;
  }}
</style>
</head>
<body>
  <div class="viewer">
    <img src="data:image/jpeg;base64,{b64}" />
  </div>
  <div class="info">↕ 스크롤하여 전체 이미지 확인 &nbsp;|&nbsp; {W}×{H}px</div>
</body>
</html>"""


def render():
    for _k, _v in [("u_selected",None), ("u_inputs",{}),
                   ("u_preview",None), ("u_active_zone",None)]:
        if _k not in st.session_state:
            st.session_state[_k] = _v
    st.markdown('<div class="section-title">② 템플릿 활용</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">저장된 템플릿을 선택하고 이미지·카피를 입력한 뒤 JPG + 포토샵 스크립트로 출력하세요</div>', unsafe_allow_html=True)

    all_tpl = load_all()
    if not all_tpl:
        st.info("저장된 템플릿이 없습니다. ① 템플릿 생성 탭에서 먼저 만들어보세요.")
        return

    for k, v in [("u_selected",None),("u_inputs",{}),("u_preview",None),("u_active_zone",None)]:
        if k not in st.session_state: st.session_state[k] = v

    # ── 템플릿 선택
    if not st.session_state.u_selected:
        st.markdown("### 템플릿 선택")
        tpl_list = list(all_tpl.items())
        for row_start in range(0, len(tpl_list), 4):
            cols = st.columns(4, gap="medium")
            for ci, (tid, meta) in enumerate(tpl_list[row_start:row_start+4]):
                with cols[ci]:
                    # 이름 + 버튼 상단
                    st.markdown(f"**{meta['name']}**")
                    iz = sum(1 for z in meta.get("zones",[]) if z.get("type")=="image")
                    tz = sum(1 for z in meta.get("zones",[]) if z.get("type")=="text")
                    w, h = meta.get("canvas_size",[0,0])
                    st.caption(f"🖼️{iz} ✏️{tz} · {w}×{h}px · {meta['created_at'][:10]}")
                    if meta.get("description"): st.caption(meta["description"])
                    if st.button("사용 →", key=f"sel_{tid}", use_container_width=True, type="primary"):
                        st.session_state.u_selected    = tid
                        st.session_state.u_inputs      = {}
                        st.session_state.u_preview     = None
                        st.session_state.u_active_zone = None
                        st.rerun()
                    # 썸네일 하단 (작게)
                    b64 = get_thumb_b64(tid)
                    if b64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{b64}"                             style="width:100%;max-height:150px;object-fit:cover;object-position:top;                            border-radius:6px;border:1px solid rgba(255,255,255,0.08);margin-top:4px">',
                            unsafe_allow_html=True,
                        )
        return

    # ── 작업 화면
    tid          = st.session_state.u_selected
    tpl          = load_one(tid)
    source_bytes = get_source_bytes(tid)
    if not tpl or not source_bytes:
        st.error("템플릿을 불러오지 못했습니다")
        st.session_state.u_selected = None; return

    zones = tpl["zones"]
    iz = sum(1 for z in zones if z["type"]=="image")
    tz = sum(1 for z in zones if z["type"]=="text")
    W_c, H_c = tpl["canvas_size"]

    st.markdown(f"""<div class="info-card">
        <strong style="color:#C8A876;font-size:16px">📋 {tpl['name']}</strong><br>
        <span style="color:#A0A0A0;font-size:12px">🖼️ 이미지존 {iz}개 · ✏️ 텍스트존 {tz}개 · {W_c}×{H_c}px</span>
    </div>""", unsafe_allow_html=True)

    if st.button("← 다른 템플릿 선택", key="u_back"):
        st.session_state.u_selected = None; st.rerun()

    st.divider()
    col_form, col_prev = st.columns([1,1], gap="large")

    with col_form:
        st.markdown("### 콘텐츠 입력")
        st.caption("각 존에 이미지/카피를 입력하세요. 존 타이틀 클릭 시 오른쪽에서 위치 확인 가능.")
        inputs = dict(st.session_state.u_inputs)

        for i, zone in enumerate(zones):
            ztype, label = zone["type"], zone["label"]
            icon         = "🖼️" if ztype=="image" else "✏️"
            is_active    = (st.session_state.u_active_zone == i)
            t_col        = "#C8A876" if ztype=="image" else "#78a8f0"
            t_bg         = "rgba(200,168,118,0.15)" if ztype=="image" else "rgba(100,160,230,0.12)"
            border       = f"2px solid {t_col}" if is_active else f"1px solid rgba(255,255,255,0.1)"

            st.markdown(f"""
            <div style="background:{t_bg};border-left:4px solid {t_col};
                        padding:8px 14px;margin-top:14px;border-radius:0 6px 0 0;
                        display:flex;align-items:center;justify-content:space-between;">
              <span style="color:{t_col};font-weight:700;font-size:13px">{icon} {label}</span>
              <span style="color:#777;font-size:11px">{zone['w']}×{zone['h']}px
              {'&nbsp;<span style="color:#C8A876">◀ 선택됨</span>' if is_active else ''}</span>
            </div>
            <div style="border:{border};border-top:none;border-radius:0 0 8px 8px;
                        padding:12px 14px;margin-bottom:4px;background:rgba(255,255,255,0.02);">
            """, unsafe_allow_html=True)

            if ztype == "image":
                up = st.file_uploader(f"이미지 선택 (권장 {zone['w']}×{zone['h']}px)",
                                      type=["jpg","jpeg","png"], key=f"u_img_{i}")
                if up:
                    raw = up.read(); inputs[i] = {"value": raw}
                    th  = Image.open(io.BytesIO(raw)); th.thumbnail((180,180))
                    st.image(th, width=140)
                    st.session_state.u_active_zone = i
                elif i in inputs and inputs[i].get("value"):
                    st.success("✓ 이미지 입력됨")

            else:
                cur      = inputs.get(i,{}).get("value", zone.get("default_text",""))
                new_text = st.text_area("카피 입력", value=cur, height=85, key=f"u_txt_{i}")
                c1,c2,c3 = st.columns(3)
                with c1: new_fs = st.number_input("폰트",12,200,int(inputs.get(i,{}).get("font_size",zone.get("font_size",36))),key=f"u_fs_{i}")
                with c2: new_tc = st.color_picker("색상",inputs.get(i,{}).get("text_color",zone.get("text_color","#222222")),key=f"u_tc_{i}")
                with c3:
                    cur_al = inputs.get(i,{}).get("align",zone.get("align","center"))
                    new_al = st.selectbox("정렬",["center","left","right"],
                        index=["center","left","right"].index(cur_al),
                        format_func=lambda x:{"center":"가운데","left":"왼쪽","right":"오른쪽"}[x],key=f"u_al_{i}")
                inputs[i] = {"value":new_text,"font_size":new_fs,"text_color":new_tc,"align":new_al}

            if st.button(f"👁 미리보기에서 확인", key=f"u_focus_{i}"):
                st.session_state.u_active_zone = i; st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.session_state.u_inputs = inputs
        st.divider()
        if st.button("🔍 전체 미리보기 생성", use_container_width=True, type="primary", key="u_prevbtn"):
            with st.spinner("합성 중..."):
                pv = compose_preview(source_bytes, zones, tpl.get("bg_color","#FFFFFF"), inputs, show_guides=False)
            st.session_state.u_preview = pv; st.rerun()

    with col_prev:
        st.markdown("### 미리보기")
        az_idx = st.session_state.u_active_zone
        az     = zones[az_idx] if (az_idx is not None and az_idx < len(zones)) else None

        disp_bytes = st.session_state.u_preview if st.session_state.u_preview else source_bytes
        label_txt  = "합성 결과" if st.session_state.u_preview else "템플릿 원본"
        if disp_bytes:
            import base64
            disp_img = __import__('PIL.Image', fromlist=['Image']).Image.open(
                __import__('io').BytesIO(disp_bytes)).convert("RGB")
            buf = __import__('io').BytesIO()
            disp_img.save(buf, "JPEG", quality=85)
            b64_disp = base64.b64encode(buf.getvalue()).decode()
            st.markdown(
                f'<img src="data:image/jpeg;base64,{b64_disp}" '
                f'style="width:100%;display:block;border-radius:8px;'
                f'border:1px solid rgba(255,255,255,0.12);">',
                unsafe_allow_html=True,
            )

        if az:
            t_col = "#C8A876" if az["type"]=="image" else "#78a8f0"
            st.markdown(f'<div style="text-align:center;color:{t_col};font-size:12px;font-weight:600">▲ 강조: {az["label"]}</div>', unsafe_allow_html=True)

        # 존 점프 목록
        st.markdown("**존 목록 (클릭 → 강조)**")
        jcols = st.columns(2)
        for i, zone in enumerate(zones):
            icon  = "🖼️" if zone["type"]=="image" else "✏️"
            is_s  = (az_idx == i)
            with jcols[i%2]:
                if st.button(f"{icon} {zone['label']}", key=f"jump_{i}",
                             use_container_width=True,
                             type="primary" if is_s else "secondary"):
                    st.session_state.u_active_zone = i; st.rerun()

        st.divider()
        st.markdown("**📦 출력**")
        st.caption("완성본 JPG + 포토샵 레이어 스크립트(.jsx) ZIP으로 다운로드")

        if st.button("⚙️ JPG + 포토샵 스크립트 생성", use_container_width=True, type="primary", key="u_genbtn"):
            with st.spinner("생성 중..."):
                try:
                    zip_bytes = build_output_zip(tpl, source_bytes, st.session_state.u_inputs)
                    safe = tpl["name"].replace(" ","_")[:30]
                    st.download_button("⬇️ ZIP 다운로드", data=zip_bytes,
                                       file_name=f"misharp_{safe}.zip",
                                       mime="application/zip", use_container_width=True)
                    st.success("✅ 생성 완료!")
                    st.info("📌 포토샵 사용법: File > Scripts > Browse → .jsx 파일 선택 실행 (CS5~CC 지원)")
                except Exception as e:
                    st.error(f"오류: {e}")
