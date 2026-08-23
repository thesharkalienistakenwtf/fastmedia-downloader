FROM python:3.11-slim

LABEL org.opencontainers.image.title="FastMedia Downloader — API Gateway" \
      org.opencontainers.image.description="Extracción de metadatos y orquestación de descargas multimedia" \
      org.opencontainers.image.authors="Juan Camilo Llamas Cárdenas" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.copyright="Copyright (c) 2026 Juan Camilo Llamas Cárdenas" \
      org.opencontainers.image.version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

RUN useradd --system --uid 1001 --create-home appuser \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["sh", "-c", "pip install --user --no-cache-dir --upgrade yt-dlp || echo '[WARN] yt-dlp upgrade failed; using bundled version'; exec uvicorn main:app --host 0.0.0.0 --port 8000"]
