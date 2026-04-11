"""
Document Mapper

Parses markdown headers to build a hierarchical section map.
The section map enables:
  - Section-aware chunking (Phase 3)
  - Full-section context expansion during retrieval (Phase 4)
"""

import logging
import re
from typing import Dict, List, Optional

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


def map_images_to_sections(
    markdown: str,
    section_map: dict,
    image_info: dict,
) -> Dict[str, str]:
    """
    Map image filenames to section IDs using ``<!-- image -->`` markers
    in the markdown and section line ranges.

    For picture images: uses 1:1 correspondence between ``<!-- image -->``
    marker order and picture extraction order.

    For table images: matches by section_title from ImageInfo against
    section titles in the map.

    Args:
        markdown: The full markdown text from Docling.
        section_map: Hierarchical section map from build_section_map().
        image_info: Dict of filename -> ImageInfo from DoclingResult.

    Returns:
        Dict mapping image filename -> section_id.
    """
    flat = flatten_sections(section_map)
    result: Dict[str, str] = {}

    if not flat:
        return result

    def _find_section_for_line(line_no: int) -> Optional[str]:
        for sec in flat:
            if sec["start_line"] <= line_no <= sec["end_line"]:
                return sec["id"]
        return flat[-1]["id"] if flat else None

    # Collect <!-- image --> marker line numbers
    lines = markdown.split("\n")
    marker_lines = [
        i for i, line in enumerate(lines)
        if line.strip() == "<!-- image -->"
    ]

    # Build ordered list of picture filenames (picture_1, picture_2, ...)
    picture_filenames = sorted(
        [fn for fn, info in image_info.items() if info.image_type == "picture"],
        key=lambda fn: int(fn.split("_")[1].split(".")[0]),
    )

    # Map pictures via marker positions (1:1 correspondence)
    for idx, filename in enumerate(picture_filenames):
        if idx < len(marker_lines):
            section_id = _find_section_for_line(marker_lines[idx])
            if section_id:
                result[filename] = section_id
        else:
            # Fallback: match by section title
            info = image_info[filename]
            matched = _match_by_title(flat, info.section_title)
            if matched:
                result[filename] = matched

    # Map table images by section title matching
    table_filenames = [
        fn for fn, info in image_info.items() if info.image_type == "table"
    ]
    for filename in table_filenames:
        info = image_info[filename]
        matched = _match_by_title(flat, info.section_title)
        if matched:
            result[filename] = matched

    logger.info(
        f"Mapped {len(result)}/{len(image_info)} images to sections"
    )
    return result


def _match_by_title(flat_sections: List[dict], title: str) -> Optional[str]:
    """Find a section whose title matches the given title."""
    if not title:
        return None
    title_lower = title.lower().strip()
    for sec in flat_sections:
        if sec["title"].lower().strip() == title_lower:
            return sec["id"]
    # Partial match fallback
    for sec in flat_sections:
        if title_lower in sec["title"].lower() or sec["title"].lower() in title_lower:
            return sec["id"]
    return None
