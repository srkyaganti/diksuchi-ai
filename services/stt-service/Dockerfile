# Stage 1: Builder - Install dependencies
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Final minimal image
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

LABEL maintainer="diksuchi-stt-service"
LABEL description="Faster Whisper STT Service with GPU/CPU support"
LABEL version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN useradd -m -u 1000 -s /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --chown=appuser:appuser server.py .
COPY --chown=appuser:appuser requirements.txt .

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "server.py"]
