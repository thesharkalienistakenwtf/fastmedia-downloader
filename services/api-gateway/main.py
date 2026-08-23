"""FastMedia Downloader - API Gateway / Metadata Service.

Enrutamiento, validaciones y CORS. Extrae metadatos ligeros con yt-dlp
(download=False) y delega las descargas pesadas al microservicio
media-processor, actuando como proxy de estado y streaming de archivos.
"""

#  _________________________________________________________________
# /                                                                 \
# |   FastMedia Downloader - High-Performance Engine                |
# |   Architecture & Core Implementation                            |
# |                                                                 |
# |   Author: Juan Camilo Llamas Cárdenas                           |
# |   License: MIT (Free & Open Source Use)                         |
# |   Copyright (c) 2026 Juan Camilo Llamas Cárdenas                |
# \_________________________________________________________________/
#               \
#                \   /\___/\
#                   /       \
#                  |  #   #  |
#                  \  ___  /
#                   |     |
#                   |     |      __
#                   |     \_____/  \
#                   |               |
#                    \______/\_____/
#                    /      /
#                   /      /
#                  /__/   /__/

import ipaddress
import logging
import os
import re
import socket
import threading
import time
from collections import defaultdict, deque
from typing import Any, Optional
from urllib.parse import quote, urlparse

import httpx
import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

MEDIA_PROCESSOR_URL = os.getenv("MEDIA_PROCESSOR_URL", "http://localhost:8001").rstrip("/")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
DOWNLOADS_PER_MINUTE = int(os.getenv("DOWNLOADS_PER_MINUTE", "10"))
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "65536"))
ALLOW_PRIVATE_URLS = os.getenv("ALLOW_PRIVATE_URLS", "0").lower() in ("1", "true", "yes")
ALLOW_INSECURE_TLS = os.getenv("YTDLP_ALLOW_INSECURE_TLS", "0").lower() in ("1", "true", "yes")

JOB_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
FORMAT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{1,32}$")

RESOLUTION_LABELS = {
    4320: "8K",
    2880: "5K",
    2160: "4K",
    1440: "1440p",
    1080: "1080p",
    720: "720p",
    480: "480p",
    360: "360p",
    240: "240p",
    144: "144p",
}

AUDIO_FORMAT_ID = "bestaudio"

HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
STREAM_TIMEOUT = httpx.Timeout(None, connect=15.0)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

BASE_YTDLP_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "nocheckcertificate": ALLOW_INSECURE_TLS,
    "http_headers": {"User-Agent": USER_AGENT},
    "extractor_retries": 3,
}

_RATE_LOCK = threading.Lock()
_RATE_HITS: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _rate_limit(key: tuple[str, str], limit: int, window_seconds: float = 60.0) -> bool:
    """Ventana deslizante en memoria; True si la peticion queda dentro del limite."""
    now = time.monotonic()
    with _RATE_LOCK:
        hits = _RATE_HITS[key]
        while hits and hits[0] <= now - window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        if len(_RATE_HITS) > 10_000:
            for bucket in [k for k, v in _RATE_HITS.items() if not v]:
                _RATE_HITS.pop(bucket, None)
        return True


