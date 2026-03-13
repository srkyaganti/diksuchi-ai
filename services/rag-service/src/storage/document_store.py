"""
Document Store

Manages the on-disk storage layout for Docling-processed documents:

    storage/{uuid}/
        document.json      # Docling JSON (immutable after write)
        images/
            picture_1.png
            ...

Read and write operations only. No transformation of the Docling JSON is
performed -- it is stored exactly as produced, with one optional addition:
the document_id field at the top level.
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


def _json_path(uuid: str) -> Path:
    return _doc_dir(uuid) / "document.json"


def _images_dir(uuid: str) -> Path:
    return _doc_dir(uuid) / "images"


def save_document(
    uuid: str,
    docling_json: dict,
    images: Dict[str, bytes],
    document_id: Optional[str] = None,
) -> Path:
    """
    Persist a Docling conversion result to disk.

    Args:
        uuid: Unique identifier for the document (used as directory name).
        docling_json: Raw dict from DoclingDocument.export_to_dict().
        images: Mapping of filename -> PNG bytes for extracted images.
        document_id: Optional ID injected at the JSON top level for traceability.

    Returns:
        Path to the created document directory.
    """
    doc_dir = _doc_dir(uuid)
    images_dir = _images_dir(uuid)
    images_dir.mkdir(parents=True, exist_ok=True)

    if document_id is not None:
        docling_json["document_id"] = document_id

    json_path = _json_path(uuid)
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(docling_json, fp, ensure_ascii=False)
    logger.info(f"Saved document.json for {uuid} ({json_path.stat().st_size} bytes)")

    for filename, data in images.items():
        img_path = images_dir / filename
        with img_path.open("wb") as fp:
            fp.write(data)
    if images:
        logger.info(f"Saved {len(images)} image(s) for {uuid}")

    return doc_dir


def get_document(uuid: str) -> dict:
    """
    Read and return the stored Docling JSON for a document.

    Raises:
        FileNotFoundError: If document.json does not exist.
    """
    json_path = _json_path(uuid)
    if not json_path.exists():
        raise FileNotFoundError(f"No document.json for uuid {uuid}")

    with json_path.open("r", encoding="utf-8") as fp:
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
    """Check whether document.json exists for the given UUID."""
    return _json_path(uuid).exists()
