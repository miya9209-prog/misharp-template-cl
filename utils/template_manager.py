"""
template_manager.py
───────────────────
템플릿 저장·로드·삭제·메타데이터 관리
"""

import json
import os
import shutil
import base64
import io
from pathlib import Path
from datetime import datetime
from PIL import Image

THUMB_VERSION = 2
THUMB_RENDER_SIZE = (240, 4096)

TEMPLATE_DIR = Path("templates")
META_FILE = TEMPLATE_DIR / "_meta.json"


def _ensure():
    TEMPLATE_DIR.mkdir(exist_ok=True)


def load_all() -> dict:
    _ensure()
    if META_FILE.exists():
        try:
            raw = META_FILE.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            # 값이 dict이고 name 키가 있는 것만 반환
            result = {}
            for k, v in data.items():
                try:
                    if isinstance(v, dict) and isinstance(v.get("name"), str):
                        result[k] = v
                except Exception:
                    continue
            return result
        except Exception:
            return {}
    return {}


def _save_meta(meta: dict):
    _ensure()
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_full_thumb_bytes(img: Image.Image) -> bytes:
    """전체 이미지 비율을 유지한 세로형 썸네일 JPEG 생성."""
    thumb = img.convert("RGB").copy()
    thumb.thumbnail(THUMB_RENDER_SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    thumb.save(buf, "JPEG", quality=84)
    return buf.getvalue()


def _write_full_thumb_from_image(img: Image.Image, out_path: Path):
    out_path.write_bytes(_build_full_thumb_bytes(img))


def _refresh_thumb_for_template(tid: str, meta: dict) -> bool:
    """구버전 잘린 썸네일을 전체 이미지형 썸네일로 1회 갱신."""
    try:
        item = meta.get(tid)
        if not isinstance(item, dict):
            return False
        tdir = Path(item.get("path", TEMPLATE_DIR / tid))
        thumb_path = tdir / "thumb.jpg"
        if item.get("thumb_version") == THUMB_VERSION and thumb_path.exists():
            return False

        if item.get("template_type") == "psd":
            from utils.psd_parser import psd_to_preview_jpg
            psd_path = tdir / "source.psd"
            if not psd_path.exists():
                return False
            prev = psd_to_preview_jpg(psd_path.read_bytes(), max_width=900)
            img = Image.open(io.BytesIO(prev)).convert("RGB")
        else:
            src_path = tdir / "source.jpg"
            if not src_path.exists():
                return False
            img = Image.open(src_path).convert("RGB")

        _write_full_thumb_from_image(img, thumb_path)
        item["thumb_version"] = THUMB_VERSION
        _save_meta(meta)
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────
# 템플릿 저장
# ──────────────────────────────────────────────────────────

def save_template(
    name: str,
    source_bytes: bytes,
    zones: list,          # [{type, label, x, y, w, h, ...defaults}]
    bg_color: str = "#FFFFFF",
    description: str = "",
) -> str:
    """템플릿 저장. 생성된 tid 반환."""
    _ensure()
    tid = "tpl_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    tdir = TEMPLATE_DIR / tid
    tdir.mkdir(exist_ok=True)

    # 원본 이미지 저장
    (tdir / "source.jpg").write_bytes(source_bytes)

    # 썸네일 (전체 이미지 비율 유지)
    img = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    W, H = img.size
    _write_full_thumb_from_image(img, tdir / "thumb.jpg")

    meta = load_all()
    meta[tid] = {
        "id": tid,
        "name": name,
        "description": description,
        "bg_color": bg_color,
        "zones": zones,
        "canvas_size": [W, H],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "path": str(tdir),
        "thumb_version": THUMB_VERSION,
    }
    _save_meta(meta)
    return tid


def load_one(tid: str) -> dict | None:
    return load_all().get(tid)


def delete_template(tid: str):
    meta = load_all()
    if tid in meta:
        tdir = Path(meta[tid]["path"])
        if tdir.exists():
            shutil.rmtree(tdir)
        del meta[tid]
        _save_meta(meta)


def get_source_bytes(tid: str) -> bytes | None:
    m = load_one(tid)
    if not m:
        return None
    p = Path(m["path"]) / "source.jpg"
    return p.read_bytes() if p.exists() else None


def get_thumb_b64(tid: str) -> str | None:
    meta = load_all()
    m = meta.get(tid)
    if not m:
        return None
    _refresh_thumb_for_template(tid, meta)
    p = Path(m["path"]) / "thumb.jpg"
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode()


def update_zones(tid: str, zones: list):
    meta = load_all()
    if tid in meta:
        meta[tid]["zones"] = zones
        _save_meta(meta)


def update_bg(tid: str, bg_color: str):
    meta = load_all()
    if tid in meta:
        meta[tid]["bg_color"] = bg_color
        _save_meta(meta)


# ── PSD 템플릿 전용 ────────────────────────────────────────

def save_psd_template(
    name: str,
    psd_bytes: bytes,
    psd_info: dict,      # parse_psd() 반환값 (raw 제외)
    description: str = "",
) -> str:
    """PSD 기반 템플릿 저장. tid 반환."""
    _ensure()
    tid  = "psd_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    tdir = TEMPLATE_DIR / tid
    tdir.mkdir(exist_ok=True)

    # 원본 PSD 저장
    (tdir / "source.psd").write_bytes(psd_bytes)

    # 레이어 정보 JSON (raw 제외)
    info_save = {k:v for k,v in psd_info.items() if k != 'raw'}
    (tdir / "psd_info.json").write_text(
        json.dumps(info_save, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 병합 미리보기 썸네일 (전체 이미지 비율 유지)
    try:
        from utils.psd_parser import psd_to_preview_jpg
        prev = psd_to_preview_jpg(psd_bytes, max_width=900)
        _img = Image.open(io.BytesIO(prev)).convert("RGB")
        _write_full_thumb_from_image(_img, tdir / "thumb.jpg")
    except Exception:
        pass

    meta = load_all()
    meta[tid] = {
        "id": tid, "name": name, "description": description,
        "template_type": "psd",
        "canvas_size": [psd_info["width"], psd_info["height"]],
        "num_layers": psd_info["num_layers"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "path": str(tdir),
        "thumb_version": THUMB_VERSION,
    }
    _save_meta(meta)
    return tid


def load_psd_info(tid: str) -> dict | None:
    """PSD 템플릿의 레이어 정보 반환."""
    m = load_one(tid)
    if not m: return None
    p = Path(m["path"]) / "psd_info.json"
    if not p.exists(): return None
    return json.loads(p.read_text(encoding="utf-8"))


def get_psd_bytes(tid: str) -> bytes | None:
    m = load_one(tid)
    if not m: return None
    p = Path(m["path"]) / "source.psd"
    return p.read_bytes() if p.exists() else None
