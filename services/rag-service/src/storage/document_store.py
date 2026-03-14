"""
Document Store

Manages the on-disk storage layout for processed documents:

    storage/{uuid}/
        document.md        # Markdown content from Docling
        section_map.json   # Hierarchical section map for retrieval
        images/
            picture_1.png
            ...
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

STORAGE_BASE = os.getenv("DOCLING_STORAGE_PATH", "storage")


def _doc_dir(uuid: str) -> Path:
    return Path(STORAGE_BASE) / uuid


def _markdown_path(uuid: str) -> Path:
    return _doc_dir(uuid) / "document.md"


def _section_map_path(uuid: str) -> Path:
    return _doc_dir(uuid) / "section_map.json"


def _images_dir(uuid: str) -> Path:
    return _doc_dir(uuid) / "images"


def save_document(
    uuid: str,
    markdown: str,
    images: Dict[str, bytes],
    section_map: Optional[dict] = None,
    document_id: Optional[str] = None,
) -> Path:
    """
    Persist a processed document to disk.

    Args:
        uuid: Unique identifier (used as directory name).
        markdown: Markdown text from Docling.
        images: Mapping of filename -> PNG bytes.
        section_map: Hierarchical section map (from document_mapper).
        document_id: Optional ID stored in section_map for traceability.

    Returns:
        Path to the created document directory.
    """
    doc_dir = _doc_dir(uuid)
    images_dir = _images_dir(uuid)
    images_dir.mkdir(parents=True, exist_ok=True)

    md_path = _markdown_path(uuid)
    md_path.write_text(markdown, encoding="utf-8")
    logger.info(f"Saved document.md for {uuid} ({md_path.stat().st_size} bytes)")

    if section_map is not None:
        if document_id is not None:
            section_map["document_id"] = document_id
        sm_path = _section_map_path(uuid)
        with sm_path.open("w", encoding="utf-8") as fp:
            json.dump(section_map, fp, ensure_ascii=False, indent=2)
        logger.info(f"Saved section_map.json for {uuid}")

    for filename, data in images.items():
        img_path = images_dir / filename
        with img_path.open("wb") as fp:
            fp.write(data)
    if images:
        logger.info(f"Saved {len(images)} image(s) for {uuid}")

    return doc_dir


def get_markdown(uuid: str) -> str:
    """Read and return the stored markdown for a document."""
    md_path = _markdown_path(uuid)
    if not md_path.exists():
        raise FileNotFoundError(f"No document.md for uuid {uuid}")
    return md_path.read_text(encoding="utf-8")


def get_section_map(uuid: str) -> dict:
    """Read and return the stored section map for a document."""
    sm_path = _section_map_path(uuid)
    if not sm_path.exists():
        raise FileNotFoundError(f"No section_map.json for uuid {uuid}")
    with sm_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def get_image_path(uuid: str, filename: str) -> Optional[Path]:
    """
    Return the absolute path to a stored image, or None if it does not exist.
    Rejects filenames with path-traversal components.
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        return None
    img_path = _images_dir(uuid) / filename
    return img_path if img_path.exists() else None


def list_images(uuid: str) -> List[str]:
    """Return sorted list of image filenames for a document."""
    images_dir = _images_dir(uuid)
    if not images_dir.exists():
        return []
    return sorted(f.name for f in images_dir.iterdir() if f.is_file())


def document_exists(uuid: str) -> bool:
    """Check whether document.md exists for the given UUID."""
    return _markdown_path(uuid).exists()
