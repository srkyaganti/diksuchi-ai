"""
Query expansion module for synonym and related term expansion.

Expands queries with synonyms and related terms to improve retrieval
when initial results are low-confidence.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class QueryExpander:
    """Expands queries with synonyms and related terms."""

    # Domain-specific synonyms for defense/technical documents
    TECHNICAL_SYNONYMS = {
        "maintenance": ["servicing", "upkeep", "service", "inspection"],
        "procedure": ["process", "steps", "method", "instructions"],
        "specification": ["spec", "requirement", "standard", "parameter"],
        "warning": ["caution", "alert", "danger", "risk"],
        "tool": ["equipment", "instrument", "device"],
        "pressure": ["psi", "bar", "force", "stress"],
        "torque": ["rotational force", "moment", "rotation"],
        "rotor": ["rotating element", "blade", "assembly"],
        "hydraulic": ["fluid", "pressure", "system"],
        "failure": ["malfunction", "breakdown", "fault"],
        "troubleshoot": ["diagnose", "debug", "investigate"],
        "initialize": ["start", "boot", "prepare", "setup"],
        "configuration": ["setup", "settings", "parameters"],
        "calibration": ["adjustment", "tuning", "alignment"],
    }

    # Abbreviations and full forms
    ABBREVIATIONS = {
        "psi": "pounds per square inch",
        "rpm": "revolutions per minute",
        "nm": "newton meter",
        "hp": "horsepower",
        "db": "decibel",
        "s1000d": "specification for technical publications",
        "lru": "line replaceable unit",
        "cru": "component replaceable unit",
    }

    def __init__(self):
        """Initialize query expander."""
        pass

    def expand_query(self, query: str, num_variants: int = 3) -> List[str]:
        """
        Expand query with synonyms and related terms.

        Returns list of query variants to try.

        Args:
            query: Original query
            num_variants: Number of expanded variants to generate

        Returns:
            List of expanded query variants
        """
        variants = [query]  # Include original

        # Try synonym-based expansion
        synonym_variant = self._expand_with_synonyms(query)
        if synonym_variant and synonym_variant != query:
            variants.append(synonym_variant)

        # Try abbreviation expansion
        abbrev_variant = self._expand_abbreviations(query)
        if abbrev_variant and abbrev_variant != query:
            variants.append(abbrev_variant)

        # Try combined expansion
        if len(variants) < num_variants:
            combined = self._combined_expansion(query)
            if combined and combined != query:
                variants.append(combined)

        # Return unique variants up to requested count
        unique_variants = []
        seen = set()
        for v in variants:
            if v not in seen:
                unique_variants.append(v)
                seen.add(v)
            if len(unique_variants) >= num_variants:
                break

        logger.debug(f"Generated {len(unique_variants)} query variants")
        return unique_variants

    def _expand_with_synonyms(self, query: str) -> str:
        """
        Expand query by replacing words with synonyms.

        Replaces first applicable word with a synonym.

        Args:
            query: Original query

        Returns:
            Expanded query or original if no synonyms found
        """
        query_lower = query.lower()

        for word, synonyms in self.TECHNICAL_SYNONYMS.items():
            if word in query_lower:
                # Replace with first synonym
                expanded = query_lower.replace(word, synonyms[0])
                logger.debug(f"Synonym expansion: '{word}' -> '{synonyms[0]}'")
                return expanded

        return query

    def _expand_abbreviations(self, query: str) -> str:
        """
        Expand abbreviations in query.

        Replaces abbreviations with full forms.

        Args:
            query: Original query

        Returns:
            Expanded query
        """
        query_lower = query.lower()
        expanded = query

        for abbrev, full_form in self.ABBREVIATIONS.items():
            if abbrev in query_lower:
                expanded = expanded.replace(abbrev, full_form)
                logger.debug(f"Abbreviation expansion: '{abbrev}' -> '{full_form}'")
                break  # Only expand one abbreviation

        return expanded

    def _combined_expansion(self, query: str) -> str:
        """
        Combine multiple expansion strategies.

        Applies both synonyms and abbreviations.

        Args:
            query: Original query

        Returns:
            Expanded query
        """
        # First expand synonyms
        expanded = self._expand_with_synonyms(query)

        # Then expand abbreviations
        expanded = self._expand_abbreviations(expanded)

        return expanded

    def add_related_terms(self, query: str) -> str:
        """
        Add related terms at end of query.

        Useful for broadening search without changing existing terms.

        Args:
            query: Original query

        Returns:
            Query with additional related terms
        """
        query_lower = query.lower()
        related_terms = []

        # Find applicable synonyms and add them
        for word, synonyms in self.TECHNICAL_SYNONYMS.items():
            if word in query_lower:
                # Add 1-2 related synonyms
                related_terms.extend(synonyms[:2])
                break

        if related_terms:
            expanded = f"{query} ({' '.join(related_terms)})"
            logger.debug(f"Added related terms: {' '.join(related_terms)}")
            return expanded

        return query

    def log_expansion(self, original: str, variants: List[str]) -> None:
        """
        Log query expansion results.

        Args:
            original: Original query
            variants: Generated variants
        """
        logger.debug("=" * 60)
        logger.debug("QUERY EXPANSION:")
        logger.debug(f"  Original: {original}")
        logger.debug(f"  Variants ({len(variants)}):")
        for i, variant in enumerate(variants[1:], 1):
            logger.debug(f"    [{i}] {variant}")
        logger.debug("=" * 60)
