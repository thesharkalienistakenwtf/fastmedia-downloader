# FastMedia Downloader

**Microservices-Based Video & Media Extractor** — Plataforma web escalable y distribuida para analizar y descargar videos/audio en cualquier calidad (hasta **4K** con combinación de pistas vía **FFmpeg**, o **MP3** solo audio).

> ⚠️ **Aviso legal**: utiliza esta herramienta únicamente con contenido del que tengas derechos o autorización explícita. Respeta los Términos de Servicio de las plataformas origen y las leyes de copyright de tu jurisdicción.

---

## 🏗️ Arquitectura de Microservicios

```
                        ┌─────────────────────────────────────────────┐
                        │            Red interna (bridge)             │
                        │               fastmedia-net                 │
                        │                                             │
 ┌──────────┐   :3000   │  ┌──────────────┐   :8001    ┌───────────┐  │
 │ Usuario  │◄──────────┼──┤   Frontend   │            │   Media   │  │
 │ (Web UI) │           │  │  Next.js 14  │            │ Processor │  │
 └──────────┘           │  └──────┬───────┘            │ yt-dlp +  │  │
                        │         │                    │  FFmpeg   │  │
                        │         ▼        :8000       │           │  │
                        │  ┌──────────────┐  HTTP      │  Jobs +   │  │
                        │  │ API Gateway  │────────────┤  TTL      │  │
                        │  │ FastAPI      │  proxy     └─────┬─────┘  │
                        │  └──────────────┘                  │        │
                        │                                    ▼        │
                        │                          temp_storage/      │
                        │                          (volumen montado)  │
                        └─────────────────────────────────────────────┘
```

| Microservicio | Stack | Puerto | Exposición | Responsabilidad |
|---|---|---|---|---|
| **Frontend** | Next.js 14+, TypeScript, Tailwind CSS, Lucide | `3000` | Pública | UI oscura responsiva: análisis de URL, selección de formato, progreso |
| **API Gateway / Metadata** | FastAPI (Python 3.11), yt-dlp, httpx | `8000` | Pública | Validaciones, CORS, metadatos ligeros (`download=False`), proxy de jobs y archivos |
| **Media Processor** | FastAPI, yt-dlp, FFmpeg | `8001` | Solo red interna | Descarga asíncrona, merge audio/video HD, conversión MP3, limpieza con TTL |

### Flujo de una descarga

1. El usuario pega una URL → el Gateway extrae metadatos y formatos con `yt-dlp` (`download=False`).
2. El usuario elige calidad (4K / 1080p / 720p / … / MP3) → el Gateway valida y delega al Media Processor.
3. El Media Processor crea un job con UUID, descarga en segundo plano y ensambla las pistas con FFmpeg.
4. El frontend hace *polling* del estado cada 2 s; al completar, el archivo se transmite vía proxy desde la red interna y se purga tras el TTL.

---

## 🚀 Inicio rápido (Docker)

Requisito: Docker Desktop (o Engine) con Compose v2.

```bash
docker compose up --build
```

- Interfaz web: <http://localhost:3000>
- API Gateway (docs interactivas): <http://localhost:8000/docs>

Para detener y limpiar:

```bash
docker compose down          # detiene contenedores
docker compose down --rmi all --volumes   # además borra imágenes
```

> Si los puertos `3000`/`8000` están ocupados en tu máquina, define `FRONTEND_PORT` / `API_GATEWAY_PORT` en un archivo `.env` (ver `.env.example`). Recuerda alinear también `NEXT_PUBLIC_API_URL` con el puerto público del Gateway.

---

## 🔧 Desarrollo local (sin Docker)

### Frontend

```bash
cd services/frontend
npm install
npm run dev          # http://localhost:3000
```

### API Gateway

