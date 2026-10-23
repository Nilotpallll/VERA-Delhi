# VERA FastAPI Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    CT2_FORCE_CPU_ISA=GENERIC

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny model during Docker build to eliminate runtime latency and timeouts
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

COPY apps/api /app/apps/api
COPY data /app/data

EXPOSE 8000

CMD ["sh", "-c", "uvicorn apps.api.src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
