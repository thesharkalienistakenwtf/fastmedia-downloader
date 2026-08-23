## 📝 Descripción / Description

<!-- Qué cambia este PR y por qué. Referencia issues con "Fixes #N" o "Closes #N".
     What this PR changes and why. Reference related issues with "Fixes #N". -->

## 🔖 Tipo de cambio / Type of change

- [ ] 🐛 Corrección de bug / Bug fix
- [ ] ✨ Nueva funcionalidad / New feature
- [ ] ♻️ Refactor (sin cambio de comportamiento / no behavior change)
- [ ] 📝 Documentación / Documentation
- [ ] 🔧 CI / build / tooling
- [ ] Otro / Other:

## 🧩 Servicio(s) afectado(s) / Affected service(s)

- [ ] Frontend (`services/frontend`)
- [ ] API Gateway (`services/api-gateway`)
- [ ] Media Processor (`services/media-processor`)
- [ ] Orquestación / docs (`docker-compose.yml`, README, …)

## ✔️ Checklist de validación local / Local validation checklist

<!-- Mismos checks que el CI (.github/workflows/ci.yml): deben pasar los que apliquen.
     Same checks CI runs: the applicable ones must pass. -->
- [ ] `docker compose build` compila correctamente / builds successfully
- [ ] `npx tsc --noEmit` pasa (si tocaste el frontend / if frontend touched)
- [ ] `flake8 --select=E9,F63,F7,F82` pasa (si tocaste un backend / if a backend touched)
- [ ] Commits siguen [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] Probé el flujo analizar → elegir formato → descargar (si aplica / if applicable)

## ➕ Contexto adicional / Additional context

<!-- Capturas, notas de despliegue, riesgos conocidos.
     Screenshots, deployment notes, known risks. -->
