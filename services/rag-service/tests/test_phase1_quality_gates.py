"""
Phase 1 & 2 Test Suite: Safety, Confidence, Conflict Detection, and Citations

Tests the core Phase 1 & 2 implementation:
1. Safety preservation
2. Confidence scoring and filtering
3. Conflict detection and resolution
4. Citation tracking and validation
"""

import unittest
from unittest.mock import Mock
from src.quality.safety_preserver import SafetyPreserver
from src.quality.confidence_scorer import ConfidenceScorer
from src.quality.conflict_detector import ConflictDetector
from src.quality.citation_tracker import CitationTracker


class TestSafetyPreserver(unittest.TestCase):
    """Test SafetyPreserver functionality."""

    def setUp(self):
        self.preserver = SafetyPreserver()

    def test_mark_safety_content_from_graph_expansion(self):
        """Test marking safety content from graph_expansion source."""
        results = [
            {
                "id": "1",
                "content": "Normal result",
                "source": "vector",
                "score": 0.8,
            },
            {
                "id": "2",
                "content": "Safety warning",
                "source": "graph_expansion",
                "score": 0.5,
            },
        ]

        marked = self.preserver.mark_safety_content(results)

        self.assertFalse(marked[0].get("is_safety_critical", False))
        self.assertTrue(marked[1].get("is_safety_critical", False))

    def test_mark_safety_content_by_keyword(self):
        """Test marking safety content by keywords."""
        results = [
            {
                "id": "1",
                "content": "WARNING: Risk of explosion if pressure exceeds 300 PSI",
                "source": "vector",
                "score": 0.8,
            },
            {
                "id": "2",
                "content": "CAUTION: Wear protective equipment",
                "source": "vector",
                "score": 0.7,
            },
        ]

        marked = self.preserver.mark_safety_content(results)

        self.assertTrue(marked[0].get("is_safety_critical", False))
        self.assertTrue(marked[1].get("is_safety_critical", False))

    def test_protect_safety_ranking(self):
        """Test that safety items are protected in ranking."""
        results = [
            {
                "id": "1",
                "content": "Normal result",
                "source": "vector",
                "score": 0.9,
                "is_safety_critical": False,
            },
            {
                "id": "2",
                "content": "WARNING",
                "source": "graph_expansion",
                "score": 0.3,
                "is_safety_critical": True,
            },
        ]

        protected = self.preserver.protect_safety_ranking(results, top_k=5)

        # Safety item should be first
        self.assertTrue(protected[0].get("is_safety_critical", False))
        self.assertTrue(protected[0]["score"] >= self.preserver.MINIMUM_SAFETY_SCORE)

    def test_ensure_safety_in_final_results(self):
        """Test safety item presence validation."""
        results = [
            {
                "id": "1",
                "content": "WARNING",
                "is_safety_critical": True,
            },
            {
                "id": "2",
                "content": "Normal",
                "is_safety_critical": False,
            },
        ]

        validation = self.preserver.ensure_safety_in_final_results(results, min_safety_items=1)

        self.assertTrue(validation["has_sufficient_safety"])
        self.assertEqual(validation["safety_count"], 1)

    def test_insufficient_safety_in_final_results(self):
        """Test warning when safety items are missing."""
        results = [
            {
                "id": "1",
                "content": "Normal result",
                "is_safety_critical": False,
            }
        ]

        validation = self.preserver.ensure_safety_in_final_results(results, min_safety_items=1)

        self.assertFalse(validation["has_sufficient_safety"])
        self.assertIn("warning", validation)


