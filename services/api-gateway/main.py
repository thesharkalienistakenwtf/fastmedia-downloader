"""FastMedia Downloader - API Gateway / Metadata Service.

Enrutamiento, validaciones y CORS. Extrae metadatos ligeros con yt-dlp
(download=False) y delega las descargas pesadas al microservicio
media-processor, actuando como proxy de estado y streaming de archivos.
"""

import os
from typing import Any, Optional
from urllib.parse import quote

import httpx
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

MEDIA_PROCESSOR_URL = os.getenv("MEDIA_PROCESSOR_URL", "http://localhost:8001").rstrip("/")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

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
    "nocheckcertificate": True,
    "http_headers": {"User-Agent": USER_AGENT},
    "extractor_retries": 3,
}

app = FastAPI(
    title="FastMedia Downloader - API Gateway",
    description="Extraccion de metadatos y orquestacion de descargas multimedia.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/api/v1/info")
def get_video_info(url: str) -> dict[str, Any]:
    """Invoca yt-dlp en modo download=False para obtener metadatos y formatos."""
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalida")

    options = {
        **BASE_YTDLP_OPTIONS,
        "skip_download": True,
        "socket_timeout": 15,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.YoutubeDLError as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo analizar el video: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error inesperado analizando el video: {exc}") from exc

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


def _map_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    """Consolida los formatos crudos de yt-dlp: la mejor pista por resolucion + opcion MP3."""
    best_by_height: dict[int, dict[str, Any]] = {}
    for fmt in info.get("formats") or []:
        height = fmt.get("height")
        format_id = fmt.get("format_id")
        if not height or not format_id or fmt.get("vcodec") in (None, "none"):
            continue
        candidate = {
            "tbr": fmt.get("tbr") or 0.0,
            "is_mp4": fmt.get("ext") == "mp4",
            "payload": {
                "format_id": str(format_id),
                "label": RESOLUTION_LABELS.get(int(height), f"{int(height)}p"),
                "height": int(height),
                "ext": fmt.get("ext"),
                "filesize_approx": fmt.get("filesize_approx") or fmt.get("filesize"),
            },
        }
        current = best_by_height.get(height)
        if current is None or (candidate["tbr"], candidate["is_mp4"]) > (current["tbr"], current["is_mp4"]):
            best_by_height[height] = candidate

    formats = [entry["payload"] for _, entry in sorted(best_by_height.items(), key=lambda kv: kv[0])][::-1]
    formats.append({
        "format_id": AUDIO_FORMAT_ID,
        "label": "Solo Audio (MP3)",
        "audio_only": True,
    })
    return formats


@app.post("/api/v1/downloads", status_code=202)
async def create_download(request: DownloadRequest) -> dict[str, Any]:
    """Valida la solicitud y delega el trabajo pesado al media-processor."""
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
    return await _proxy_job_get(job_id)


@app.get("/api/v1/downloads/{job_id}/file")
async def download_file(job_id: str) -> StreamingResponse:
    """Transmite en proxy el archivo generado por el media-processor."""
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
