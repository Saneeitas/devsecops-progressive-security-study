# V05 — Hardcoded Secret

- **ID:** V05
- **Name:** Hardcoded non-functional research token
- **Security layer:** Source/secrets
- **Mapping:** CWE-798
- **Proposed location:** A future `application/src/config/research-fixture.ts` used only on the V05 mutation branch
- **Secure baseline behavior:** JWT and database secrets are read from environment variables; `.env` is ignored.
- **Proposed controlled mutation:** Commit `RESEARCH_ONLY_FAKE_TOKEN` with the GitHub classic-token prefix (`ghp_`) followed by exactly 36 zero characters. The complete detector-shaped value is deliberately not written in this design document. The future value will be all-zero, non-functional, and labelled as research data.
- **Why selected:** It supplies deterministic secret-scanning ground truth without exposing or creating a usable credential.
- **Expected security-control category:** Secret scanning and source review.
- **Potential scanner classes:** Regex/entropy secret scanners, provider-pattern scanners, pre-commit hooks, and repository-history scanners.
- **Ground-truth validation:** Confirm the exact literal is present in the mutation commit and that the selected scanner reports its file/line. Do not attempt authentication with it.
- **Expected detection behavior:** Provider-pattern scanners may flag the `ghp_` shape; entropy-only tools may miss the all-zero body. That difference is an intended measurement.
- **Safety considerations:** Never substitute a generated, active, or previously used token. Do not register the fake value with any service.
- **Restoration procedure:** Remove the fixture and its commit/history reference in the experimental branch, then verify repository and history scans no longer report the token in the restored snapshot.
