# 🔐 Política de Seguridad / Security Policy

## Versiones soportadas / Supported Versions

Solo la última línea menor de la serie actual recibe parches de seguridad.
Only the latest minor line of the current series receives security patches.

| Versión / Version | Soporte / Support             |
| ----------------- | ----------------------------- |
| v1.0.x            | ✅ Soportada / Supported      |
| < v1.0            | ❌ No soportada / Unsupported |

## Reportar una vulnerabilidad / Reporting a Vulnerability

> ⚠️ **No abras un Issue público ni una Discussion para reportar vulnerabilidades.**
> **Do not open a public Issue or Discussion to report vulnerabilities.**

Todos los reportes se gestionan de forma **privada** mediante GitHub Security
Advisories (*"Report a vulnerability"*):
All reports are handled **privately** through GitHub Security Advisories:

**👉 https://github.com/Llamas126/fastmedia-downloader/security/advisories/new**

### Información requerida / Required information

1. **Servicio afectado / Affected service**
   - Frontend (`:3000`) · API Gateway (`:8000`) · Media Processor (`:8001`, red interna) · Orquestación (`docker-compose.yml` / Dockerfiles)
2. **Tipo de vulnerabilidad / Vulnerability type**
   - Ejemplos / e.g.: SSRF, XSS, path traversal, DoS, fuga de información / information disclosure, escalamiento de privilegios / privilege escalation, validación de entrada insuficiente / insufficient input validation
   - Pistas útiles / useful hints: módulo implicado (p. ej. `_assert_public_url`, rate limiter, `/jobs/{job_id}/file`)
3. **PoC — Prueba de concepto reproducible / Proof of Concept**
   - Pasos exactos, URLs/payloads de ejemplo y respuesta obtenida vs esperada
   - Exact steps, sample URLs/payloads, obtained vs expected response
4. **Impacto estimado / Estimated impact** y condiciones de explotación / exploitation conditions
5. **Entorno / Environment**: Docker o local, versión (`docker --version`), SO

### Proceso y tiempos de respuesta / Process & Response Timeline

| Etapa / Stage                                        | Compromiso / Commitment                |
| ---------------------------------------------------- | -------------------------------------- |
| Acuse de recibo / Acknowledgment                     | ≤ 72 horas / hours                     |
| Triaje y evaluación / Triage & assessment            | ≤ 7 días / days                        |
| Fix + release del parche / Patch release             | Coordinado contigo / Coordinated       |
| Divulgación pública / Public disclosure              | Tras publicar el parche / After patch  |
| Crédito público / Public credit                      | A tu elección / At your discretion     |

## Ámbito / Scope

**En alcance / In scope**

- `services/api-gateway`: bloqueo anti-SSRF, validación de `url`/`format_id`/`job_id`, rate limiting por IP, `MAX_BODY_BYTES`, proxy y streaming de archivos
- `services/media-processor`: ciclo de vida de jobs, purga TTL de `temp_storage`, límites de concurrencia y tamaño, exposición en red interna
- `services/frontend`: manejo de datos y URLs provenientes del Gateway
- Hardening de contenedores: usuario no-root, `no-new-privileges`, `cap_drop`, límites de recursos

**Fuera de alcance / Out of scope**

- Salidas automáticas de scanners sin PoC verificado / Automated scanner output without a verified PoC
- Ataques que requieran acceso físico, al host o credenciales del operador / Attacks requiring physical/host access or operator credentials
- Vulnerabilidades upstream de dependencias sin impacto demostrable aquí (repórtalas también en `yt-dlp`/FFmpeg) / Upstream dependency issues without demonstrable impact here
- Ausencia de headers de seguridad en entornos puramente locales / Missing security headers in purely local environments

## Configuración segura recomendada / Recommended Secure Configuration

Mantén los valores seguros por defecto: `ALLOW_PRIVATE_URLS=0`,
`YTDLP_ALLOW_INSECURE_TLS=0`. Revisa las variables de entorno en el README.
Keep the secure defaults: `ALLOW_PRIVATE_URLS=0`, `YTDLP_ALLOW_INSECURE_TLS=0`.
See all environment variables in the README.
