import logging
import os
from typing import Optional
try:
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler
except ImportError:
    Llama = None
    Llava15ChatHandler = None

logger = logging.getLogger(__name__)

class VisionAnalyzer:
    """
    Uses a local VLM (Qwen2-VL or LLaVA) to generate descriptions for images.
    """
    def __init__(self, model_path: str = "models/qwen2-vl-2b-instruct-q4_k_m.gguf", clip_model_path: str = "models/mmproj-model-f16.gguf"):
        self.model_path = model_path
        self.clip_model_path = clip_model_path
        self.llm = None
        
        if not os.path.exists(model_path) or not os.path.exists(clip_model_path):
            logger.warning(f"Vision models not found at {model_path} or {clip_model_path}. Vision analysis disabled.")
            return

        try:
            # Initialize Qwen2-VL / LLaVA handler
            chat_handler = Llava15ChatHandler(clip_model_path=self.clip_model_path)
            
            self.llm = Llama(
                model_path=self.model_path,
                chat_handler=chat_handler,
                n_ctx=2048, # Context for image + description
                n_gpu_layers=-1,
                verbose=False
            )
            logger.info("Vision Analyzer initialized.")
        except Exception as e:
            logger.error(f"Failed to init Vision Analyzer: {e}")

    def analyze_image(self, image_path: str) -> str:
        """
        Generates a technical description of the image.
        """
        if not self.llm:
            return "Vision model not loaded."
            
        if not os.path.exists(image_path):
            return "Image file not found."

        prompt = "Describe this technical diagram or image in detail. Focus on components, labels, and warnings."
        
        try:
            response = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a technical assistant analyzing defense manual diagrams."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"file://{image_path}"}}
                    ]}
                ]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return "Error analyzing image."
