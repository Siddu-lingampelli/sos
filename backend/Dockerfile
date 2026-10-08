FROM python:3.11-slim
# System libs required by opencv-python (libGL), torch, and audio.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsndfile1 ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend and AI dependencies. Build context is the repo root so the ai/ tree
# is available for the vision/audio import paths.
COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai/requirements.txt /app/ai/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt -r /app/ai/requirements.txt

COPY backend /app/backend
COPY ai /app/ai

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 silentsos \
 && chown -R silentsos:silentsos /app
USER silentsos

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]