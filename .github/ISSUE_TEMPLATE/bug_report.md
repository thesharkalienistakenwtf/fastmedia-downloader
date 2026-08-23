---
name: 🐛 Reporte de error / Bug report
about: Fallo en análisis, descarga o procesamiento / Failure in analysis, download or processing
title: "[BUG] "
labels: ["bug"]
assignees: ""
---

## 📝 Descripción del problema / Problem description

<!-- Explica claramente qué ocurre e indica el componente afectado: Frontend (:3000),
     API Gateway (:8000) o Media Processor (:8001).
     Explain clearly what happens and which component is affected. -->

## 🔗 URL del video/audio que falló / Failing video/audio URL

<!-- Si contiene datos sensibles, reemplaza el enlace por uno equivalente.
     If it contains sensitive data, replace it with an equivalent public link. -->
- **URL:** `https://...`
- **Formato seleccionado / Selected format:** (ej./e.g. 1080p MP4 / Solo Audio MP3)

## ✅ Comportamiento esperado / Expected behavior

<!-- Qué debería haber pasado. What should have happened instead. -->

## 🔁 Pasos para reproducirlo / Steps to reproduce

<!--
1. Ir a '...' / Go to '...'
2. Pegar la URL '...' / Paste the URL '...'
3. Seleccionar formato '...' / Select format '...'
4. Ver el error / See the error
-->

## 📋 Logs y mensajes de error / Logs and error messages

<!-- Salida de `docker compose logs --tail=100`, mensaje de la UI o respuesta JSON del endpoint.
     Relevant output from `docker compose logs --tail=100`, UI message or endpoint JSON response. -->

## 💻 Entorno / Environment

- **Despliegue / Deployment:** [ ] Docker (`docker compose up`) · [ ] Local sin Docker / Local without Docker
- **Sistema operativo / OS:**
- **Navegador / Browser** (si aplica / if applicable):
- **Versión de Docker / Docker version** (`docker --version`):

## ✔️ Checklist

- [ ] El video es accesible públicamente / The video is publicly accessible (no privado ni geobloqueado / not private or geo-blocked).
- [ ] Revisé los errores comunes documentados / Reviewed documented common errors (400/409/410/413/429/502).
- [ ] Busqué issues existentes similares / Searched existing Issues for similar reports.

## ➕ Contexto adicional / Additional context

<!-- Capturas, frecuencia del fallo, plataforma origen, etc.
     Screenshots, failure frequency, source platform, etc. -->
