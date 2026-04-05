"""
ai_analyzer.py
──────────────
ChatGPT Vision API를 사용해 상세페이지 JPG를 분석하고
이미지 존(교체 가능한 제품 이미지 영역)과
텍스트 존(카피 영역)을 자동으로 감지한다.
"""

import base64
import json
import io
import re
from PIL import Image

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ──────────────────────────────────────────────────────────
# 이미지 → base64 변환 (API 전송용, 리사이즈)
# ──────────────────────────────────────────────────────────

def _img_to_b64(image_bytes: bytes, max_width: int = 1200) -> tuple[str, tuple]:
    """API 전송용 base64. 너무 크면 리사이즈. (b64, (W, H)) 반환"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    W, H = img.size

    if W > max_width:
        ratio = max_width / W
        img = img.resize((max_width, int(H * ratio)), Image.LANCZOS)
        W, H = img.size

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return b64, (W, H)


# ──────────────────────────────────────────────────────────
# 프롬프트
# ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
당신은 이커머스 상세페이지 이미지를 분석하는 전문가입니다.
주어진 상세페이지 JPG를 분석하여 아래 두 가지 영역을 JSON으로 반환하세요.

분석 대상:
1. IMAGE_ZONE: 제품 사진이나 배경 이미지가 있어서 다른 제품으로 교체 가능한 영역
2. TEXT_ZONE: 제품명, 가격, 설명 카피, 혜택 문구 등 텍스트가 있어 내용 변경이 필요한 영역

JSON 응답 형식 (다른 텍스트 없이 JSON만 반환):
{
  "zones": [
    {
      "type": "image",
      "label": "메인 제품 이미지",
      "x": 0,
      "y": 0,
      "w": 900,
      "h": 1200,
      "confidence": 0.95,
      "note": "제품 전신 컷"
    },
    {
      "type": "text",
      "label": "제품명",
      "x": 50,
      "y": 1220,
      "w": 800,
      "h": 80,
      "confidence": 0.90,
      "default_text": "감지된 텍스트 내용",
      "font_size": 42,
      "text_color": "#222222",
      "align": "center",
      "note": "상품명 카피 영역"
    }
  ],
  "analysis_summary": "분석 요약 (한국어)"
}

중요 규칙:
- 이미지 크기는 실제 픽셀 좌표로 정확히 추정할 것
- 전체 이미지 너비는 {width}px, 높이는 {height}px
- x, y는 영역 좌상단 좌표
- w, h는 너비와 높이
- 영역이 겹치지 않도록 할 것
- 교체 가능성이 낮은 장식 요소, 브랜드 로고는 제외
- 반드시 JSON만 반환 (마크다운 코드블록 제외)
"""

USER_PROMPT = "이 상세페이지 이미지를 분석해서 교체 가능한 이미지 존과 텍스트 카피 존을 JSON으로 반환해주세요."


# ──────────────────────────────────────────────────────────
# 메인 분석 함수
# ──────────────────────────────────────────────────────────

def analyze_detail_page(
    image_bytes: bytes,
    api_key: str,
    model: str = "gpt-4o",
) -> dict:
    """
    상세페이지 JPG를 GPT-4o Vision으로 분석.
    반환: {"zones": [...], "analysis_summary": "...", "canvas_size": [W, H], "error": None}
    """
    result = {"zones": [], "analysis_summary": "", "canvas_size": [900, 10000], "error": None}

    if not OPENAI_AVAILABLE:
        result["error"] = "openai 패키지가 설치되지 않았습니다. pip install openai"
        return result

    if not api_key or not api_key.strip():
        result["error"] = "OpenAI API 키가 입력되지 않았습니다."
        return result

    try:
        b64, (W, H) = _img_to_b64(image_bytes)
        result["canvas_size"] = [W, H]

        client = openai.OpenAI(api_key=api_key.strip())

        system_msg = SYSTEM_PROMPT.replace("{width}", str(W)).replace("{height}", str(H))

        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": USER_PROMPT},
                    ],
                },
            ],
        )

        raw = response.choices[0].message.content.strip()

        # JSON 파싱 (마크다운 펜스 제거)
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)

        parsed = json.loads(raw)
        zones = parsed.get("zones", [])

        # 좌표 정수화 + 기본값 보정
        clean_zones = []
        for z in zones:
            clean_zones.append({
                "type":         z.get("type", "image"),
                "label":        z.get("label", "영역"),
                "x":            int(z.get("x", 0)),
                "y":            int(z.get("y", 0)),
                "w":            max(10, int(z.get("w", 100))),
                "h":            max(10, int(z.get("h", 100))),
                "confidence":   float(z.get("confidence", 0.8)),
                "note":         z.get("note", ""),
                # 텍스트 전용 기본값
                "default_text": z.get("default_text", ""),
                "font_size":    int(z.get("font_size", 36)),
                "text_color":   z.get("text_color", "#222222"),
                "align":        z.get("align", "center"),
            })

        result["zones"] = clean_zones
        result["analysis_summary"] = parsed.get("analysis_summary", "분석 완료")

    except json.JSONDecodeError as e:
        result["error"] = f"AI 응답 파싱 오류: {e}\n원본: {raw[:300]}"
    except Exception as e:
        result["error"] = f"API 호출 오류: {str(e)}"

    return result


# ──────────────────────────────────────────────────────────
# 오프라인 Fallback: 이미지 크기 기반 기본 존 추정
# ──────────────────────────────────────────────────────────

def fallback_zones(canvas_w: int, canvas_h: int) -> list:
    """
    API 없이 이미지 크기만으로 일반적인 상세페이지 존 구조를 추정.
    900×10000px 기준 미샵 스타일 상세페이지 레이아웃 적용.
    """
    section_h = canvas_h // 6  # 대략 섹션 단위

    zones = [
        {
            "type": "image", "label": "상단 메인 이미지",
            "x": 0, "y": 0, "w": canvas_w, "h": section_h,
            "confidence": 0.6, "note": "상단 히어로 이미지",
            "default_text": "", "font_size": 40, "text_color": "#222222", "align": "center",
        },
        {
            "type": "text", "label": "제품명",
            "x": 40, "y": section_h + 20, "w": canvas_w - 80, "h": 100,
            "confidence": 0.6, "note": "제품명 카피",
            "default_text": "제품명을 입력하세요", "font_size": 42, "text_color": "#111111", "align": "center",
        },
        {
            "type": "text", "label": "서브 카피",
            "x": 40, "y": section_h + 140, "w": canvas_w - 80, "h": 80,
            "confidence": 0.5, "note": "설명 카피",
            "default_text": "서브 설명 문구", "font_size": 28, "text_color": "#555555", "align": "center",
        },
        {
            "type": "image", "label": "제품 상세 이미지 1",
            "x": 0, "y": section_h * 2, "w": canvas_w, "h": section_h,
            "confidence": 0.6, "note": "상세컷 1",
            "default_text": "", "font_size": 36, "text_color": "#222222", "align": "center",
        },
        {
            "type": "image", "label": "제품 상세 이미지 2",
            "x": 0, "y": section_h * 3, "w": canvas_w, "h": section_h,
            "confidence": 0.6, "note": "상세컷 2",
            "default_text": "", "font_size": 36, "text_color": "#222222", "align": "center",
        },
        {
            "type": "text", "label": "혜택/가격 카피",
            "x": 40, "y": section_h * 4 + 20, "w": canvas_w - 80, "h": 120,
            "confidence": 0.5, "note": "가격/혜택 문구",
            "default_text": "가격 및 혜택 문구", "font_size": 36, "text_color": "#CC0000", "align": "center",
        },
    ]
    return zones
