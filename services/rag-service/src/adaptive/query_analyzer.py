"""
Query analysis module for classification and complexity detection.

Analyzes queries to determine type, complexity, and appropriate
retrieval strategy.
"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes queries for type and complexity."""

    # Query type indicators
    QUESTION_PATTERNS = {
        "what": r"what\s+is|what\s+are|what\s+does",
        "how": r"how\s+do|how\s+can|how\s+to",
        "why": r"why\s+is|why\s+are|why\s+do",
        "when": r"when\s+is|when\s+do|when\s+should",
        "where": r"where\s+is|where\s+are|where\s+do",
        "who": r"who\s+is|who\s+are|who\s+was",
        "comparison": r"difference\s+between|compare|vs|versus",
        "procedure": r"procedure|steps|process|instructions",
        "specification": r"specification|spec|requirement|standard",
        "troubleshooting": r"troubleshoot|problem|issue|error|fail",
    }

    def __init__(self):
        """Initialize query analyzer."""
        pass

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query for type, complexity, and characteristics.

        Args:
            query: The query text

        Returns:
            {
                'query_type': str (procedure/specification/troubleshooting/etc),
                'complexity': str (SIMPLE/MODERATE/COMPLEX),
                'is_multi_part': bool,
                'has_technical_terms': bool,
                'word_count': int,
                'estimated_answer_length': str (SHORT/MEDIUM/LONG),
                'recommended_retrieval_strategy': str
            }
        """
        query_lower = query.lower()

        # Determine query type
        query_type = self._classify_query_type(query_lower)

        # Check complexity
        complexity = self._assess_complexity(query)

        # Check if multi-part (e.g., "what and how")
        is_multi_part = self._is_multi_part_query(query_lower)

        # Check for technical terms
        has_technical = self._has_technical_terms(query)

        # Word count
        word_count = len(query.split())

        # Estimate answer length
        answer_length = self._estimate_answer_length(query, word_count)

        # Recommend strategy
        recommended_strategy = self._recommend_strategy(
            query_type, complexity, is_multi_part
        )

        result = {
            "query_type": query_type,
            "complexity": complexity,
            "is_multi_part": is_multi_part,
            "has_technical_terms": has_technical,
            "word_count": word_count,
            "estimated_answer_length": answer_length,
            "recommended_retrieval_strategy": recommended_strategy,
        }

        logger.debug(f"Query analysis: {result}")
        return result

    def _classify_query_type(self, query_lower: str) -> str:
        """
        Classify query by type.

        Args:
            query_lower: Lowercased query

        Returns:
            Query type string
        """
        for query_type, pattern in self.QUESTION_PATTERNS.items():
            if re.search(pattern, query_lower):
                return query_type

        # Default
        return "general"

    def _assess_complexity(self, query: str) -> str:
        """
        Assess query complexity.

        SIMPLE: Short, direct, single aspect
        MODERATE: Medium length, 1-2 aspects
        COMPLEX: Long, multiple aspects, technical

        Args:
            query: Query text

        Returns:
            Complexity level
        """
        word_count = len(query.split())
        conjunction_count = len(re.findall(r'\b(and|or|but|however)\b', query.lower()))
        question_count = len(re.findall(r'\?', query))

        # Scoring
        complexity_score = 0

        # Word count factor
        if word_count < 10:
            complexity_score += 1
        elif word_count < 20:
            complexity_score += 2
        else:
            complexity_score += 3

        # Conjunction factor (indicates multiple parts)
        complexity_score += conjunction_count

        # Question factor
        complexity_score += question_count * 2

        if complexity_score <= 2:
            return "SIMPLE"
        elif complexity_score <= 4:
            return "MODERATE"
        else:
            return "COMPLEX"

    def _is_multi_part_query(self, query_lower: str) -> bool:
        """
        Check if query has multiple parts.

        Args:
            query_lower: Lowercased query

        Returns:
            True if multi-part
        """
        # Multiple question marks or "and"/"or" with different subjects
        if query_lower.count("?") > 1:
            return True

        if re.search(r'\b(and|or)\b.*\b(how|what|why|when|where|who)\b', query_lower):
            return True

        return False

    def _has_technical_terms(self, query: str) -> bool:
        """
        Check if query contains technical terms.

        Args:
            query: Query text

        Returns:
            True if has technical terms
        """
        technical_indicators = [
            r"\d+\s*(rpm|psi|nm|hp|db|khz|mhz|ghz|gb|mb|kb)",
            r"\b(torque|pressure|rpm|amperage|voltage|frequency)\b",
            r"\b(algorithm|function|interface|protocol|bandwidth)\b",
            r"[A-Z]{2,}",  # Acronyms
        ]

        for pattern in technical_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                return True

        return False

    def _estimate_answer_length(self, query: str, word_count: int) -> str:
        """
        Estimate expected answer length.

        Args:
            query: Query text
            word_count: Word count of query

        Returns:
            Answer length estimate
        """
        # Procedure/process queries need longer answers
        if re.search(r"(procedure|steps|process|how.*to)", query.lower()):
            return "LONG"

        # Simple questions get short answers
        if word_count < 10 and not self._is_multi_part_query(query.lower()):
            return "SHORT"

        # Default
        return "MEDIUM"

    def _recommend_strategy(
        self, query_type: str, complexity: str, is_multi_part: bool
    ) -> str:
        """
        Recommend retrieval strategy based on query analysis.

        STANDARD: Direct hybrid search
        EXPANDED: Add synonyms (for low-specificity queries)
        DECOMPOSED: Break into sub-queries (for complex queries)
        FALLBACK: Expand + lower threshold (for very difficult queries)

        Args:
            query_type: Classified query type
            complexity: Complexity level
            is_multi_part: Whether multi-part

        Returns:
            Recommended strategy
        """
        # Complex, multi-part queries benefit from decomposition
        if is_multi_part and complexity in ["MODERATE", "COMPLEX"]:
            return "DECOMPOSED"

        # Complex queries benefit from expansion
        if complexity == "COMPLEX":
            return "EXPANDED"

        # Default strategy for simple/moderate single-part queries
        return "STANDARD"

    def log_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Log query analysis results.

        Args:
            analysis: Analysis result dict
        """
        logger.debug("=" * 60)
        logger.debug("QUERY ANALYSIS:")
        logger.debug(f"  Type: {analysis.get('query_type')}")
        logger.debug(f"  Complexity: {analysis.get('complexity')}")
        logger.debug(f"  Multi-part: {analysis.get('is_multi_part')}")
        logger.debug(f"  Technical terms: {analysis.get('has_technical_terms')}")
        logger.debug(f"  Word count: {analysis.get('word_count')}")
        logger.debug(f"  Answer length: {analysis.get('estimated_answer_length')}")
        logger.debug(f"  Recommended strategy: {analysis.get('recommended_retrieval_strategy')}")
        logger.debug("=" * 60)
