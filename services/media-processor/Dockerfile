FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# FFmpeg: imprescindible para el merge de pistas HD y la conversion a MP3
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY worker.py .

RUN useradd --system --uid 1001 --create-home appuser \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()" || exit 1

CMD ["sh", "-c", "pip install --user --no-cache-dir --upgrade yt-dlp || echo '[WARN] yt-dlp upgrade failed; using bundled version'; exec uvicorn worker:app --host 0.0.0.0 --port 8001"]
