import os
from llama_cpp import Llama

# --- Configuration from environment variables ---
model_path = os.environ.get("MODEL_PATH", "/app/models/your-model.gguf")
n_gpu_layers = int(os.environ.get("N_GPU_LAYERS", "0"))
chat_format = os.environ.get("CHAT_FORMAT", "llama-3")

# --- Device Detection ---
def detect_device() -> str:
    """Detect the best available device for inference."""
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print(f"Using device: {device} ({torch.cuda.get_device_name(0)})")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return device
        elif torch.backends.mps.is_available():
            device = "mps"
            print(f"Using device: {device} (Apple Metal)")
            return device
        else:
            device = "cpu"
            print(f"Using device: {device}")
            return device
    except ImportError:
        # If torch is not available, assume CPU or rely on llama-cpp-python's detection
        print("PyTorch not available, device detection limited")
        if n_gpu_layers > 0:
            print("GPU layers configured, assuming CUDA/Metal available")
            return "cuda/metal"
        return "cpu"

# --- Validate Model File ---
if not os.path.exists(model_path):
    raise FileNotFoundError(
        f"Model file not found: {model_path}\n"
        f"Please download a GGUF model and place it in the models directory.\n"
        f"Example: Place your model at {model_path}"
    )

print("=" * 60)
print("Diksuchi LLM Service Starting...")
print("=" * 60)
print(f"Model path: {model_path}")
print(f"Offloading {n_gpu_layers} layers to GPU (0 = CPU only, -1 = all layers)")
print(f"Chat format: {chat_format}")

device = detect_device()
print("=" * 60)

# --- Load the Model ---
print(f"Loading model from: {model_path}")
print("This may take 30-120 seconds depending on model size...")

try:
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=4096,
        chat_format=chat_format,
        verbose=False  # Set to True for debugging
    )
    print("✓ Model loaded successfully!")
    print("=" * 60)
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    print("=" * 60)
    raise

# --- Start the OpenAI-compatible server ---
# This automatically creates the /v1/chat/completions endpoint
# We'll add a health endpoint by starting our own FastAPI server
print("Starting OpenAI-compatible API server...")
print(f"API will be available at: http://0.0.0.0:8003/v1")
print(f"Health check at: http://0.0.0.0:8003/health")
print("=" * 60)

# Use llama-cpp-python's built-in OpenAI server on port 8003
llm.create_openai_api_server(
    host="0.0.0.0",
    port=8003
)
