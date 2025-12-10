"""
Hallucination detection module for checking faithfulness of LLM responses.

Detects when LLM invents information not supported by retrieved context.
Uses claim-level entailment checking to verify response accuracy.
"""

import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class HallucinationDetector:
    """Detects hallucinations in LLM responses against retrieved context."""

    # Faithfulness thresholds
    FAITHFULNESS_THRESHOLD = 0.80  # 80% of claims must be supported
    CLAIM_ENTAILMENT_THRESHOLD = 0.65  # Confidence in entailment

    def __init__(self, embedding_model=None):
        """
        Initialize hallucination detector.

        Args:
            embedding_model: Optional pre-loaded embedding model for entailment
        """
        self.embedding_model = embedding_model
        self.use_embeddings = embedding_model is not None

    def check_faithfulness(
        self, llm_response: str, context_chunks: List[str]
    ) -> Dict[str, Any]:
        """
        Check if LLM response is faithful to provided context.

        Splits response into claims and checks if each is supported
        by the context.

        Args:
            llm_response: The LLM-generated response
            context_chunks: List of retrieved context documents

        Returns:
            {
                'is_faithful': bool,
                'faithfulness_score': float (0-1),
                'total_claims': int,
                'supported_claims': int,
                'unsupported_claims': List[str],
                'confidence': str (HIGH/MEDIUM/LOW)
            }
        """
        # Split response into claims
        claims = self._extract_claims(llm_response)

        if not claims:
            return {
                "is_faithful": True,
                "faithfulness_score": 1.0,
                "total_claims": 0,
                "supported_claims": 0,
                "unsupported_claims": [],
                "confidence": "HIGH",
            }

        # Check each claim against context
        supported = []
        unsupported = []

        for claim in claims:
            is_supported = self._is_claim_supported(claim, context_chunks)
            if is_supported:
                supported.append(claim)
            else:
                unsupported.append(claim)

        # Calculate faithfulness score
        faithfulness_score = len(supported) / len(claims) if claims else 1.0

        # Determine confidence level
        if len(claims) >= 5:
            confidence = "HIGH"  # Enough claims for good evaluation
        elif len(claims) >= 2:
            confidence = "MEDIUM"  # Some claims
        else:
            confidence = "LOW"  # Very few claims

        result = {
            "is_faithful": faithfulness_score >= self.FAITHFULNESS_THRESHOLD,
            "faithfulness_score": faithfulness_score,
            "total_claims": len(claims),
            "supported_claims": len(supported),
            "unsupported_claims": unsupported,
            "confidence": confidence,
        }

        if not result["is_faithful"]:
            logger.warning(
                f"Hallucination detected: {len(unsupported)}/{len(claims)} "
                f"claims unsupported (faithfulness: {faithfulness_score:.2%})"
            )

        return result

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract factual claims from text.

        Splits by sentence and filters out subjective phrases.

        Args:
            text: Input text

        Returns:
            List of extracted claims (sentences)
        """
        # Split by periods, question marks, exclamation marks
        sentences = re.split(r'[.!?]+', text)

        # Clean and filter
        claims = []
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue

            # Skip subjective statements
            subjective_words = [
                "I think",
                "I believe",
                "in my opinion",
                "it seems",
                "apparently",
                "hopefully",
            ]
            if any(word in sent.lower() for word in subjective_words):
                continue

            claims.append(sent)

        return claims

    def _is_claim_supported(self, claim: str, context_chunks: List[str]) -> bool:
        """
        Check if a claim is supported by context.

        Uses pattern matching and semantic similarity.

        Args:
            claim: Single claim to verify
            context_chunks: List of context documents

        Returns:
            True if claim is supported by context
        """
        if not context_chunks:
            return False

        # Try pattern-based matching first (fast)
        if self._pattern_matches(claim, context_chunks):
            return True

        # If available, use semantic similarity (slower but more accurate)
        if self.use_embeddings:
            return self._semantic_entailment(claim, context_chunks)

        # Conservative: unsupported by default
        return False

    def _pattern_matches(self, claim: str, context_chunks: List[str]) -> bool:
        """
        Check if claim matches content in context using keywords.

        Args:
            claim: Claim to verify
            context_chunks: Context documents

        Returns:
            True if keywords from claim appear in context
        """
        # Extract key terms (nouns, numbers)
        key_terms = self._extract_key_terms(claim)

        if not key_terms:
            return True  # No specific terms to check

        # Check if context contains key terms
        context_text = " ".join(context_chunks).lower()

        for term in key_terms:
            if term.lower() not in context_text:
                return False

        return True

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms (named entities, numbers, technical terms).

        Args:
            text: Input text

        Returns:
            List of key terms
        """
        # Simple heuristic: words > 4 chars that are capitalized or numbers
        words = text.split()
        key_terms = []

        for word in words:
            word_clean = word.strip(".,!?;:")
            # Include: capitalized words, numbers, technical terms
            if len(word_clean) > 4 or word_clean.isdigit() or "%" in word:
                key_terms.append(word_clean)

        return key_terms[:10]  # Limit to 10 key terms

    def _semantic_entailment(
        self, claim: str, context_chunks: List[str]
    ) -> bool:
        """
        Check semantic entailment using embeddings.

        If context sentence has high similarity and same semantic
        direction as claim, claim is supported.

        Args:
            claim: Claim to verify
            context_chunks: Context documents

        Returns:
            True if claim is entailed by context
        """
        if not self.use_embeddings:
            return False

        try:
            from sentence_transformers import util

            # Encode claim
            claim_embedding = self.embedding_model.encode(claim, convert_to_tensor=True)

            # Check against context
            for context in context_chunks:
                context_embedding = self.embedding_model.encode(
                    context, convert_to_tensor=True
                )

                # Compute similarity
                similarity = util.pytorch_cos_sim(claim_embedding, context_embedding).item()

                # If high similarity, consider supported
                if similarity > self.CLAIM_ENTAILMENT_THRESHOLD:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error in semantic entailment: {e}")
            return False

    def log_hallucination_analysis(
        self, faithfulness_result: Dict[str, Any], response_preview: str = None
    ) -> None:
        """
        Log detailed hallucination analysis.

        Args:
            faithfulness_result: Result from check_faithfulness()
            response_preview: Optional preview of response
        """
        logger.info("=" * 70)
        logger.info("HALLUCINATION ANALYSIS")
        logger.info("=" * 70)

        is_faithful = faithfulness_result.get("is_faithful", False)
        score = faithfulness_result.get("faithfulness_score", 0.0)
        total = faithfulness_result.get("total_claims", 0)
        supported = faithfulness_result.get("supported_claims", 0)
        unsupported = faithfulness_result.get("unsupported_claims", [])
        confidence = faithfulness_result.get("confidence", "UNKNOWN")

        status = "✅ FAITHFUL" if is_faithful else "⚠️  HALLUCINATION"
        logger.info(f"Status: {status}")
        logger.info(f"Faithfulness Score: {score:.1%}")
        logger.info(f"Claims: {supported}/{total} supported")
        logger.info(f"Confidence: {confidence}")

        if unsupported:
            logger.warning(f"Unsupported claims ({len(unsupported)}):")
            for claim in unsupported[:3]:  # Log first 3
                logger.warning(f"  - {claim[:80]}...")

        logger.info("=" * 70)