class TestConfidenceScorer(unittest.TestCase):
    """Test ConfidenceScorer functionality."""

    def setUp(self):
        self.scorer = ConfidenceScorer()

    def test_compute_confidence_basic(self):
        """Test basic confidence scoring."""
        result = {
            "id": "1",
            "content": "Test",
            "source": "vector",
            "score": 0.8,
            "metadata": {"source": "manual.pdf", "fileId": "123"},
        }

        confidence = self.scorer.compute_confidence(result)

        # Should be > 0.8 due to boosts
        self.assertGreater(confidence, 0.8)

    def test_confidence_with_safety_boost(self):
        """Test that safety items get confidence boost."""
        result_normal = {
            "id": "1",
            "content": "Test",
            "source": "vector",
            "score": 0.8,
            "is_safety_critical": False,
            "metadata": {"source": "manual.pdf", "fileId": "123"},
        }

        result_safety = {
            "id": "2",
            "content": "WARNING",
            "source": "vector",
            "score": 0.8,
            "is_safety_critical": True,
            "metadata": {"source": "manual.pdf", "fileId": "123"},
        }

        conf_normal = self.scorer.compute_confidence(result_normal)
        conf_safety = self.scorer.compute_confidence(result_safety)

        # Safety should have higher confidence
        self.assertGreater(conf_safety, conf_normal)

    def test_filter_by_confidence(self):
        """Test filtering results by confidence threshold."""
        results = [
            {
                "id": "1",
                "content": "High quality",
                "source": "graph_expansion",
                "score": 0.9,
                "is_safety_critical": True,
                "metadata": {"source": "manual.pdf", "fileId": "123"},
            },
            {
                "id": "2",
                "content": "Low quality",
                "source": "keyword",
                "score": 0.3,
                "is_safety_critical": False,
                "metadata": {"source": "manual.pdf", "fileId": "123"},
            },
        ]

        confident, uncertain = self.scorer.filter_by_confidence(
            results, min_confidence=0.65
        )

        self.assertEqual(len(confident), 1)
        self.assertEqual(len(uncertain), 1)
        self.assertEqual(confident[0]["id"], "1")

    def test_get_confidence_level(self):
        """Test confidence level classification."""
        self.assertEqual(self.scorer.get_confidence_level(0.8), "HIGH")
        self.assertEqual(self.scorer.get_confidence_level(0.7), "MEDIUM")
        self.assertEqual(self.scorer.get_confidence_level(0.55), "LOW")
        self.assertEqual(self.scorer.get_confidence_level(0.3), "VERY_LOW")


class TestConflictDetector(unittest.TestCase):
    """Test ConflictDetector functionality."""

    def setUp(self):
        self.detector = ConflictDetector(embedding_model=None)

    def test_detect_conflicts_negation_patterns(self):
        """Test conflict detection using negation patterns."""
        results = [
            {
                "id": "1",
                "content": "The oil is prohibited in the hydraulic system",
                "source": "vector",
                "score": 0.8,
            },
            {
                "id": "2",
                "content": "The oil is required for better performance",
                "source": "vector",
                "score": 0.7,
            },
        ]

        conflicts = self.detector.detect_conflicts(results)

        # Should detect conflict between "prohibited" and "required"
        self.assertGreater(len(conflicts), 0)

    def test_no_conflicts_similar_content(self):
        """Test that similar non-contradictory content is not flagged."""
        results = [
            {
                "id": "1",
                "content": "The maintenance procedure requires inspection",
                "source": "vector",
                "score": 0.8,
            },
            {
                "id": "2",
                "content": "Maintenance requires careful inspection",
                "source": "vector",
                "score": 0.7,
            },
        ]

        conflicts = self.detector.detect_conflicts(results)

        # Should have minimal or no conflicts
        self.assertEqual(len(conflicts), 0)

    def test_resolve_conflicts_keeps_higher_confidence(self):
        """Test that conflict resolution keeps higher-confidence result."""
        results = [
            {
                "id": "1",
                "content": "Torque to 50 Nm",
                "source": "vector",
                "score": 0.9,
                "confidence": 0.8,
            },
            {
                "id": "2",
                "content": "Torque to 100 Nm",
                "source": "keyword",
                "score": 0.5,
                "confidence": 0.4,
            },
        ]

        conflicts = [(0, 1, 0.9)]
        resolved = self.detector.resolve_conflicts(results, conflicts)

        # Should keep result with ID "1" (higher confidence)
        ids = [r["id"] for r in resolved]
        self.assertIn("1", ids)
        self.assertNotIn("2", ids)

    def test_empty_results(self):
        """Test handling of empty results."""
        conflicts = self.detector.detect_conflicts([])
        self.assertEqual(len(conflicts), 0)

    def test_single_result(self):
        """Test handling of single result."""
        results = [{"id": "1", "content": "Test", "source": "vector"}]
        conflicts = self.detector.detect_conflicts(results)
        self.assertEqual(len(conflicts), 0)


