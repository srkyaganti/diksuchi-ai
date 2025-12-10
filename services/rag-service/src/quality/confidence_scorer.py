"""
Confidence scoring and quality threshold enforcement.

Assigns confidence scores to retrieval results based on multiple signals
and enforces minimum thresholds. Prevents low-quality context from reaching LLM.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Computes and enforces confidence scores for retrieval results."""

    # Defense-grade confidence thresholds
    CONFIDENCE_THRESHOLD_HIGH = 0.75  # High confidence - suitable for primary answers
    CONFIDENCE_THRESHOLD_MEDIUM = 0.65  # Medium confidence - for supplementary info
    CONFIDENCE_THRESHOLD_LOW = 0.50  # Minimum threshold to include

    # Source type confidence boosts
    SOURCE_BOOSTS = {
        "graph_expansion": 0.15,  # High confidence in knowledge graph items
        "vector": 0.10,  # Good confidence in semantic search
        "keyword": 0.05,  # Lower confidence for pure keyword matches
    }

    # Safety content confidence boost
    SAFETY_BOOST = 0.10

    def compute_confidence(self, result: Dict) -> float:
        """
        Compute confidence score based on multiple signals.

        Signals:
        1. Base retrieval score (vector similarity, BM25, etc.)
        2. Source type (graph > vector > keyword)
        3. Safety classification (safety items get boost)
        4. Metadata completeness (source, page, section present)

        Args:
            result: Retrieval result from hybrid search

        Returns:
            Confidence score (0.0-1.0)
        """
        # Base score from retrieval
        base_score = result.get("score", 0.0)

        # Source type boost
        source = result.get("source", "unknown")
        source_boost = self.SOURCE_BOOSTS.get(source, 0.0)

        # Safety content boost
        safety_boost = self.SAFETY_BOOST if result.get("is_safety_critical", False) else 0.0

        # Metadata completeness score
        metadata_score = self._score_metadata(result.get("metadata", {}))

        # Combine all signals
        confidence = min(
            1.0, base_score + source_boost + safety_boost + (metadata_score * 0.05)
        )

        return confidence

    def _score_metadata(self, metadata: Dict) -> float:
        """
        Score metadata completeness (0-1).

        Checks for presence of important metadata fields:
        - source (file path)
        - fileId (document ID)

        Args:
            metadata: Metadata dict from result

        Returns:
            Metadata completeness score (0-1)
        """
        required_fields = ["source", "fileId"]
        present = sum(1 for f in required_fields if metadata.get(f))
        return present / len(required_fields) if required_fields else 1.0

    def filter_by_confidence(
        self, results: List[Dict], min_confidence: float = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Split results into confident vs uncertain.

        Args:
            results: Retrieval results
            min_confidence: Minimum confidence threshold
                          (defaults to CONFIDENCE_THRESHOLD_MEDIUM)

        Returns:
            Tuple of (confident_results, uncertain_results)
            Each result includes 'confidence' field
        """
        if min_confidence is None:
            min_confidence = self.CONFIDENCE_THRESHOLD_MEDIUM

        confident = []
        uncertain = []

        logger.info(
            f"Filtering results by confidence (threshold: {min_confidence:.2f})"
        )

        for result in results:
            # Compute confidence score
            confidence = self.compute_confidence(result)
            result["confidence"] = confidence

            # Split by threshold
            if confidence >= min_confidence:
                confident.append(result)
            else:
                uncertain.append(result)

        logger.info(
            f"Confidence filtering: {len(confident)} confident, "
            f"{len(uncertain)} uncertain (below {min_confidence:.2f})"
        )

        return confident, uncertain

    def get_confidence_level(self, confidence: float) -> str:
        """
        Get human-readable confidence level.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence level string
        """
        if confidence >= self.CONFIDENCE_THRESHOLD_HIGH:
            return "HIGH"
        elif confidence >= self.CONFIDENCE_THRESHOLD_MEDIUM:
            return "MEDIUM"
        elif confidence >= self.CONFIDENCE_THRESHOLD_LOW:
            return "LOW"
        else:
            return "VERY_LOW"

    def add_confidence_to_results(self, results: List[Dict]) -> List[Dict]:
        """
        Add confidence score and level to all results.

        Args:
            results: Retrieval results

        Returns:
            Results with 'confidence' and 'confidence_level' fields
        """
        for result in results:
            if "confidence" not in result:
                result["confidence"] = self.compute_confidence(result)

            result["confidence_level"] = self.get_confidence_level(
                result["confidence"]
            )

        return results

    def log_confidence_analysis(self, results: List[Dict]) -> None:
        """
        Log detailed confidence analysis of results.

        Useful for debugging and monitoring result quality.
        """
        if not results:
            return

        confidences = [r.get("confidence", 0.0) for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        logger.info("=" * 60)
        logger.info("CONFIDENCE ANALYSIS:")
        logger.info(f"  Average: {avg_confidence:.3f}")
        logger.info(f"  Range: {min_confidence:.3f} - {max_confidence:.3f}")
        logger.info(f"  Total results: {len(results)}")

        # Breakdown by confidence level
        high = sum(1 for r in results if r.get("confidence_level") == "HIGH")
        medium = sum(1 for r in results if r.get("confidence_level") == "MEDIUM")
        low = sum(1 for r in results if r.get("confidence_level") == "LOW")
        very_low = sum(1 for r in results if r.get("confidence_level") == "VERY_LOW")

        logger.info(f"  HIGH ({self.CONFIDENCE_THRESHOLD_HIGH}+): {high}")
        logger.info(f"  MEDIUM ({self.CONFIDENCE_THRESHOLD_MEDIUM:.2f}+): {medium}")
        logger.info(f"  LOW ({self.CONFIDENCE_THRESHOLD_LOW:.2f}+): {low}")
        logger.info(f"  VERY_LOW (<{self.CONFIDENCE_THRESHOLD_LOW:.2f}): {very_low}")
        logger.info("=" * 60)

        # Log individual results
        for i, result in enumerate(results[:5], 1):
            score = result.get("confidence", 0.0)
            level = result.get("confidence_level", "?")
            source = result.get("source", "?")
            preview = result.get("content", "")[:50]
            logger.debug(f"  [{i}] {level:8} {score:.3f} | {source:8} | {preview}...")
