"""
Document Mapper

Parses markdown headers to build a hierarchical section map.
The section map enables:
  - Section-aware chunking (Phase 3)
  - Full-section context expansion during retrieval (Phase 4)
"""

import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")


def build_section_map(markdown: str) -> dict:
    """
    Parse markdown text and produce a hierarchical section map.

    Returns:
        {
            "sections": [
                {
                    "id": "section-1",
                    "title": "...",
                    "level": 1,
                    "path": "Chapter Title",
                    "start_line": 0,
                    "end_line": 44,
                    "children": [ ... ]
                },
                ...
            ]
        }

    Line numbers are 0-indexed. end_line is inclusive.
    """
    lines = markdown.split("\n")
    total_lines = len(lines)

    raw_sections: List[dict] = []
    section_counter = 0

    for line_idx, line in enumerate(lines):
        match = HEADER_RE.match(line.strip())
        if match:
            section_counter += 1
            level = len(match.group(1))
            title = match.group(2).strip()
            raw_sections.append({
                "id": f"section-{section_counter}",
                "title": title,
                "level": level,
                "start_line": line_idx,
                "end_line": -1,
                "children": [],
            })

    if not raw_sections:
        return {
            "sections": [{
                "id": "section-1",
                "title": "Document",
                "level": 1,
                "path": "Document",
                "start_line": 0,
                "end_line": total_lines - 1,
                "children": [],
            }]
        }

    # Fill in end_line: each section extends until the next section at same or higher level
    for i, sec in enumerate(raw_sections):
        if i + 1 < len(raw_sections):
            sec["end_line"] = raw_sections[i + 1]["start_line"] - 1
        else:
            sec["end_line"] = total_lines - 1

    # Build hierarchy: nest children under their parents based on heading level
    root_sections: List[dict] = []
    stack: List[dict] = []

    for sec in raw_sections:
        # Pop stack until we find a parent with a lower level
        while stack and stack[-1]["level"] >= sec["level"]:
            stack.pop()

        # Build the breadcrumb path
        if stack:
            sec["path"] = stack[-1]["path"] + " > " + sec["title"]
            stack[-1]["children"].append(sec)
        else:
            sec["path"] = sec["title"]
            root_sections.append(sec)

        stack.append(sec)

    logger.info(
        f"Built section map: {section_counter} section(s), "
        f"{len(root_sections)} top-level"
    )

    return {"sections": root_sections}


def get_section_text(markdown: str, section: dict) -> str:
    """Extract the full text of a section from markdown by line range."""
    lines = markdown.split("\n")
    start = max(0, section["start_line"])
    end = min(len(lines) - 1, section["end_line"])
    return "\n".join(lines[start : end + 1])


def flatten_sections(section_map: dict) -> List[dict]:
    """
    Flatten the hierarchical section map into a list of leaf/all sections.
    Each item keeps its 'path' for breadcrumb context.
    """
    flat: List[dict] = []

    def _walk(sections: List[dict]) -> None:
        for sec in sections:
            flat.append(sec)
            if sec.get("children"):
                _walk(sec["children"])

    _walk(section_map.get("sections", []))
    return flat


def find_section_by_id(section_map: dict, section_id: str) -> Optional[dict]:
    """Look up a section by its id in the hierarchical map."""
    for sec in flatten_sections(section_map):
        if sec["id"] == section_id:
            return sec
    return None
