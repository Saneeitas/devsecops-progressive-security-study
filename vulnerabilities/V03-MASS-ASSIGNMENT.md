# V03 — Mass Assignment

- **ID:** V03
- **Name:** Unauthorized role assignment during registration
- **Security layer:** API/object-property authorization
- **Mapping:** CWE-915; OWASP API Security API3:2023 Broken Object Property Level Authorization
- **Proposed location:** `application/src/controllers/auth.controller.ts` registration schema and `application/src/services/auth.service.ts` insert
- **Secure baseline behavior:** Registration accepts only `name`, `email`, and `password`; the database supplies the `user` role.
- **Proposed controlled mutation:** Permit a client-supplied `role` field and pass it to the insert, allowing a registrant to request `admin`. Avoid unrelated authentication changes.
- **Why selected:** Reflected XSS is not credible in a JSON-only API with no HTML sink. Protected-property mass assignment is native to this architecture and has a deterministic privilege impact.
- **Expected security-control category:** SAST, API/DAST authorization testing, and security-focused integration tests.
- **Potential scanner classes:** API schema fuzzers, property-level authorization tests, taint/data-flow SAST, and manual review.
- **Ground-truth validation:** Register a synthetic account with `"role":"admin"`, log in, and confirm access to one read-only admin endpoint. The secure oracle must reject/strip the field and return HTTP 403 on that endpoint.
- **Expected detection behavior:** Automated detection is uncertain because the weakness depends on business semantics for `role`; a generic SAST tool may not know that the property is privileged.
- **Safety considerations:** Disposable users and database; read-only admin validation; no persistent production-like data.
- **Restoration procedure:** Restore the strict registration schema and database-default role, remove any role parameter from registration, recreate the test database, and re-run authorization tests.