class TestPhase1Integration(unittest.TestCase):
    """Integration tests for Phase 1 quality gates."""

    def setUp(self):
        self.preserver = SafetyPreserver()
        self.scorer = ConfidenceScorer()
        self.detector = ConflictDetector(embedding_model=None)

    def test_phase1_full_pipeline(self):
        """Test complete Phase 1 pipeline on realistic data."""
        # Simulate retrieval results
        raw_results = [
            {
                "id": "doc1",
                "content": "Maintenance procedures for rotor assembly",
                "source": "vector",
                "score": 0.85,
                "metadata": {"source": "manual.pdf", "fileId": "f1"},
            },
            {
                "id": "doc2",
                "content": "WARNING: Risk of rotor imbalance causing vibration",
                "source": "graph_expansion",
                "score": 0.5,
                "metadata": {"source": "safety_guide.pdf", "fileId": "f2"},
            },
            {
                "id": "doc3",
                "content": "Use synthetic grease for bearing lubrication",
                "source": "keyword",
                "score": 0.6,
                "metadata": {"source": "manual.pdf", "fileId": "f1"},
            },
        ]

        # Step 1: Mark safety content
        marked = self.preserver.mark_safety_content(raw_results)
        self.assertTrue(marked[1].get("is_safety_critical", False))

        # Step 2: Protect safety ranking
        protected = self.preserver.protect_safety_ranking(marked, top_k=5)
        # Safety item (doc2) should be first
        self.assertTrue(protected[0].get("is_safety_critical", False))

        # Step 3: Score confidence
        confident, uncertain = self.scorer.filter_by_confidence(
            protected, min_confidence=0.65
        )
        # Should have at least the high-confidence and safety items
        self.assertGreaterEqual(len(confident), 1)

        # Step 4: Detect conflicts
        conflicts = self.detector.detect_conflicts(confident)
        # No contradictions expected in this set
        self.assertIsInstance(conflicts, list)

    def test_phase1_filters_low_quality(self):
        """Test that Phase 1 filters low-quality results."""
        results = [
            {
                "id": "good",
                "content": "High quality maintenance instruction",
                "source": "vector",
                "score": 0.95,
                "metadata": {"source": "manual.pdf", "fileId": "f1"},
            },
            {
                "id": "poor",
                "content": "Vague reference",
                "source": "keyword",
                "score": 0.3,
                "metadata": {"source": "old_manual.pdf"},
            },
        ]

        marked = self.preserver.mark_safety_content(results)
        protected = self.preserver.protect_safety_ranking(marked, top_k=5)
        confident, uncertain = self.scorer.filter_by_confidence(
            protected, min_confidence=0.65
        )

        # Should filter out the poor result
        confident_ids = [r["id"] for r in confident]
        self.assertIn("good", confident_ids)
        self.assertNotIn("poor", confident_ids)


