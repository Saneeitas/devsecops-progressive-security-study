# V08 — Container Running as Root

- **ID:** V08
- **Name:** Runtime container executes with unnecessary root privileges
- **Security layer:** Container configuration
- **Mapping:** CWE-250 (Execution with Unnecessary Privileges); OWASP Docker Security guidance
- **Proposed location:** Runtime stage of `application/Dockerfile`
- **Secure baseline behavior:** Secure baseline v2 uses `USER node`, owns copied runtime files as `node:node`, and must execute with UID 1000 rather than UID 0.
- **Proposed controlled mutation:** Remove only the runtime `USER node` instruction so the experimental image falls back to root execution.
- **Why selected:** Root execution is a common container-hardening control and has a simple configuration oracle, but research integrity requires a truly secure comparison state.
- **Expected security-control category:** Dockerfile/IaC scanning and runtime policy enforcement.
- **Potential scanner classes:** Dockerfile linters, container configuration scanners, admission policies, and runtime identity checks.
- **Ground-truth validation:** Run `id -u` inside the container. The corrected baseline must return a nonzero UID; the V08 mutation must return `0`.
- **Expected detection behavior:** Static tools commonly detect a missing/non-root `USER`; runtime controls should observe UID 0. Some image CVE scanners do not inspect this configuration.
- **Safety considerations:** Do not run the future root mutation with host mounts, privileged mode, host namespaces, or sensitive sockets.
- **Restoration procedure:** Restore `USER node` and `node:node` runtime file ownership from secure baseline v2, rebuild, and require UID 1000 plus passing API tests.
