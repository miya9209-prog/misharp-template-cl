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

TEMPLATE_DIR = Path("templates")
META_FILE = TEMPLATE_DIR / "_meta.json"


def _ensure():
    TEMPLATE_DIR.mkdir(exist_ok=True)


def load_all() -> dict:
    _ensure()
    if META_FILE.exists():
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    return {}


def _save_meta(meta: dict):
    _ensure()
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


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

    # 썸네일 (상단 800px 기준)
    img = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    W, H = img.size
    thumb_h = min(H, int(W * 1.5))
    thumb = img.crop((0, 0, W, thumb_h)).copy()
    thumb.thumbnail((360, 540), Image.LANCZOS)
    thumb.save(tdir / "thumb.jpg", "JPEG", quality=82)

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
    m = load_one(tid)
    if not m:
        return None
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
