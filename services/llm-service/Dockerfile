FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install llama-cpp-python with CUDA support
# This is the critical fix - properly enable GPU support during installation
RUN pip3 install --upgrade pip && \
    CMAKE_ARGS="-DLLAMA_CUDA=on" pip3 install llama-cpp-python==0.2.55 --force-reinstall --no-cache-dir && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Expose port for API
EXPOSE 8003

# Health check using the /v1/models endpoint (llama-cpp-python provides this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8003/v1/models || exit 1

# Default command
CMD ["python3", "main.py"]