class TestCitationTracker(unittest.TestCase):
    """Test CitationTracker functionality."""

    def setUp(self):
        self.tracker = CitationTracker()

    def test_enrich_with_citations(self):
        """Test adding citations to results."""
        results = [
            {
                "id": "1",
                "content": "Maintenance procedure",
                "metadata": {"source": "/path/to/manual.pdf", "page": "42"},
            },
            {
                "id": "2",
                "content": "Safety warning",
                "metadata": {"source": "/path/to/safety.pdf", "page": "15"},
            },
        ]

        enriched = self.tracker.enrich_with_citations(results)

        # Check citations were added
        self.assertEqual(enriched[0]["citation"]["citation_id"], "C1")
        self.assertEqual(enriched[1]["citation"]["citation_id"], "C2")
        self.assertEqual(enriched[0]["citation"]["source_file"], "manual.pdf")
        self.assertEqual(enriched[1]["citation"]["source_file"], "safety.pdf")

    def test_extract_filename(self):
        """Test filename extraction from paths."""
        # Test Unix path
        filename = self.tracker._extract_filename("/path/to/document.pdf")
        self.assertEqual(filename, "document.pdf")

        # Test Windows path
        filename = self.tracker._extract_filename("C:\\Users\\doc.pdf")
        self.assertEqual(filename, "doc.pdf")

        # Test unknown
        filename = self.tracker._extract_filename("unknown")
        self.assertEqual(filename, "unknown")

    def test_citation_summary(self):
        """Test generation of citation summary."""
        results = [
            {
                "id": "1",
                "content": "Procedure",
                "confidence": 0.85,
                "citation": {
                    "citation_id": "C1",
                    "source_file": "manual.pdf",
                    "source_page": "42",
                    "source_section": "3.2.1",
                    "confidence": 0.85,
                    "is_safety_critical": False,
                },
            },
            {
                "id": "2",
                "content": "WARNING",
                "confidence": 0.95,
                "citation": {
                    "citation_id": "C2",
                    "source_file": "safety.pdf",
                    "source_page": "15",
                    "source_section": "",
                    "confidence": 0.95,
                    "is_safety_critical": True,
                },
            },
        ]

        summary = self.tracker.generate_citation_summary(results)

        self.assertIn("[C1]", summary)
        self.assertIn("[C2]", summary)
        self.assertIn("manual.pdf", summary)
        self.assertIn("safety.pdf", summary)
        self.assertIn("Safety critical", summary)

    def test_validate_response_citations_valid(self):
        """Test citation validation with valid citations."""
        response = "According to [C1], you should follow [C2] for safety."
        valid_citations = ["C1", "C2", "C3"]

        result = self.tracker.validate_response_citations(response, valid_citations)

        self.assertTrue(result["is_valid"])
        self.assertEqual(set(result["cited_ids"]), {"C1", "C2"})
        self.assertEqual(len(result["invalid_citations"]), 0)

    def test_validate_response_citations_invalid(self):
        """Test citation validation with invalid citations."""
        response = "According to [C1], but [C5] says differently."
        valid_citations = ["C1", "C2", "C3"]

        result = self.tracker.validate_response_citations(response, valid_citations)

        self.assertFalse(result["is_valid"])
        self.assertIn("C5", result["invalid_citations"])
        self.assertGreater(len(result["issues"]), 0)

    def test_extract_citations_from_response(self):
        """Test extracting citation IDs from LLM response."""
        response = "According to [C1], the procedure [C2] requires [C1] verification."

        citations = self.tracker.extract_citations_from_response(response)

        self.assertEqual(set(citations), {"C1", "C2"})

    def test_get_sources_for_citations(self):
        """Test retrieving source info for citations."""
        results = [
            {
                "id": "1",
                "content": "Procedure",
                "citation": {
                    "citation_id": "C1",
                    "source_file": "manual.pdf",
                    "source_page": "42",
                    "source_section": "3.2",
                    "confidence": 0.85,
                    "is_safety_critical": False,
                },
            },
            {
                "id": "2",
                "content": "Warning",
                "citation": {
                    "citation_id": "C2",
                    "source_file": "safety.pdf",
                    "source_page": "15",
                    "source_section": "",
                    "confidence": 0.95,
                    "is_safety_critical": True,
                },
            },
        ]

        sources = self.tracker.get_sources_for_citations(["C1", "C2"], results)

        self.assertIn("C1", sources)
        self.assertIn("C2", sources)
        self.assertEqual(sources["C1"]["source_file"], "manual.pdf")
        self.assertEqual(sources["C2"]["source_file"], "safety.pdf")

    def test_add_citations_to_prompt(self):
        """Test building prompt with citations."""
        query = "How do I maintain the rotor?"
        results = [
            {
                "id": "1",
                "content": "Use mineral oil for maintenance",
                "citation": {
                    "citation_id": "C1",
                    "source_file": "manual.pdf",
                    "source_page": "42",
                },
            },
            {
                "id": "2",
                "content": "WARNING: Never overfill",
                "citation": {
                    "citation_id": "C2",
                    "source_file": "safety.pdf",
                    "source_page": "15",
                },
            },
        ]

        system, context, user_query = self.tracker.add_citations_to_prompt(
            query, results
        )

        # Check system prompt
        self.assertIn("cite your sources", system)

        # Check context has citations
        self.assertIn("[C1]", context)
        self.assertIn("[C2]", context)
        self.assertIn("manual.pdf", context)

        # Check user query
        self.assertIn(query, user_query)


