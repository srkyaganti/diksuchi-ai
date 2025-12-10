"""
Citation tracking and source attribution module.

Adds source attribution to retrieval results and validates citations in LLM responses.
Critical for defense manuals where traceability to source documents is essential.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class CitationTracker:
    """Manages source attribution and citation validation."""

    def __init__(self):
        """Initialize citation tracker."""
        self.citation_format = "[C{idx}]"
        self.citation_counter = 0

    def enrich_with_citations(
        self, results: List[Dict], start_index: int = 1
    ) -> List[Dict]:
        """
        Add citation metadata to retrieval results.

        Creates a unique citation ID (C1, C2, C3, etc.) for each result
        and enriches with source information.

        Args:
            results: Retrieval results from quality gates
            start_index: Starting index for citation numbering (default: 1)

        Returns:
            Results enriched with citation metadata
        """
        self.citation_counter = start_index

        for result in results:
            citation_id = f"C{self.citation_counter}"
            self.citation_counter += 1

            # Extract source information
            metadata = result.get("metadata", {})
            source_file = self._extract_filename(metadata.get("source", "unknown"))
            source_page = metadata.get("page", "?")
            source_section = metadata.get("section", "")

            # Create citation object
            citation = {
                "citation_id": citation_id,
                "source_file": source_file,
                "source_page": source_page,
                "source_section": source_section,
                "confidence": result.get("confidence", 0.0),
                "is_safety_critical": result.get("is_safety_critical", False),
            }

            result["citation"] = citation

            # Add citation to content for easy reference
            result["content_with_citation"] = (
                f"{result.get('content', '')}\n\n[Source: {citation_id}]"
            )

            logger.debug(
                f"Added citation {citation_id}: {source_file} "
                f"(page {source_page}, confidence {citation['confidence']:.2f})"
            )

        logger.info(f"Enriched {len(results)} results with citations")

        return results

    def _extract_filename(self, source_path: str) -> str:
        """
        Extract filename from full path.

        Args:
            source_path: Full source path (e.g., "/path/to/manual.pdf")

        Returns:
            Just the filename (e.g., "manual.pdf")
        """
        if not source_path or source_path == "unknown":
            return "unknown"

        # Extract filename from path
        parts = source_path.replace("\\", "/").split("/")
        return parts[-1] if parts else "unknown"

    def generate_citation_summary(self, results: List[Dict]) -> str:
        """
        Generate human-readable citation summary.

        Creates a formatted list of all sources used.

        Example:
        Sources:
        [C1] manual_ah64.pdf, Page 42, Section 3.2.1 (High confidence)
        [C2] safety_guide.pdf, Page 15 (Safety critical)
        [C3] maintenance_log.pdf, Page 8 (Medium confidence)

        Args:
            results: Results with citation metadata

        Returns:
            Formatted citation summary string
        """
        if not results:
            return "No sources cited."

        lines = ["Sources:"]

        for result in results:
            citation = result.get("citation")
            if not citation:
                continue

            citation_id = citation.get("citation_id", "?")
            source_file = citation.get("source_file", "unknown")
            source_page = citation.get("source_page", "?")
            confidence = citation.get("confidence", 0.0)
            is_safety = citation.get("is_safety_critical", False)

            # Build citation line
            line = f"[{citation_id}] {source_file}, Page {source_page}"

            # Add section if available
            source_section = citation.get("source_section")
            if source_section:
                line += f", Section {source_section}"

            # Add metadata
            confidence_level = self._get_confidence_label(confidence)
            if is_safety:
                line += " (Safety critical)"
            else:
                line += f" ({confidence_level} confidence)"

            lines.append(line)

        return "\n".join(lines)

    def _get_confidence_label(self, confidence: float) -> str:
        """
        Get human-readable confidence label.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence label
        """
        if confidence >= 0.75:
            return "High"
        elif confidence >= 0.65:
            return "Medium"
        elif confidence >= 0.50:
            return "Low"
        else:
            return "Very low"

    def validate_response_citations(
        self, llm_response: str, valid_citations: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that LLM response only cites valid sources.

        Checks if LLM used only the citation IDs that were provided
        in the retrieved results.

        Args:
            llm_response: The LLM-generated response text
            valid_citations: List of valid citation IDs (e.g., ["C1", "C2", "C3"])

        Returns:
            {
                'is_valid': bool,
                'cited_ids': List[str],
                'invalid_citations': List[str],
                'missing_citations': List[str],
                'issues': List[str]
            }
        """
        # Extract all citations from response
        citation_pattern = r"\[C(\d+)\]"
        cited_matches = re.findall(citation_pattern, llm_response)
        cited_ids = [f"C{m}" for m in cited_matches]
        cited_ids = list(set(cited_ids))  # Unique citations

        logger.info(f"Validating response citations: {cited_ids}")

        issues = []
        invalid_citations = []
        missing_citations = []

        # Check for invalid citations (cited but not provided)
        for citation_id in cited_ids:
            if citation_id not in valid_citations:
                invalid_citations.append(citation_id)
                issues.append(f"Response cites {citation_id} which is not in provided sources")

        # Check for missing citations (provided but not used)
        # Note: We don't require all sources to be cited, but it's worth noting
        for valid_id in valid_citations:
            if valid_id not in cited_ids and len(valid_citations) <= 5:
                # Only flag if small number of results - large results may legitimately not all be cited
                missing_citations.append(valid_id)

        is_valid = len(invalid_citations) == 0

        result = {
            "is_valid": is_valid,
            "cited_ids": cited_ids,
            "invalid_citations": invalid_citations,
            "missing_citations": missing_citations,
            "issues": issues,
        }

        if issues:
            logger.warning(f"Citation validation failed: {issues}")
        else:
            logger.info(f"Citation validation passed: {len(cited_ids)} citations validated")

        return result

    def extract_citations_from_response(self, llm_response: str) -> List[str]:
        """
        Extract all citation IDs from LLM response.

        Args:
            llm_response: The LLM-generated response

        Returns:
            List of citation IDs found (e.g., ["C1", "C2"])
        """
        citation_pattern = r"\[C(\d+)\]"
        matches = re.findall(citation_pattern, llm_response)
        citations = [f"C{m}" for m in matches]
        return list(set(citations))  # Unique citations

    def get_sources_for_citations(
        self, citation_ids: List[str], results: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Get source information for specific citations.

        Useful for expanding abbreviated citations back to full source details.

        Args:
            citation_ids: List of citation IDs to look up
            results: Original results with citation data

        Returns:
            Dictionary mapping citation_id to source information
        """
        sources = {}

        for result in results:
            citation = result.get("citation")
            if not citation:
                continue

            citation_id = citation.get("citation_id")
            if citation_id in citation_ids:
                sources[citation_id] = {
                    "source_file": citation.get("source_file"),
                    "source_page": citation.get("source_page"),
                    "source_section": citation.get("source_section"),
                    "confidence": citation.get("confidence"),
                    "is_safety_critical": citation.get("is_safety_critical"),
                    "content_preview": result.get("content", "")[:100],
                }

        return sources

    def add_citations_to_prompt(
        self, query: str, results: List[Dict], system_prompt: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Prepare enriched prompt with citations for LLM.

        Creates three components:
        1. System prompt with citation instructions
        2. Retrieved context with citations
        3. User query

        Args:
            query: User's original query
            results: Retrieved results with citations
            system_prompt: Optional custom system prompt

        Returns:
            (system_prompt, context, user_query)
        """
        # Default system prompt with citation instructions
        if not system_prompt:
            system_prompt = """You are a helpful assistant answering questions about technical documentation.

When providing information, always cite your sources using [C1], [C2], etc. format.
For example: "According to the maintenance manual [C1], you should..."

Always cite the sources that support your answer. If information is from multiple sources, cite all of them.
Never cite sources that are not provided in the context."""

        # Build context with citations
        context_lines = ["## Retrieved Context:\n"]

        for result in results:
            citation = result.get("citation")
            if not citation:
                continue

            citation_id = citation.get("citation_id", "?")
            source_file = citation.get("source_file", "unknown")
            source_page = citation.get("source_page", "?")
            content = result.get("content", "")

            context_lines.append(f"\n[{citation_id}] ({source_file}, Page {source_page}):")
            context_lines.append(f"{content}\n")

        context = "".join(context_lines)

        # User query
        user_query = f"Question: {query}"

        return system_prompt, context, user_query

    def log_citation_analysis(self, results: List[Dict]) -> None:
        """
        Log detailed citation analysis.

        Args:
            results: Results with citation metadata
        """
        if not results:
            return

        logger.info("=" * 60)
        logger.info("CITATION ANALYSIS:")
        logger.info(f"  Total citations: {len(results)}")

        # Count by source file
        sources = {}
        for result in results:
            citation = result.get("citation")
            if citation:
                source = citation.get("source_file", "unknown")
                sources[source] = sources.get(source, 0) + 1

        logger.info("  Sources cited:")
        for source, count in sorted(sources.items(), key=lambda x: -x[1]):
            logger.info(f"    - {source}: {count} result(s)")

        # Safety critical count
        safety_count = sum(
            1 for r in results if r.get("citation", {}).get("is_safety_critical", False)
        )
        logger.info(f"  Safety-critical sources: {safety_count}")

        logger.info("=" * 60)
