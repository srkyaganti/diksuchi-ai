"""
Section Context Expander

After retrieval and reranking identify the best *chunks*, this module
expands each chunk back to its full parent section using the document map.
This gives the LLM complete context around the answer, dramatically
reducing hallucination for technical defence documents.
"""

import logging
from typing import Dict, List

from src.storage.document_store import get_markdown, get_section_map
from src.ingestion.document_mapper import find_section_by_id, get_section_text

logger = logging.getLogger(__name__)


def expand_to_sections(
    ranked_results: List[Dict],
    top_k: int = 5,
) -> List[Dict]:
    """
    For each top-k reranked chunk, look up its parent section and
    return the full section text (deduplicated).

    Args:
        ranked_results: Reranked chunk dicts (must have metadata with
                        section_id and document_uuid).
        top_k: Number of top chunks to expand.

    Returns:
        List of section dicts:
            {
                "content": <full section markdown>,
                "section_path": "Chapter > Section",
                "section_id": "section-3",
                "document_uuid": "...",
                "score": <best chunk score in this section>,
            }
    """
    seen_sections: Dict[str, Dict] = {}  # keyed by (uuid, section_id)

    for result in ranked_results[:top_k]:
        meta = result.get("metadata") or {}
        doc_uuid = meta.get("document_uuid")
        section_id = meta.get("section_id")

        if not doc_uuid or not section_id:
            continue

        dedup_key = f"{doc_uuid}::{section_id}"
        if dedup_key in seen_sections:
            existing_score = seen_sections[dedup_key].get("score", 0)
            new_score = result.get("rerank_score", result.get("score", 0))
            if new_score > existing_score:
                seen_sections[dedup_key]["score"] = new_score
            continue

        try:
            markdown = get_markdown(doc_uuid)
            section_map = get_section_map(doc_uuid)
        except FileNotFoundError:
            logger.warning(f"Storage files missing for document {doc_uuid}")
            continue

        section = find_section_by_id(section_map, section_id)
        if section is None:
            logger.warning(
                f"Section {section_id} not found in map for document {doc_uuid}"
            )
            continue

        section_text = get_section_text(markdown, section)

        seen_sections[dedup_key] = {
            "content": section_text,
            "section_path": section.get("path", ""),
            "section_id": section_id,
            "document_uuid": doc_uuid,
            "score": result.get("rerank_score", result.get("score", 0)),
        }

    sections = sorted(
        seen_sections.values(), key=lambda s: s["score"], reverse=True
    )

    logger.info(
        f"Expanded {min(top_k, len(ranked_results))} chunks "
        f"-> {len(sections)} unique section(s)"
    )

    return sections
