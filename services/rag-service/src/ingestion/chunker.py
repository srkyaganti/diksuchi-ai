"""
Section-Aware Chunker

Splits markdown documents into chunks aligned with section boundaries.
Each chunk carries metadata linking it back to its parent section,
enabling full-section context expansion during retrieval.

Strategy:
  1. Walk the flattened section map.
  2. For leaf sections (no children), extract the full section text.
  3. For parent sections, extract only the intro text between the parent
     header and the first child header (avoids duplicating child content).
  4. If text fits within MAX_CHUNK_TOKENS, emit as a single chunk.
  5. If it exceeds the limit, split at paragraph boundaries.
  6. Each chunk includes section_id, section_path, document_uuid, collection_id.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List

from src.ingestion.document_mapper import flatten_sections, get_section_text

logger = logging.getLogger(__name__)

MAX_CHUNK_TOKENS = 512
OVERLAP_TOKENS = 50
AVG_CHARS_PER_TOKEN = 4

PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict = field(default_factory=dict)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // AVG_CHARS_PER_TOKEN)


def _split_paragraphs(text: str) -> List[str]:
    """Split text on blank-line boundaries, keeping non-empty paragraphs."""
    parts = PARAGRAPH_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _get_intro_text(markdown: str, section: dict) -> str:
    """
    For a parent section, extract only the intro content between
    the section header and the first child section header.
    """
    children = section.get("children", [])
    if not children:
        return get_section_text(markdown, section)

    lines = markdown.split("\n")
    start = max(0, section["start_line"])
    first_child_start = children[0]["start_line"]
    end = max(start, first_child_start - 1)
    return "\n".join(lines[start : end + 1])


def chunk_document(
    markdown: str,
    section_map: dict,
    document_uuid: str,
    collection_id: str,
) -> List[Chunk]:
    """
    Chunk a markdown document using its section map.

    Returns a list of Chunk objects, each with metadata:
        section_id, section_path, document_uuid, collection_id, chunk_index
    """
    flat = flatten_sections(section_map)
    chunks: List[Chunk] = []
    global_idx = 0

    for sec in flat:
        children = sec.get("children", [])
        if children:
            section_text = _get_intro_text(markdown, sec)
        else:
            section_text = get_section_text(markdown, sec)

        if not section_text.strip():
            continue

        base_meta = {
            "section_id": sec["id"],
            "section_path": sec["path"],
            "document_uuid": document_uuid,
            "collection_id": collection_id,
        }

        token_estimate = _estimate_tokens(section_text)

        if token_estimate <= MAX_CHUNK_TOKENS:
            chunk = Chunk(
                chunk_id=f"{document_uuid}__chunk_{global_idx}",
                text=section_text,
                metadata={**base_meta, "chunk_index": global_idx},
            )
            chunks.append(chunk)
            global_idx += 1
        else:
            paragraphs = _split_paragraphs(section_text)
            if not paragraphs:
                continue

            current_parts: List[str] = []
            current_tokens = 0

            for para in paragraphs:
                para_tokens = _estimate_tokens(para)

                if current_tokens + para_tokens > MAX_CHUNK_TOKENS and current_parts:
                    chunk_text = "\n\n".join(current_parts)
                    chunk = Chunk(
                        chunk_id=f"{document_uuid}__chunk_{global_idx}",
                        text=chunk_text,
                        metadata={**base_meta, "chunk_index": global_idx},
                    )
                    chunks.append(chunk)
                    global_idx += 1

                    overlap_para = current_parts[-1] if current_parts else ""
                    current_parts = [overlap_para] if _estimate_tokens(overlap_para) <= OVERLAP_TOKENS else []
                    current_tokens = _estimate_tokens("\n\n".join(current_parts)) if current_parts else 0

                current_parts.append(para)
                current_tokens += para_tokens

            if current_parts:
                chunk_text = "\n\n".join(current_parts)
                chunk = Chunk(
                    chunk_id=f"{document_uuid}__chunk_{global_idx}",
                    text=chunk_text,
                    metadata={**base_meta, "chunk_index": global_idx},
                )
                chunks.append(chunk)
                global_idx += 1

    logger.info(
        f"Chunked document {document_uuid}: "
        f"{len(flat)} section(s) -> {len(chunks)} chunk(s)"
    )

    return chunks
