# V04 — Broken Object Level Authorization

- **ID:** V04
- **Name:** Cross-user order retrieval
- **Security layer:** API/authorization
- **Mapping:** CWE-639 (Authorization Bypass Through User-Controlled Key), CWE-862; OWASP API1:2023 Broken Object Level Authorization
- **Proposed location:** `application/src/services/order.service.ts`, `getOrder(userId, orderId)`
- **Secure baseline behavior:** The query requires both `o.user_id = $1` and `o.id = $2`; an authenticated non-owner receives HTTP 404.
- **Proposed controlled mutation:** Remove only the user-owner predicate and query by order ID while leaving authentication and ID validation intact.
- **Why selected:** Sequential order IDs and an existing two-user test create a realistic, isolated horizontal authorization failure.
- **Expected security-control category:** API/DAST authorization testing, SAST, and integration tests.
- **Potential scanner classes:** Authenticated API scanners with two sessions, authorization test harnesses, semantic SAST, and manual review.
- **Ground-truth validation:** User A creates an order; user B requests its ID. The vulnerable oracle returns HTTP 200 with A's order, while the secure oracle returns HTTP 404.
- **Expected detection behavior:** Multi-user DAST should detect it. Single-session scanners and syntax-only SAST are likely to miss the missing business predicate.
- **Safety considerations:** Synthetic accounts/orders only; do not validate against real user data; retain request/response evidence without JWTs.
- **Restoration procedure:** Restore the owner predicate and parameter order from `secure-baseline-v2`, then run the cross-user order test and require HTTP 404.
