# 🤝 Guía de Contribución · Contributing Guide

¡Gracias por tu interés en mejorar FastMedia Downloader! / Thanks for your interest in improving FastMedia Downloader!

> Antes de empezar: respeta el [Código de Conducta](CODE_OF_CONDUCT.md) /
> Please follow the Code of Conduct.
> 🔒 Vulnerabilidades de seguridad NO van aquí: usa el proceso privado de
> [SECURITY.md](SECURITY.md) / Security vulnerabilities go through SECURITY.md,
> never public issues.

## 🧰 Requisitos / Prerequisites

| Herramienta | Versión | Uso |
| --- | --- | --- |
| Docker Desktop / Engine | Compose v2 | Stack completo (`docker compose`) |
| Node.js + npm | 20.x | Desarrollo local del frontend |
| Python + pip | 3.11 | Desarrollo local de los backends |
| FFmpeg | estable | Solo si ejecutas media-processor fuera de Docker |

## 🐛 Reportar errores y proponer funciones / Bugs & features

Usa las plantillas de Issues: [Reporte de error](.github/ISSUE_TEMPLATE/bug_report.md) ·
[Solicitud de función](.github/ISSUE_TEMPLATE/feature_request.md).
Dudas generales → GitHub Discussions / General questions → Discussions.

## 🌿 Flujo de trabajo Git / Git workflow

1. **Fork** del repositorio / Fork the repository.
2. Clona tu fork y entra al proyecto / Clone your fork.
3. Crea una rama desde `main` / Create a branch from `main`:
   - Funcionalidad / feature: `git checkout -b feature/nombre-descriptivo`
   - Corrección / fix: `git checkout -b fix/descripcion-del-bug`
4. Haz cambios pequeños y enfocados, con commits atómicos /
   Keep changes small and focused with atomic commits.
5. Valida localmente (ver abajo) antes de abrir el PR / Validate locally before opening the PR.
6. Abre el PR hacia `main` de `Llamas126/fastmedia-downloader` completando la plantilla /
   Open the PR toward `main` filling in the template.

## 🧪 Validación local / Local validation (obligatoria / mandatory)

Estos son exactamente los checks que ejecuta el CI (`.github/workflows/ci.yml`);
These are exactly the checks CI runs; your PR must pass them:

```bash
# Orquestación / orchestration
docker compose config -q
docker compose build

# Frontend — type-check TypeScript
cd services/frontend
npm ci
npx tsc --noEmit

# Backends — flake8 (errores de sintaxis y nombres indefinidos)
flake8 services/api-gateway services/media-processor \
  --count --select=E9,F63,F7,F82 --show-source --statistics
```

Prueba manual recomendada / Recommended smoke test: levanta `docker compose up`,
analiza una URL válida, descarga en `1080p` y en `Solo Audio (MP3)`, verifica el
archivo resultante / bring the stack up, analyze a valid URL, download 1080p and MP3.

## 💬 Convención de commits / Commit convention

Seguimos [Conventional Commits](https://www.conventionalcommits.org/) /
We follow Conventional Commits:

| Tipo / Type | Uso / Usage |
| --- | --- |
| `feat` | Nueva funcionalidad / new feature |
| `fix` | Corrección de bug / bug fix |
| `docs` | Documentación / documentation |
| `refactor` | Cambio interno sin alterar comportamiento / internal change, same behavior |
| `test` | Pruebas / tests |
| `perf` | Mejora de rendimiento / performance |
| `ci` | Pipelines y builds / pipelines & builds |
| `chore` | Mantenimiento / maintenance |

```bash
git commit -m "feat(gateway): agregar soporte de cookies para yt-dlp"
git commit -m "fix(frontend): corregir estado atascado al expirar un job"
```

Reglas / Rules: imperativo y presente («agregar», no «agregué»), sin punto final /
imperative mood, no trailing period. Scope sugerido / suggested scopes:
`gateway`, `processor`, `frontend`, `compose`, `ci`.

## 🎨 Estilo de código / Code style

- **Frontend**: TypeScript en modo `strict` (debe pasar `tsc --noEmit`); Tailwind CSS para estilos.
- **Backends**: Python 3.11 con type hints; sin imports sin usar; docstrings breves donde aporten.
- Evita comentarios innecesarios y cambios cosméticos no relacionados /
  Avoid unrelated cosmetic changes.

## ⚖️ Licencia / License

Al contribuir, aceptas que tus aportaciones se publiquen bajo la [licencia MIT](LICENSE) del proyecto.
By contributing you agree your contributions are licensed under the project's MIT license.
