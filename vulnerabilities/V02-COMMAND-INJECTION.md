# V02 — Command Injection

- **ID:** V02
- **Name:** OS command injection in research diagnostics
- **Security layer:** Application/source and operating-system interaction
- **Mapping:** CWE-78; OWASP Top 10 A03:2021 Injection
- **Proposed location:** A future admin-only `GET /api/admin/diagnostics/ping?host=...` route, controller, and `application/src/services/diagnostics.service.ts`
- **Secure baseline behavior:** No process-spawning or shell-execution API exists.
- **Proposed controlled mutation:** First define the experimental operation with strict host validation and `execFile` argument separation; the vulnerable mutation would replace it with `exec` and shell interpolation. This endpoint must exist only on the isolated mutation branch.
- **Why selected:** It models a realistic operational diagnostic feature without altering an existing business endpoint and creates a clear source-to-shell data flow.
- **Expected security-control category:** SAST and DAST/API security testing.
- **Potential scanner classes:** Taint-based SAST, dangerous-API rules, DAST with authenticated requests, and runtime monitoring.
- **Ground-truth validation:** Use only a benign canary such as appending a command that prints `V02_CANARY`; assert that the marker appears in the vulnerable response/log and never in the secure variant.
- **Expected detection behavior:** SAST should flag user input reaching `child_process.exec`. DAST may miss the route because it requires an admin JWT or because command output is not reflected.
- **Safety considerations:** Disposable non-root container, read-only filesystem, no mounted host paths, no secrets, no cloud metadata access, restricted egress, CPU/time limits, and an allowlisted benign validation payload. Never expose the endpoint outside the research network.
- **Restoration procedure:** Remove the research diagnostics route/service or restore the validated `execFile` implementation, then verify the canary is rejected and no shell is invoked.
