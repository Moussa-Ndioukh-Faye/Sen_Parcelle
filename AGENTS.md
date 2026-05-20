# Sen_Parcelle — Agent Guide

Monorepo: Django 5 API · Flutter mobile · Angular 21 admin · Solidity/Hardhat blockchain.

## Quick start

```bash
# Backend (Poetry)
cd backend && poetry install
cp .env.example .env    # edit secrets
python manage.py migrate && python manage.py runserver

# Mobile
cd mobile && flutter pub get && flutter run
# Android emulator: --dart-define=API_URL=http://10.0.2.2:8000/api

# Web admin (Angular 21)
cd web && npm install && npm start   # → localhost:4200, proxied to :8000

# Blockchain (Hardhat ESM)
cd blockchain && npm install && npm run compile && npm test

# Full stack
docker-compose -f infra/docker/docker-compose.yml up --build
```

## Tests

| Package | Command | Notes |
|---------|---------|-------|
| Backend | `cd backend && poetry run pytest` | `DJANGO_SETTINGS_MODULE=config.settings.test` (set in pyproject.toml) |
| Backend (coverage) | `poetry run pytest --cov` | |
| Backend (single file) | `poetry run pytest apps/parcels/tests/` | |
| Mobile | `cd mobile && flutter test` | |
| Web | `cd web && npm test` | Karma + ChromeHeadless |
| Blockchain | `cd blockchain && npm test` | Hardhat, 16 tests |
| Blockchain coverage | `npm run coverage` | Hardhat coverage |

### Backend test quirks

- **PostGIS is mocked** in test settings when GDAL is unavailable (mock kicks in automatically).
- **SQLite in-memory** — no Postgres required for tests.
- **Celery runs eagerly** (`CELERY_TASK_ALWAYS_EAGER = True`) — no Redis needed.
- **S3 is disabled** — falls back to `FileSystemStorage`.

Run focused: `poetry run pytest apps/parcels/tests/test_domain.py -k test_name`

## Architecture

### Django (Clean Architecture)

```
apps/{domain}/
├── domain/          # dataclasses, value objects, business rules
├── application/     # use cases, service interfaces (lru_cache DI)
├── presentation/    # DRF ViewSets, serializers
└── infrastructure/  # adapters (Wave, Orange Money, S3, web3, SMS)
```

Settings split: `base.py` ← `development.py` / `staging.py` / `production.py` / `test.py`
Custom `AUTH_USER_MODEL = "users.User"`

### API

- `/api/` — DRF router (auth, utilisateurs, parcelles, transactions)
- `/api/health/` — health check (inline JsonResponse)
- `/api/schema/` — OpenAPI schema (drf-spectacular)
- `/api/docs/` — Swagger UI
- `/api/redoc/` — ReDoc UI
- JWT: access 15min, refresh 7d, blacklisted on rotation
- Rate limiting: `django_ratelimit` (decorators) + DRF throttling (100/h anon, 1000/h user)
- RBAC: Acheteur / Vendeur / Admin (11 permissions)

### Celery

- Queues: `blockchain`, `notifications`, `default`
- Entry: `config.celery.app`
- Beat scheduler: `django_celery_beat.schedulers:DatabaseScheduler`

### Mobile (Flutter)

- State: Riverpod + `riverpod_generator` (run `build_runner` after adding providers)
- Navigation: GoRouter
- HTTP: Dio + `pretty_dio_logger`
- Auth: `flutter_secure_storage` for tokens

### Web (Angular 21)

- Standalone components, Signals, OnPush change detection
- Dev proxy: `proxy.conf.json` → `http://localhost:8000`
- Build: `npm run build` → `dist/sen-parcelle-admin/`
- Test: Karma + Jasmine + ChromeHeadless

### Blockchain (Hardhat — ESM)

- `"type": "module"` in package.json — use `import` not `require`
- Networks: hardhat (31337) · mumbai (80001) · polygon (137)
- `npm run deploy:mumbai` / `npm run deploy:polygon`
- Solidity 0.8.20 with optimizer enabled (200 runs)

## CI/CD (GitHub Actions)

Workflow: `.github/workflows/ci.yml`
- **Backend**: ruff lint, pytest with coverage
- **Web (Angular)**: npm test + npm run build
- **Blockchain (Hardhat)**: compile + test
- **Mobile (Flutter)** : analyze + test

Code quality:
- Ruff (Python lint + format) — `poetry run ruff check .`
- Prettier (JS/TS/HTML/CSS) — `.prettierrc` at root
- ESLint (Angular/TS) — `.eslintrc.json` at root
- Solhint (Solidity) — `.solhint.json` in `blockchain/`
- Pre-commit hooks — `.pre-commit-config.yaml` at root

## Monitoring / Observabilité

- **Sentry** configuré dans `base.py` (DSN via `SENTRY_DSN` env)
- Intégrations: Django, Celery, Redis
- Staging: `config/settings/staging.py` (SQLite → Postgres, traces 0.5)

## Backups

Scripts: `infra/scripts/backup.sh` (Linux) / `backup.bat` (Windows)
- Rotation: garde les 7 derniers backups
- Rétention: supprime les backups > 30 jours

## SSL (développement)

Génération: `infra/scripts/gen-ssl-dev.sh`
- Certificats auto-signés pour localhost
- 10 ans de validité

## Key gotchas

- **`.gitignore`** has `web/` commented out — was previously blocking the web dir; `web/dist/` and `web/.angular/` are now ignored instead.
- **`django.contrib.gis`** is commented out in `base.py` by default (no GDAL dependency for local dev with SQLite). Test settings strip it too.
- **`SECRET_KEY`** must be set via env var in `base.py` — will `raise ValueError` if missing.
- **Env files** (`.env`, `.env.*`) are gitignored; only `.env.example` tracked.
- **`bandit-report.json`** at root — Python security scan artifact.
- **Android emulator** needs `--dart-define=API_URL=http://10.0.2.2:8000/api` to reach host.
