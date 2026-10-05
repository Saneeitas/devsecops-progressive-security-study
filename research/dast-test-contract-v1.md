# Authenticated DAST Test Contract v1

## Fixed treatment

OWASP ZAP 2.17.0 API Scan consumes `pipeline/security/openapi-corpus-v1.yaml` against only `http://api:3000` on the isolated Compose network. The contract, dataset, context, add-ons, rules, image, reports, and timeout are frozen before observing results. No cloud or external target is permitted.

## Reset and preconditions

Before each DAST run, destroy the disposable database volume, recreate PostgreSQL, apply the existing schema, and execute the existing seed once with generated per-run `SEED_ADMIN_PASSWORD`, `SEED_USER_PASSWORD`, and `JWT_SECRET`. Confirm health and the expected identifiers in `dast-dataset-v1.json`; abort on drift.

Log in as Bob and create exactly one order for product ID 1, quantity 1. A clean reset makes this order ID 1. Log in as Alice and the seeded admin and retain their JWTs only in masked runtime environment/files. Never commit tokens/passwords or include authorization headers in reports.

## Authentication passes

C6 comprises two predetermined ZAP API Scan passes within one measured DAST stage:

1. **User pass:** inject Alice's bearer token. It covers public and normal-user operations and supplies order ID 1 to `GET /api/orders/{id}`.
2. **Admin pass:** inject the seeded admin bearer token. It covers the same immutable contract, including admin-only routes. Responses caused solely by using an inappropriate role for a route are normalized once, not counted as duplicate vulnerabilities.

Authentication is performed by a pre-scan orchestration hook calling `/api/auth/login`; ZAP receives only the resulting bearer header through the frozen declarative context at `pipeline/security/zap-context-v1.json`, rendered at runtime without persisting tokens. The hook may substitute runtime tokens and the fixed target URL but may not change payload schemas, identifiers, rules, or endpoints. Failed login or fixture assertions fail setup before DAST timing/results.

## V03 testability decision

The frozen OpenAPI registration schema includes the optional `role` property with its actual `user`/`admin` enum because that accurately represents corpus-v1. Generic ZAP API Scan is therefore theoretically capable of submitting the property, but no V03-specific exploit script, forced `admin` payload, or post-result rule is included. Detection is classified as **possible**, not expected. If generic generation never selects the privileged value, that is a treatment limitation fixed before experimentation.

## V04/BOLA testability decision

The fixture explicitly represents User A (Alice), User B (Bob), Bob's order, and Alice requesting Bob's order ID. The user pass uses Alice's bearer token and the OpenAPI path parameter has deterministic example/default `1`, which belongs to Bob after the asserted clean reset. This generic deterministic precondition hook is frozen now and may not be altered after results.

This makes the vulnerable cross-user request reachable, but standard ZAP does not inherently understand ownership semantics or compare a secure oracle. V04 detection remains **possible**, not guaranteed. No bespoke alert is created if ZAP fails to recognize the response.

## Other deterministic inputs

- Users: admin ID 1, Alice ID 2, Bob ID 3 after clean reset.
- Products: IDs 1–5 in existing seed order.
- Bob order: ID 1 with product ID 1 and quantity 1.
- Public search example: `keyboard`.
- Diagnostics example: `localhost`; the canary enum remains represented accurately, but no exploit-specific forcing is added.
- Generated registration email uses the reserved `.invalid` domain and a per-run suffix if uniqueness is required.

Mutating operations can change state within a pass. Each complete DAST run starts from a fresh reset; pass order is always user then admin. A failed or timed-out run is not resumed against dirty state.

## Reporting and safety

Each pass emits JSON. The outer DAST stage timeout is 30 minutes; packaged-scan startup/passive timeout is 15 minutes. All release and beta rules present in the frozen image are WARN unless the frozen rule file states otherwise; alpha rules and add-on updates are disabled. Native exit codes are recorded, later stages continue safely, and the final gate is derived after both passes. Raw artifacts redact tokens and contain no committed secrets.
