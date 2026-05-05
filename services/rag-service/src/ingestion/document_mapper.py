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

# Numbered-subsection detection: many technical/defence docs have flat Docling
# heading structure (everything is `##`) but the document logically uses a
# numbered hierarchy like 2.2 > 2.2.1 > 2.2.4. Some of those numbered topics
# get rendered as list items or bare prose lines instead of `#` headings, so
# we promote them to synthetic sections and re-level by numeric depth so the
# tree reflects intent. Pattern matches lines that begin (after optional `- `
# list marker) with a multi-part numeric prefix, then a Title-Case phrase, a
# period, and either end-of-line or the start of a new sentence.
NUMBERED_HEADING_RE = re.compile(
    r"^(?:- )?((\d+(?:\.\d+)+)\s+[A-Z][^.\n]{2,80})\s*\.\s*(?=[A-Z]|$)"
)
NUMERIC_PREFIX_RE = re.compile(r"^(\d+(?:\.\d+)+)")

# Page-banner detection: Docling sometimes promotes per-page header/footer
# text (e.g. classification stamps like "RESTRICTED") to markdown headings,
# which fragments real sections at every page break. We drop a heading if
# either it exactly matches a canonical classification banner (Layer A)
# or it appears on enough of the document's pages to be a banner (Layer B).
PAGE_BANNER_TITLES = {
    "RESTRICTED",
    "CONFIDENTIAL",
    "SECRET",
    "TOP SECRET",
    "UNCLASSIFIED",
    "FOR OFFICIAL USE ONLY",
    "FOUO",
    "NOFORN",
}
PAGE_BANNER_COVERAGE_RATIO = 0.5  # appears on >= 50% of pages -> banner
PAGE_BANNER_MIN_COUNT = 3         # but only if it appears at least this many times


def build_section_map(
    markdown: str,
    section_pages: Optional[Dict[str, int]] = None,
) -> dict:
    """
    Parse markdown text and produce a hierarchical section map.

    Args:
        markdown: Full markdown text.
        section_pages: Optional mapping of section title -> PDF page number
                       from Docling provenance.

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
                    "page_no": 1,
                    "children": [ ... ]
                },
                ...
            ]
        }

    Line numbers are 0-indexed. end_line is inclusive.
    """
    lines = markdown.split("\n")
    total_lines = len(lines)
    _section_pages = section_pages or {}

    raw_sections: List[dict] = []
    section_counter = 0

    for line_idx, line in enumerate(lines):
        stripped = line.strip()

        h = HEADER_RE.match(stripped)
        if h:
            section_counter += 1
            level = len(h.group(1))
            title = h.group(2).strip()
            raw_sections.append({
                "id": f"section-{section_counter}",
                "title": title,
                "level": level,
                "start_line": line_idx,
                "end_line": -1,
                "page_no": _section_pages.get(title, 0),
                "children": [],
            })
            continue

        # Synthetic heading from a numbered-subsection prose line / list item.
        # Level is set to 0 here and resolved by the re-level pass below.
        n = NUMBERED_HEADING_RE.match(stripped)
        if n:
            section_counter += 1
            title = n.group(1).strip()
            raw_sections.append({
                "id": f"section-{section_counter}",
                "title": title,
                "level": 0,
                "start_line": line_idx,
                "end_line": -1,
                "page_no": _section_pages.get(title, 0),
                "children": [],
            })

    # Drop page-banner headings before computing end_line / hierarchy so that
    # surviving sections naturally extend across the deleted banner positions.
    total_pages = max(_section_pages.values(), default=0)
    banner_titles = _identify_banner_titles(raw_sections, total_pages)
    if banner_titles:
        before = len(raw_sections)
        raw_sections = [
            s for s in raw_sections
            if s["title"].strip().upper() not in banner_titles
        ]
        logger.info(
            f"Filtered {before - len(raw_sections)} page-banner heading(s): "
            f"{sorted(banner_titles)}"
        )

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

    # Re-level numbered sections so their numeric depth determines hierarchy
    # placement. Numbered sections are placed below any non-numbered real
    # heading so a flat Docling structure (everything `##`) gets reorganized
    # into Chapter -> 2.X -> 2.X.Y nesting.
    non_numeric_levels = [
        s["level"] for s in raw_sections
        if _numeric_depth(s["title"]) is None and s["level"] > 0
    ]
    non_numeric_max = max(non_numeric_levels, default=1)
    numeric_base = non_numeric_max + 1

    numeric_depths = [
        d for s in raw_sections
        for d in [_numeric_depth(s["title"])] if d is not None
    ]
    numeric_min_depth = min(numeric_depths) if numeric_depths else 1

    for s in raw_sections:
        d = _numeric_depth(s["title"])
        if d is not None:
            s["level"] = numeric_base + (d - numeric_min_depth)
        elif s["level"] <= 0:
            s["level"] = numeric_base

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
        f"Built section map: {len(raw_sections)} section(s), "
        f"{len(root_sections)} top-level"
    )

    return {"sections": root_sections}


def _numeric_depth(title: str) -> Optional[int]:
    """Return the depth of an 'X.Y[.Z...]' style numeric prefix, or None."""
    m = NUMERIC_PREFIX_RE.match(title.strip())
    if m:
        return m.group(1).count(".") + 1
    return None


def _identify_banner_titles(raw_sections: List[dict], total_pages: int) -> set:
    """
    Identify heading titles that are repeated page-banner artifacts rather than
    real document sections.

    A title is flagged if either:
      - It exactly matches a canonical classification banner (case-insensitive), or
      - It appears as a heading at least PAGE_BANNER_MIN_COUNT times AND on at
        least PAGE_BANNER_COVERAGE_RATIO of the document's pages on average.

    Returns a set of normalized (upper, stripped) banner titles.
    """
    def norm(t: str) -> str:
        return t.strip().upper()

    banners: set = set()

    for sec in raw_sections:
        if norm(sec["title"]) in PAGE_BANNER_TITLES:
            banners.add(norm(sec["title"]))

    if total_pages > 0:
        title_counts: Dict[str, int] = {}
        for sec in raw_sections:
            t = norm(sec["title"])
            title_counts[t] = title_counts.get(t, 0) + 1

        for t, count in title_counts.items():
            if (
                count >= PAGE_BANNER_MIN_COUNT
                and count / total_pages >= PAGE_BANNER_COVERAGE_RATIO
            ):
                banners.add(t)

    return banners


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
