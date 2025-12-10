"""
Safety information preservation module.

Ensures safety warnings, cautions, and required tools are never demoted
in ranking. Critical for defense manuals where safety info must always be visible.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SafetyPreserver:
    """Protects safety-critical information from being demoted by reranking."""

    # Safety information sources - should never be demoted
    SAFETY_SOURCE_TYPES = ["graph_expansion"]

    # Keywords indicating safety-critical content
    SAFETY_KEYWORDS = [
        "WARNING",
        "CAUTION",
        "DANGER",
        "REQUIRED TOOL",
        "SAFETY",
        "HAZARD",
        "RISK",
        "INJURY",
        "EXPLOSION",
        "FIRE",
        "TOXIC",
        "ELECTRICAL",
        "PRESSURE",
    ]

    # Minimum score for safety content (forces high ranking)
    MINIMUM_SAFETY_SCORE = 0.95

    def mark_safety_content(self, results: List[Dict]) -> List[Dict]:
        """
        Mark results containing safety information.

        Identifies safety-critical content by:
        1. Source type (graph_expansion = knowledge graph safety warnings)
        2. Content keywords (WARNING, DANGER, CAUTION, etc.)

        Args:
            results: Retrieval results from hybrid search

        Returns:
            Results with 'is_safety_critical' flag added/updated
        """
        for result in results:
            # Check if from knowledge graph (explicit safety)
            is_from_graph = result.get("source") in self.SAFETY_SOURCE_TYPES

            # Check content for safety keywords
            content = result.get("content", "").upper()
            has_safety_keyword = any(kw in content for kw in self.SAFETY_KEYWORDS)

            # Mark as safety critical if either condition is true
            is_safety = is_from_graph or has_safety_keyword

            result["is_safety_critical"] = is_safety

            if is_safety:
                logger.debug(f"Marked as safety-critical: {result.get('id', '?')}")

        return results

    def protect_safety_ranking(
        self, results: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        """
        Ensure safety-critical items appear in top-k results.

        Strategy:
        1. Separate safety-critical from normal results
        2. Boost safety item scores to minimum threshold
        3. Combine safety-first (safety items first, then normal)
        4. Return expanded pool for downstream processing

        Args:
            results: Retrieval results (should be marked with is_safety_critical)
            top_k: Target number of results for final output

        Returns:
            Protected results with safety items in prominent positions
        """
        safety_results = [r for r in results if r.get("is_safety_critical", False)]
        normal_results = [r for r in results if not r.get("is_safety_critical", False)]

        logger.info(
            f"Safety preservation: {len(safety_results)} safety items, {len(normal_results)} normal items"
        )

        # Boost safety scores to prevent future demotion
        for result in safety_results:
            original_score = result.get("score", 0.0)
            boosted_score = max(original_score, self.MINIMUM_SAFETY_SCORE)

            if boosted_score > original_score:
                result["score"] = boosted_score
                result["score_boosted"] = True
                result["original_score"] = original_score

                logger.debug(
                    f"Boosted safety score: {original_score:.3f} → {boosted_score:.3f}"
                )

        # Combine: Safety items first, then normal items
        # This ensures safety warnings appear early in results
        protected_results = safety_results + normal_results

        # Return expanded pool (2x top_k) to give reranker room to work
        # but with safety items guaranteed in top positions
        return protected_results[: top_k * 2]

    def ensure_safety_in_final_results(
        self, results: List[Dict], min_safety_items: int = 1
    ) -> Dict[str, Any]:
        """
        Validate that final results contain minimum safety items.

        Args:
            results: Final retrieval results
            min_safety_items: Minimum number of safety items to require

        Returns:
            {
                'has_sufficient_safety': bool,
                'safety_count': int,
                'safety_items': List[Dict],
                'warning': str if insufficient
            }
        """
        safety_items = [r for r in results if r.get("is_safety_critical", False)]
        safety_count = len(safety_items)
        has_sufficient = safety_count >= min_safety_items

        result = {
            "has_sufficient_safety": has_sufficient,
            "safety_count": safety_count,
            "safety_items": safety_items,
        }

        if not has_sufficient:
            warning = (
                f"WARNING: Only {safety_count} safety item(s) in results "
                f"(expected at least {min_safety_items})"
            )
            result["warning"] = warning
            logger.warning(warning)

        return result

    def log_safety_analysis(self, results: List[Dict]) -> None:
        """
        Log detailed safety analysis of results.

        Useful for debugging and monitoring safety preservation.
        """
        safety_items = [r for r in results if r.get("is_safety_critical", False)]
        normal_items = [r for r in results if not r.get("is_safety_critical", False)]

        if safety_items:
            logger.info("=" * 60)
            logger.info("SAFETY ITEMS IN RESULTS:")
            for i, item in enumerate(safety_items, 1):
                score = item.get("score", 0.0)
                boosted = item.get("score_boosted", False)
                source = item.get("source", "unknown")
                content_preview = item.get("content", "")[:60]
                logger.info(
                    f"  [{i}] Score: {score:.3f}{'*' if boosted else ''} | "
                    f"Source: {source} | {content_preview}..."
                )
            logger.info("=" * 60)

        if normal_items:
            logger.debug(f"Normal items in results: {len(normal_items)}")
