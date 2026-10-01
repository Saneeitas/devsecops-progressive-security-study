# DevSecOps Progressive Security Study

A small e-commerce and order-management REST API used for the study **“Evaluating the Security Effectiveness and Operational Impact of Progressive Security Control Integration in DevSecOps Pipelines.”** It uses Node.js 22, TypeScript, Express, PostgreSQL, JWT authentication, and Docker Compose.

> This version represents the secure baseline application for the DevSecOps progressive security-control experiment. Controlled vulnerabilities and security scanning controls are intentionally excluded from this baseline.

## Requirements

- Node.js 22 and npm
- PostgreSQL 15 or later
- Docker and Docker Compose (optional for containerized setup)

## Environment configuration

For local execution, copy the application template and replace every angle-bracket placeholder:

```bash
cd application
cp .env.example .env
```

For Docker Compose, create the separate ignored repository-root environment file:

```bash
cp .env.example .env
```

Required settings are `DATABASE_URL` and a private `JWT_SECRET` containing at least 32 characters. Seeding also requires locally selected `SEED_ADMIN_PASSWORD` and `SEED_USER_PASSWORD` values. Never commit either `.env` file.

Local host execution uses PostgreSQL at `localhost:5432`. Docker Compose publishes its PostgreSQL service on host port `5433` to avoid conflicting with a locally installed server; containers communicate internally through `postgres:5432`.

## Local setup

Create the `devsecops_study` database, then install dependencies, apply the schema, and load repeatable development data:

```bash
cd application
npm ci
npm run db:migrate
npm run db:seed
npm run dev
```

The seed creates five products and these local accounts using passwords supplied through the ignored application environment file:

| Role | Email |
|---|---|
| Admin | `admin@example.com` |
| User | `alice@example.com` |
| User | `bob@example.com` |

Seed values are configured with `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, and `SEED_USER_PASSWORD`.

## Build and tests

```bash
cd application
npm run build
npm test
```

Database-backed tests should use a separate database to avoid altering development data. Export the connection URL and a generated test JWT secret rather than committing them:

```bash
export NODE_ENV=test
export TEST_DATABASE_URL='<test-database-connection-url>'
export JWT_SECRET='<generated-test-value-of-at-least-32-characters>'
npm test
```

## Docker Compose

```bash
cp .env.example .env
docker compose build
docker compose up -d postgres
docker compose run --rm api npm run db:migrate:prod
docker compose run --rm api npm run db:seed:prod
docker compose up -d
```

By default, the API is available at `http://localhost:3000` and PostgreSQL is published at `localhost:5433`. Change `API_HOST_PORT` or `POSTGRES_HOST_PORT` in the ignored root `.env` if those ports are occupied. Stop services with `docker compose down`. Use `docker compose down -v` only when you also intend to delete the Compose database volume.

Confirm that the runtime container is unprivileged:

```bash
docker compose exec api id -u
```

The command must print a nonzero UID (`1000` for the official image's `node` user).

## API endpoints

| Method | Endpoint | Access |
|---|---|---|
| GET | `/` | Public service metadata |
| GET | `/api/health` | Public application health |
| GET | `/api/health/db` | Public database health |
| POST | `/api/auth/register` | Public registration |
| POST | `/api/auth/login` | Public login |
| GET | `/api/users/me` | Authenticated user |
| PATCH | `/api/users/me` | Authenticated user |
| GET | `/api/products` | Public |
| GET | `/api/products/search?q=...` | Public |
| GET | `/api/products/:id` | Public |
| POST | `/api/orders` | Authenticated user |
| GET | `/api/orders` | Authenticated user; own orders only |
| GET | `/api/orders/:id` | Authenticated user; own order only |
| GET | `/api/admin/users` | Admin |
| GET | `/api/admin/orders` | Admin |
| POST | `/api/admin/products` | Admin |
| PATCH | `/api/admin/products/:id` | Admin |
| DELETE | `/api/admin/products/:id` | Admin |

Send JWTs as `Authorization: Bearer <token>`. Errors use a consistent `{ "error": { "code": "...", "message": "..." } }` response.

## Research constraints

This baseline uses parameterized SQL, bcrypt password hashing, JWT authentication, input validation, owner and role authorization, transactions for order creation, Helmet, and restricted CORS origins. Intentional vulnerabilities, SAST, SCA, secret scanning, container scanning, IaC scanning, and DAST are reserved for later controlled experiment stages and are not included here.
