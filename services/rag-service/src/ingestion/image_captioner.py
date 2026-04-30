"""
Image Captioner

Generates descriptive captions for document images using an Ollama vision model.
Falls back gracefully when no vision model is available -- images still get
section-mapped, they just don't get AI-generated captions.

Caption priority:
  1. Docling-extracted caption (from PDF figure captions)
  2. Vision model caption (via Ollama)
  3. Section-title fallback ("Image from section: ...")
"""

import base64
import logging
import os
from typing import Callable, Dict, Optional

import httpx

from src.ingestion.docling_converter import ImageInfo

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "")  # empty = disabled
VISION_TIMEOUT = float(os.getenv("VISION_TIMEOUT", "30.0"))

CAPTION_PROMPT = (
    "Describe this technical image from an equipment manual in 1-2 sentences. "
    "Focus on what equipment, component, or procedure is shown. "
    "Include any visible labels, part numbers, or annotations."
)


def is_vision_available() -> bool:
    """Check if a vision model is configured and reachable."""
    if not VISION_MODEL:
        return False
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = [
                m.get("name", "").split(":")[0]
                for m in resp.json().get("models", [])
            ]
            return VISION_MODEL.split(":")[0] in models
    except Exception:
        return False


def caption_image(
    image_bytes: bytes, context_hint: str = ""
) -> Optional[str]:
    """
    Generate a caption for a single image using the Ollama vision model.

    Args:
        image_bytes: PNG image data.
        context_hint: Optional text like section title to provide context.

    Returns:
        Caption string, or None if captioning fails or is unavailable.
    """
    if not VISION_MODEL:
        return None

    b64 = base64.b64encode(image_bytes).decode("ascii")

    prompt = CAPTION_PROMPT
    if context_hint:
        prompt += f"\n\nThis image appears in the section: {context_hint}"

    try:
        with httpx.Client(timeout=VISION_TIMEOUT) as client:
            resp = client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": VISION_MODEL,
                    "prompt": prompt,
                    "images": [b64],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip() or None
    except Exception as exc:
        logger.warning(f"Vision captioning failed: {exc}")
        return None


def caption_images(
    images: Dict[str, bytes],
    image_info: Dict[str, ImageInfo],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, str]:
    """
    Generate captions for all images, preferring Docling captions when available.

    Args:
        images: Mapping of filename -> PNG bytes.
        image_info: Mapping of filename -> ImageInfo with docling captions
                    and section context.

    Returns:
        Dict mapping filename -> caption string.
    """
    captions: Dict[str, str] = {}
    vision_ok = is_vision_available()

    docling_count = 0
    vision_count = 0
    fallback_count = 0
    total = len(image_info)

    for i, (filename, info) in enumerate(image_info.items()):
        # Priority 1: Docling-extracted caption from the PDF
        if info.docling_caption:
            captions[filename] = info.docling_caption
            docling_count += 1
            continue

        # Priority 2: Vision model caption
        if vision_ok and filename in images:
            caption = caption_image(
                images[filename],
                context_hint=info.section_title,
            )
            if caption:
                captions[filename] = caption
                vision_count += 1
                continue

        # Priority 3: Section-title fallback
        captions[filename] = f"Image from section: {info.section_title}"
        fallback_count += 1

        if progress_callback:
            progress_callback(i + 1, total)

    logger.info(
        f"Captioned {len(captions)} images "
        f"(docling={docling_count}, vision={vision_count}, "
        f"fallback={fallback_count})"
    )
    return captions
