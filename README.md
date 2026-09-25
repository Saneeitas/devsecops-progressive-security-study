# DevSecOps Progressive Security Study

Baseline research repository for an empirical study of progressive security-control integration in CI/CD pipelines.

## Current phase

This repository currently contains the **clean baseline** only. Do not seed vulnerabilities or add security scanners yet; those will be introduced as controlled experimental variables.

## Included

- Research protocol with working title and four research questions
- Literature-matrix CSV template
- Node.js + TypeScript + Express baseline API
- PostgreSQL service
- Basic Vitest/Supertest tests
- Multi-stage Dockerfile
- Docker Compose for API + PostgreSQL
- Baseline GitHub Actions workflow template
- Terraform and experimental-data placeholders

## Quick start with Docker

From the repository root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:3000/
http://localhost:3000/api/health
http://localhost:3000/api/health/db
```

Stop the environment with:

```bash
docker compose down
```

To also remove the local database volume:

```bash
docker compose down -v
```

## Run locally without Docker for the API

Start PostgreSQL first (Docker is easiest):

```bash
docker compose up -d postgres
```

Then:

```bash
cd application
cp .env.example .env
npm install
npm run dev
```

## Tests and build

```bash
cd application
npm test
npm run build
```

## GitHub Actions

GitHub only discovers workflows in `.github/workflows/`. The baseline workflow is intentionally stored in `pipeline/workflows/ci.yml` to preserve the requested research structure. When ready, copy it to:

```text
.github/workflows/ci.yml
```

Do this after `npm install` has generated and committed `application/package-lock.json`, because the workflow uses `npm ci`.

## Next milestone

Confirm that:

1. `npm test` passes.
2. `npm run build` passes.
3. `docker compose up --build` starts both services.
4. `/api/health/db` reports `{"database":"connected"}`.

After that, the next research step is to freeze the baseline application architecture and design the controlled vulnerability corpus.