class TestPhase2Integration(unittest.TestCase):
    """Integration tests for Phase 2 citation tracking."""

    def setUp(self):
        self.tracker = CitationTracker()

    def test_citation_workflow(self):
        """Test complete citation workflow."""
        # 1. Results from Phase 1
        results = [
            {
                "id": "doc1",
                "content": "Maintenance requires regular inspection",
                "source": "vector",
                "score": 0.85,
                "confidence": 0.82,
                "is_safety_critical": False,
                "metadata": {"source": "manual.pdf", "page": "42", "fileId": "f1"},
            },
            {
                "id": "doc2",
                "content": "WARNING: Risk of injury without proper tools",
                "source": "graph_expansion",
                "score": 0.95,
                "confidence": 0.95,
                "is_safety_critical": True,
                "metadata": {"source": "safety.pdf", "page": "15", "fileId": "f2"},
            },
        ]

        # 2. Enrich with citations
        enriched = self.tracker.enrich_with_citations(results)

        # 3. Generate citation summary
        summary = self.tracker.generate_citation_summary(enriched)

        # 4. Create prompt with citations
        query = "What are the maintenance procedures?"
        system, context, user_query = self.tracker.add_citations_to_prompt(
            query, enriched
        )

        # 5. Simulate LLM response
        llm_response = (
            "According to the manual [C1], you need regular inspection. "
            "[C2] warns about injury risks without proper tools."
        )

        # 6. Validate response citations
        valid_ids = [r["citation"]["citation_id"] for r in enriched]
        validation = self.tracker.validate_response_citations(llm_response, valid_ids)

        # Assertions
        self.assertEqual(len(enriched), 2)
        self.assertIn("C1", summary)
        self.assertIn("C2", summary)
        self.assertTrue(validation["is_valid"])
        self.assertEqual(set(validation["cited_ids"]), {"C1", "C2"})

    def test_citation_no_hallucination(self):
        """Test that citation validation catches hallucinations."""
        results = [
            {
                "id": "1",
                "content": "Content A",
                "citation": {
                    "citation_id": "C1",
                    "source_file": "doc1.pdf",
                    "source_page": "1",
                },
            }
        ]

        # LLM hallucinates by citing C99 which doesn't exist
        llm_response = "According to [C1] and [C99], the answer is yes."

        valid_ids = ["C1"]
        validation = self.tracker.validate_response_citations(
            llm_response, valid_ids
        )

        self.assertFalse(validation["is_valid"])
        self.assertIn("C99", validation["invalid_citations"])


if __name__ == "__main__":
    unittest.main()
