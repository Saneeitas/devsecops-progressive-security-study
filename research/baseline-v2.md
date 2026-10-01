# Secure Baseline v2 Verification Record

## Identity

- **Baseline name:** `secure-baseline-v2`
- **Verification date:** 2026-09-30
- **Purpose:** Final secure experimental control before any V01–V12 mutation or progressive security-control integration
- **Deployment status:** Verified locally and with Docker Compose; Terraform fixtures validated statically and not deployed

## Application stack

- Node.js, TypeScript, Express, PostgreSQL
- JWT authentication with an environment-supplied signing secret
- bcrypt password hashing
- Zod request validation
- Helmet security headers and configured CORS
- Role and object-owner authorization
- Parameterized PostgreSQL queries
- Transactional order creation

## Verified versions and artifacts

- **Local Node.js:** 22.14.0
- **Container Node.js:** 22.22.3
- **PostgreSQL container:** 16.15
- **Docker base image:** `node:22-alpine3.22`
- **Resolved Node base digest:** `sha256:cd7807368cf24826297cbad5dca1a44972ccfd770647db52a8c7589eb4599ac8`
- **Resolved PostgreSQL image digest:** `sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea`
- **Built API image:** `sha256:f2e2cbcc7223cb1385b838b29e10e35cc52290e3f0b14300e0e097a775892a00`
- **Terraform CLI:** 1.14.8
- **Terraform AWS provider:** 6.66.0, recorded in `.terraform.lock.hcl`

## Container and dependency controls

- The runtime declares `USER node` and executes as UID/GID 1000.
- Compiled application and schema files are copied with `node:node` ownership.
- Both Docker stages use `npm ci`; the runtime stage uses `npm ci --omit=dev`.
- CI uses `npm ci` and obtains database/JWT values from repository secrets.
- Compose requires database and JWT values through environment substitution; tracked templates contain placeholders only.
- `.env` and `application/.env` remain gitignored.

## Verification results

- TypeScript build: passed
- Automated tests: 12 passed across 2 test files
- npm audit: 0 known vulnerabilities
- Database migration: passed locally and in the runtime image
- Repeatable seed: passed locally and in the runtime image with environment-supplied passwords
- Local API: health, database health, registration, login, profile, products, search, order creation/listing, and authorization passed
- Docker image build: passed
- Docker Compose: API running on verification host port 3101; PostgreSQL healthy on host port 5433
- Docker API: health, database health, authentication, profile, products, search, order creation/retrieval, unauthenticated rejection, and normal-user admin rejection passed
- Runtime identity: `uid=1000(node) gid=1000(node)`
- Terraform format check: passed
- Terraform initialization without backend: passed
- Terraform validation: passed
- Terraform apply: not run

## Secure Terraform fixture summary

- **S3:** all public-access-block flags enabled, bucket-owner ownership enforced, no public policy/ACL, AES-256 server-side encryption enabled
- **Security group:** SSH limited to validated `admin_cidr`; `0.0.0.0/0` is rejected
- **IAM:** only `s3:GetObject` on the fixture bucket's `products/*` path; no wildcard action or resource
- **EBS:** encryption explicitly enabled

## Known limitations

- Node and PostgreSQL Compose references remain readable version tags rather than immutable digests. Record resolved digests for each experimental run.
- Terraform resources are static research fixtures and were not planned or applied against an AWS account.
- The fixture S3 bucket name, VPC ID, region, and availability zone are synthetic and would require approved organization-specific values before any deployment.
- JWT role claims remain valid until token expiry, so database-side role changes are not immediate.
- GitHub CI requires `BASELINE_TEST_DATABASE_PASSWORD` and `BASELINE_TEST_JWT_SECRET` repository secrets before the template workflow can run.
- Port 3000 was occupied during local verification, so the local API used 3100 and Docker Compose used the supported `API_HOST_PORT=3101` override.

## Corpus state

This baseline contains no intentionally seeded V01–V12 vulnerabilities. Every entry in `vulnerabilities/manifest.json` remains `designed`. No vulnerability injection or security scanner integration was performed during baseline v2 hardening.
