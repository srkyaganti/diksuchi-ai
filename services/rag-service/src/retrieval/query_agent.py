import logging
import os
from typing import List, Dict
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

logger = logging.getLogger(__name__)

class QueryAgent:
    """
    Agent that refines and expands user queries before retrieval.
    Uses a small, fast LLM (e.g., Llama-3.2-3B or Qwen2.5-7B).
    """
    
    def __init__(self, model_path: str = "models/llama-3.2-3b-instruct.gguf"):
        self.model_path = model_path
        self.llm = None
        
        if not os.path.exists(model_path):
            logger.warning(f"Query Agent model not found at {model_path}. Query refinement disabled.")
            return

        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_gpu_layers=-1,
                verbose=False
            )
            logger.info("Query Agent initialized.")
        except Exception as e:
            logger.error(f"Failed to init Query Agent: {e}")

    def refine_query(self, original_query: str) -> str:
        """
        Rewrites the query to be more search-friendly.
        Example: "torque for bolt" -> "torque specification main rotor bolt fastener"
        """
        if not self.llm:
            return original_query

        prompt = f"""You are a search optimization expert for defense manuals.
        Your goal is to rewrite the user's query to improve retrieval accuracy.
        
        Rules:
        1. Expand technical acronyms (e.g., "HPC" -> "High Pressure Compressor").
        2. Add synonyms for key terms (e.g., "bolt" -> "fastener", "screw").
        3. Keep it concise. Do NOT explain your reasoning. Just output the rewritten query.
        
        User Query: {original_query}
        
        Rewritten Query:"""
        
        try:
            output = self.llm.create_completion(
                prompt,
                max_tokens=64,
                stop=["User Query:", "\n"],
                temperature=0.0 # Low temperature for deterministic behavior
            )
            refined = output['choices'][0]['text'].strip()
            logger.info(f"Refined query: '{original_query}' -> '{refined}'")
            return refined
        except Exception as e:
            logger.error(f"Query refinement failed: {e}")
            return original_query