```bash
cd services/api-gateway
python -m venv .venv && .venv\Scripts\activate     # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Media Processor

```bash
cd services/media-processor
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# Requiere ffmpeg en PATH: winget install Gyan.FFmpeg  (Windows) / apt install ffmpeg (Debian/Ubuntu)
set MEDIA_PROCESSOR_URL=http://localhost:8001        # no aplica aquí; es variable del gateway
set ALLOWED_ORIGINS=http://localhost:3000
uvicorn main:app --port 8000                         # gateway
# en otra terminal:
set TEMP_STORAGE_DIR=./temp_storage
uvicorn worker:app --port 8001                       # media processor
```

---

## 📡 API Reference

| Método | Endpoint (Gateway :8000) | Descripción |
|---|---|---|
| `GET` | `/api/v1/info?url=` | Metadatos: título, miniatura, duración, creador + formatos disponibles |
| `POST` | `/api/v1/downloads` | Body `{ "url", "format_id"?, "audio_only"? }` → `{ job_id }` (HTTP 202) |
| `GET` | `/api/v1/downloads/{job_id}` | Estado del job: `queued/downloading/processing/completed/error`, progreso % |
| `GET` | `/api/v1/downloads/{job_id}/file` | Streaming del archivo terminado (`Content-Disposition: attachment`) |

| Método | Endpoint (Media Processor :8001, red interna) |
|---|---|
| `POST` | `/process-media` |
| `GET` | `/jobs/{job_id}` |
| `GET` | `/jobs/{job_id}/file` |
| `GET` | `/health` |

---

## ⚙️ Variables de entorno

| Variable | Servicio | Default | Descripción |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:8000` | URL pública del Gateway (se compila en el bundle cliente) |
| `MEDIA_PROCESSOR_URL` | api-gateway | `http://localhost:8001` | URL interna del microservicio de procesamiento |
| `ALLOWED_ORIGINS` | api-gateway | `http://localhost:3000` | Orígenes CORS separados por coma |
| `TEMP_STORAGE_DIR` | media-processor | `/app/temp_storage` | Directorio de archivos temporales |
| `FILE_TTL_MINUTES` | media-processor | `30` | Minutos antes de purgar trabajos terminados |

---

## 📁 Estructura del monorepo

```
fastmedia-downloader/
├── docker-compose.yml              # Orquestación: red bridge, volúmenes, healthchecks
├── .env.example
├── services/
│   ├── frontend/                   # Next.js 14+ (App Router, TS, Tailwind)
│   │   ├── Dockerfile              # Build multietapa (deps → builder → runner standalone)
│   │   ├── package.json
│   │   ├── tailwind.config.ts
│   │   └── src/
│   │       ├── app/                # layout, page (máquina de estados), globals.css
│   │       ├── components/         # UrlForm, MetadataCard, FormatSelector
│   │       └── lib/api.ts          # Cliente tipado del Gateway
│   ├── api-gateway/                # FastAPI :8000
│   │   ├── Dockerfile              # python:3.11-slim
│   │   ├── requirements.txt
│   │   └── main.py
│   └── media-processor/            # FastAPI + yt-dlp + FFmpeg :8001
│       ├── Dockerfile              # python:3.11-slim + apt-get ffmpeg
│       ├── requirements.txt
│       ├── worker.py               # Jobs en memoria, merge HD, janitor TTL
│       └── temp_storage/           # Volumen de descargas temporales (.gitkeep)
```

---

## 🧭 Decisiones técnicas y roadmap

- **Jobs en memoria** (`dict` + lock) dentro del Media Processor: simple y sin dependencias externas para v1. Los jobs no sobreviven reinicios del contenedor. Ruta de escalado: sustituir por **Redis** + cola (RQ/Celery/arq) para múltiples réplicas horizontales del worker.
- **Progreso por pistas**: en descargas DASH (video+audio separados) la barra puede reiniciarse entre pista de video y pista de audio; es el comportamiento esperado del hook de yt-dlp.
- **Plataformas con anti-bot agresivo** (p. ej. YouTube en datacenters): pueden requerir cookies o tokens; se puede extender pasando `cookiefile` en las opciones de yt-dlp.
- Limpieza automática de `temp_storage/` cada 60 s para archivos con más de `FILE_TTL_MINUTES`.