def _assert_public_url(url: str) -> None:
    """Bloqueo SSRF basico: resuelve el host y rechaza IPs no publicas."""
    if ALLOW_PRIVATE_URLS:
        return
    hostname = urlparse(url).hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL invalida")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="No se pudo resolver el host de la URL") from exc
    for info in infos:
        address = info[4][0].split("%")[0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if not ip.is_global:
            raise HTTPException(status_code=400, detail="La URL apunta a una direccion no publica")

app = FastAPI(
    title="FastMedia Downloader - API Gateway",
    description="Extraccion de metadatos y orquestacion de descargas multimedia.",
    version="1.0.0",
    contact={"name": "Juan Camilo Llamas Cárdenas"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def abuse_guard(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Cuerpo de la peticion demasiado grande"})
    if not _rate_limit((client_ip, "general"), RATE_LIMIT_PER_MINUTE):
        return JSONResponse(status_code=429, content={"detail": "Demasiadas peticiones; reintenta mas tarde"})
    if request.method == "POST" and request.url.path == "/api/v1/downloads":
        if not _rate_limit((client_ip, "downloads"), DOWNLOADS_PER_MINUTE):
            return JSONResponse(status_code=429, content={"detail": "Limite de descargas por minuto alcanzado"})
    return await call_next(request)


class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None
    audio_only: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError("La URL debe comenzar con http:// o https://")
        return value

    @field_validator("format_id")
    @classmethod
    def validate_format_id(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not FORMAT_ID_PATTERN.fullmatch(value):
            raise ValueError("format_id contiene caracteres no permitidos")
        return value


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/api/v1/info")
def get_video_info(url: str) -> dict[str, Any]:
    """Invoca yt-dlp en modo download=False para obtener metadatos y formatos."""
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalida")
    _assert_public_url(url)

    options = {
        **BASE_YTDLP_OPTIONS,
        "skip_download": True,
        "socket_timeout": 15,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.YoutubeDLError as exc:
        logger.warning("Analisis fallido para %s: %s", url, exc)
        raise HTTPException(status_code=400, detail="No se pudo analizar el video") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error inesperado analizando %s", url)
        raise HTTPException(status_code=500, detail="Error inesperado analizando el video") from exc

    if info is None:
        raise HTTPException(status_code=404, detail="No se encontro contenido en la URL indicada")
    if info.get("_type") == "playlist":
        raise HTTPException(status_code=400, detail="Las listas de reproduccion no estan soportadas; usa el enlace de un video individual")

    return {
        "title": info.get("title"),
        "thumbnail": _pick_thumbnail(info),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url") or url,
        "formats": _map_formats(info),
    }


def _pick_thumbnail(info: dict[str, Any]) -> Optional[str]:
    thumbnail = info.get("thumbnail")
    if thumbnail:
        return thumbnail
    thumbnails = info.get("thumbnails") or []
    for item in reversed(thumbnails):
        if item.get("url"):
            return item["url"]
    return None


MP3_BITRATE_KBPS = 192


def _format_bytes(fmt: dict[str, Any], duration: Optional[float]) -> Optional[int]:
    """Tamano exacto si existe; si no, lo aproxima con el bitrate (tbr)."""
    size = fmt.get("filesize") or fmt.get("filesize_approx")
    if size:
        return int(size)
    tbr = fmt.get("tbr")
    if tbr and duration and duration > 0:
        return int(float(tbr) * 1000 / 8 * float(duration))
    return None


def _best_audio_track(info: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Pista de audio que el merge de yt-dlp combinara (m4a preferente)."""
    tracks = [
        f
        for f in info.get("formats") or []
        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")
    ]
    if not tracks:
        return None
    tracks.sort(key=lambda f: (f.get("ext") == "m4a", f.get("tbr") or 0.0), reverse=True)
    return tracks[0]


def _human_size(size_bytes: Optional[int]) -> Optional[str]:
    """Convierte bytes a etiqueta legible ('45.2 MB'); None si no hay dato."""
    if not size_bytes or size_bytes <= 0:
        return None
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            decimals = 0 if unit == "B" else 1
            return f"{value:.{decimals}f} {unit}".replace(".0 ", " ")
        value /= 1024
    return None


def _map_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    """Consolida los formatos crudos de yt-dlp: la mejor pista por resolucion + opcion MP3."""
    duration = info.get("duration")
    audio_track = _best_audio_track(info)
    audio_bytes = _format_bytes(audio_track, duration) if audio_track else None

    best_by_height: dict[int, dict[str, Any]] = {}
    for fmt in info.get("formats") or []:
        height = fmt.get("height")
        format_id = fmt.get("format_id")
        if not height or not format_id or fmt.get("vcodec") in (None, "none"):
            continue
        video_bytes = _format_bytes(fmt, duration)
        has_own_audio = fmt.get("acodec") not in (None, "none")
        if video_bytes is None:
            total_bytes: Optional[int] = None
        elif has_own_audio or not audio_bytes:
            total_bytes = video_bytes
        else:
            total_bytes = video_bytes + audio_bytes
        candidate = {
            "tbr": fmt.get("tbr") or 0.0,
            "is_mp4": fmt.get("ext") == "mp4",
            "payload": {
                "format_id": str(format_id),
                "label": RESOLUTION_LABELS.get(int(height), f"{int(height)}p"),
                "height": int(height),
                "ext": fmt.get("ext"),
                "filesize_approx": fmt.get("filesize_approx") or fmt.get("filesize"),
                "filesize_bytes": total_bytes,
                "filesize_human": _human_size(total_bytes),
            },
        }
        current = best_by_height.get(height)
        if current is None or (candidate["tbr"], candidate["is_mp4"]) > (current["tbr"], candidate["is_mp4"]):
            best_by_height[height] = candidate

    formats = [entry["payload"] for _, entry in sorted(best_by_height.items(), key=lambda kv: kv[0])][::-1]

    mp3_bytes = int(MP3_BITRATE_KBPS * 1000 / 8 * duration) if duration and duration > 0 else None
    formats.append({
        "format_id": AUDIO_FORMAT_ID,
        "label": "Solo Audio (MP3)",
        "audio_only": True,
        "filesize_bytes": mp3_bytes,
        "filesize_human": _human_size(mp3_bytes),
    })
    return formats


@app.post("/api/v1/downloads", status_code=202)
async def create_download(request: DownloadRequest) -> dict[str, Any]:
    """Valida la solicitud y delega el trabajo pesado al media-processor."""
    if not request.url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalida")
    _assert_public_url(request.url)

    payload: dict[str, Any] = {"url": request.url}
    if request.audio_only:
        payload["audio_only"] = True
    elif request.format_id:
        payload["format_id"] = request.format_id
    else:
        raise HTTPException(status_code=400, detail="Indica un formato (format_id) o audio_only=true")

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(f"{MEDIA_PROCESSOR_URL}/process-media", json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="El servicio de procesamiento no esta disponible") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=_extract_detail(response))
    return response.json()


@app.get("/api/v1/downloads/{job_id}")
async def get_download_status(job_id: str) -> dict[str, Any]:
    _ensure_valid_job_id(job_id)
    return await _proxy_job_get(job_id)


@app.get("/api/v1/downloads/{job_id}/file")
async def download_file(job_id: str) -> StreamingResponse:
    """Transmite en proxy el archivo generado por el media-processor."""
    _ensure_valid_job_id(job_id)
    job = await _proxy_job_get(job_id)
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="El archivo aun no esta listo")
    filename = job.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    client = httpx.AsyncClient(timeout=STREAM_TIMEOUT)
    try:
        request = client.build_request("GET", f"{MEDIA_PROCESSOR_URL}/jobs/{job_id}/file")
        upstream = await client.send(request, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail="El servicio de procesamiento no esta disponible") from exc

    if upstream.status_code >= 400:
        detail = _extract_detail(upstream)
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=upstream.status_code, detail=detail)

    headers: dict[str, str] = {"Content-Disposition": _content_disposition(filename)}
    content_length = upstream.headers.get("content-length")
    if content_length:
        headers["Content-Length"] = content_length

    async def stream_media():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=256 * 1024):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_media(),
        media_type=_guess_media_type(filename),
        headers=headers,
    )


def _ensure_valid_job_id(job_id: str) -> None:
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="Trabajo no encontrado o expirado")


async def _proxy_job_get(job_id: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(f"{MEDIA_PROCESSOR_URL}/jobs/{job_id}")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="El servicio de procesamiento no esta disponible") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=_extract_detail(response))
    return response.json()


def _extract_detail(response: httpx.Response) -> str:
    try:
        return str(response.json().get("detail") or "Error en el servicio de procesamiento")
    except Exception:  # noqa: BLE001
        return "Error en el servicio de procesamiento"


def _content_disposition(filename: str) -> str:
    """RFC 6266/5987: fallback ASCII + version UTF-8 para nombres unicode."""
    ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "").strip()
    return f'attachment; filename="{ascii_name or "download"}"; filename*=UTF-8\'\'{quote(filename, safe="")}'


def _guess_media_type(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    return {
        "mp4": "video/mp4",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
    }.get(extension, "application/octet-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
