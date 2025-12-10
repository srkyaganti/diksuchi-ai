"""
Context conflict detection module.

Detects contradictory information in retrieved context.
Critical for preventing LLM from seeing conflicting instructions.
"""

import logging
from typing import List, Dict, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Identifies contradictory information in retrieval results."""

    # Threshold for considering content semantically similar
    # Higher = more conservative (fewer false positives)
    CONTRADICTION_THRESHOLD = 0.85

    # Keywords indicating negation/contradiction
    NEGATION_PATTERNS = [
        ("do not", "do "),
        ("never", "always"),
        ("don't", "do "),
        ("prohibited", "required"),
        ("forbidden", "must"),
        ("avoid", "use"),
        ("restrict", "allow"),
        ("cannot", "can "),
        ("unable", "able"),
        ("no", "yes"),
    ]

    def __init__(self, embedding_model=None):
        """
        Initialize conflict detector.

        Args:
            embedding_model: Optional pre-loaded embedding model for similarity
                           If None, conflict detection uses pattern-based method only
        """
        self.embedding_model = embedding_model
        self.use_embeddings = embedding_model is not None

    def detect_conflicts(self, results: List[Dict]) -> List[Tuple[int, int, float]]:
        """
        Find pairs of results that may contradict each other.

        Strategy:
        1. For each pair of results, check for negation patterns
        2. If embedding model available, compute semantic similarity
        3. Flag high similarity + negation as conflict

        Args:
            results: List of retrieval results

        Returns:
            List of (index1, index2, conflict_score) tuples
        """
        if len(results) < 2:
            return []

        conflicts = []

        # Extract content
        contents = [r.get("content", "") for r in results]

        # Check all pairs
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                conflict_score = self._check_pair_conflict(
                    contents[i], contents[j]
                )

                if conflict_score > 0:
                    conflicts.append((i, j, conflict_score))
                    logger.warning(
                        f"Potential conflict detected between result {i} and {j} "
                        f"(score: {conflict_score:.3f})"
                    )

        return conflicts

    def _check_pair_conflict(self, text1: str, text2: str) -> float:
        """
        Check if two texts potentially contradict each other.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Conflict score (0.0 = no conflict, 1.0 = definite conflict)
        """
        # Check for explicit negation patterns
        negation_score = self._check_negation_patterns(text1, text2)

        if negation_score > 0.7:
            # High confidence contradiction detected
            return negation_score

        # If embedding model available, check semantic similarity
        if self.use_embeddings:
            similarity_score = self._check_semantic_contradiction(text1, text2)
            return max(negation_score, similarity_score)

        return negation_score

    def _check_negation_patterns(self, text1: str, text2: str) -> float:
        """
        Check for opposite negation patterns in texts.

        Pattern matching for contradictions like:
        - "do not use X" vs "use X"
        - "never" vs "always"
        - "forbidden" vs "required"

        Args:
            text1: First text
            text2: Second text

        Returns:
            Contradiction score (0-1)
        """
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        contradiction_count = 0
        total_patterns = 0

        for neg_term, pos_term in self.NEGATION_PATTERNS:
            neg_in_t1 = neg_term in text1_lower
            pos_in_t1 = pos_term in text1_lower
            neg_in_t2 = neg_term in text2_lower
            pos_in_t2 = pos_term in text2_lower

            # Check for opposing terms
            if (neg_in_t1 and pos_in_t2) or (pos_in_t1 and neg_in_t2):
                contradiction_count += 1
                total_patterns += 1
            elif neg_in_t1 or pos_in_t1 or neg_in_t2 or pos_in_t2:
                total_patterns += 1

        if total_patterns == 0:
            return 0.0

        # Normalize score
        return min(1.0, contradiction_count / total_patterns)

    def _check_semantic_contradiction(self, text1: str, text2: str) -> float:
        """
        Check semantic contradiction using embeddings.

        If texts are semantically very similar AND have negation patterns,
        they likely contradict.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Contradiction score (0-1)
        """
        if not self.use_embeddings:
            return 0.0

        try:
            from sentence_transformers import util

            # Encode texts
            emb1 = self.embedding_model.encode(text1, convert_to_tensor=True)
            emb2 = self.embedding_model.encode(text2, convert_to_tensor=True)

            # Compute similarity
            similarity = util.pytorch_cos_sim(emb1, emb2).item()

            # High similarity + negation patterns = conflict
            if similarity > self.CONTRADICTION_THRESHOLD:
                negation_score = self._check_negation_patterns(text1, text2)
                return similarity * 0.5 + negation_score * 0.5

            return 0.0

        except Exception as e:
            logger.error(f"Error in semantic contradiction check: {e}")
            return 0.0

    def resolve_conflicts(
        self, results: List[Dict], conflicts: List[Tuple[int, int, float]]
    ) -> List[Dict]:
        """
        Resolve conflicts by keeping higher-confidence result.

        Strategy:
        1. For each conflicting pair, keep the one with higher confidence
        2. Mark kept result with conflict warning
        3. Remove lower-confidence conflicting result

        Args:
            results: List of retrieval results
            conflicts: List of (idx1, idx2, score) conflict tuples

        Returns:
            Results with conflicts resolved
        """
        if not conflicts:
            return results

        to_remove = set()

        for i, j, score in conflicts:
            result_i = results[i]
            result_j = results[j]

            conf_i = result_i.get("confidence", 0.5)
            conf_j = result_j.get("confidence", 0.5)

            # Remove lower confidence result
            if conf_i >= conf_j:
                to_remove.add(j)
                result_i["has_conflict"] = True
                result_i["conflict_note"] = f"Conflicted with result at index {j}"
                logger.info(
                    f"Conflict resolution: Kept result {i} (conf: {conf_i:.3f}), "
                    f"removed {j} (conf: {conf_j:.3f})"
                )
            else:
                to_remove.add(i)
                result_j["has_conflict"] = True
                result_j["conflict_note"] = f"Conflicted with result at index {i}"
                logger.info(
                    f"Conflict resolution: Kept result {j} (conf: {conf_j:.3f}), "
                    f"removed {i} (conf: {conf_i:.3f})"
                )

        # Filter out removed indices
        filtered_results = [r for idx, r in enumerate(results) if idx not in to_remove]

        logger.info(f"Conflict resolution complete: removed {len(to_remove)} results")

        return filtered_results

    def log_conflict_analysis(
        self, conflicts: List[Tuple[int, int, float]], results: List[Dict]
    ) -> None:
        """
        Log detailed conflict analysis.

        Args:
            conflicts: List of detected conflicts
            results: Original results list
        """
        if not conflicts:
            logger.info("No conflicts detected")
            return

        logger.info("=" * 60)
        logger.info(f"CONFLICT ANALYSIS: {len(conflicts)} conflict(s) detected")

        for i, j, score in conflicts:
            if i < len(results) and j < len(results):
                content_i = results[i].get("content", "")[:60]
                content_j = results[j].get("content", "")[:60]
                logger.info(f"  Conflict {i} <-> {j} (score: {score:.3f})")
                logger.info(f"    [{i}]: {content_i}...")
                logger.info(f"    [{j}]: {content_j}...")

        logger.info("=" * 60)
