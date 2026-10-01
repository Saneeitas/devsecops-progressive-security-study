# V01 — SQL Injection

- **ID:** V01
- **Name:** SQL injection in product search
- **Security layer:** Application/source and database access
- **Mapping:** CWE-89; OWASP Top 10 A03:2021 Injection
- **Proposed location:** `application/src/services/product.service.ts`, the search branch of `listProducts(search)`
- **Secure baseline behavior:** The `ILIKE` predicates use `$1`, and the wildcard search value is supplied separately to `pool.query`.
- **Proposed controlled mutation:** In the experimental branch only, interpolate the validated `search` string into the two `ILIKE` predicates instead of binding `$1`. Keep the route and response shape unchanged so the query construction is the sole intended mutation.
- **Why selected:** Product search is a natural user-controlled database flow and provides a compact comparison between safe parameter binding and unsafe query construction.
- **Expected security-control category:** SAST and DAST/API security testing.
- **Potential scanner classes:** Taint-based SAST, pattern-based SAST, SQL-injection DAST, and manual code review.
- **Ground-truth validation:** Against a disposable database, use a non-destructive boolean payload that changes the number of returned products. Capture the normal and mutated responses plus database logs. Do not use data-changing or stacked-query payloads.
- **Expected detection behavior:** SAST should identify query-string construction from request input; DAST may identify response differences. Either may miss it because the value crosses controller/service boundaries or PostgreSQL syntax differs from generic payloads.
- **Safety considerations:** Synthetic data only; least-privileged database account; no stacked statements; reset the database after validation.
- **Restoration procedure:** Restore the `$1` placeholders and values array from `secure-baseline-v2`, rebuild, and verify that the boolean canary is treated as text and normal search tests pass.
