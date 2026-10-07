"""Read-only gate for pre-provisioned experimental security tools."""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("DEVSECOPS_RUNTIME_ROOT", Path.home() / ".local/share/devsecops-study-runtime"))
STATE = ROOT / "pipeline/runtime/tool-runtime-state.json"
CONTROL_TOOLS = {"SAST": "semgrep", "SCA": "osv", "SECRET_SCANNING": "gitleaks", "CONTAINER_SCANNING": "trivy", "IAC_SCANNING": "checkov", "DAST": "zap"}
TOOL_ARTIFACTS = {"semgrep": ["semgrep_rules"], "osv": ["osv_database"], "gitleaks": ["gitleaks_config"], "trivy": ["trivy_database"], "checkov": ["checkov_config"], "zap": ["zap_inventory", "openapi", "zap_context"]}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def directory_digest(path: Path) -> str:
    entries = [f"{digest(f)}  {f.relative_to(path).as_posix()}\n" for f in sorted(path.rglob("*.yaml"))]
    return hashlib.sha256("".join(entries).encode()).hexdigest()

def resolve_runtime_path(value):
    if value and str(value).startswith("${DEVSECOPS_RUNTIME_ROOT}"):
        return str(RUNTIME_ROOT) + str(value).removeprefix("${DEVSECOPS_RUNTIME_ROOT}")
    return value

def artifact_ready(record):
    path = resolve_runtime_path(record.get("runtime_path"))
    if not path:
        return False
    kind = record.get("kind")
    if kind == "file":
        f = Path(path)
        if not f.is_file():
            return False
        if record.get("observed_sha256") and digest(f) != record["observed_sha256"]:
            return False
        if record.get("expected_size_bytes") is not None:
            raw = f.read_bytes()
            md5 = base64.b64encode(hashlib.md5(raw).digest()).decode()
            if len(raw) != record["expected_size_bytes"] or md5 != record.get("expected_md5_base64"):
                return False
        return True
    if kind == "directory":
        folder = Path(path)
        return folder.is_dir() and directory_digest(folder) == record.get("expected_sha256")
    if kind == "metadata":
        meta = Path(path)
        dbfile = meta.parent / "trivy.db"
        archive = meta.parent.parent / "db-layer.tar.gz"
        if not meta.is_file() or not dbfile.is_file():
            return False
        try:
            data = json.loads(meta.read_text())
            receipt = json.loads((meta.parent / "provenance.json").read_text())
            layer_ok = (archive.is_file()
                        and f"sha256:{digest(archive)}" == record.get("expected_layer_digest")
                        and archive.stat().st_size == record.get("expected_layer_size_bytes"))
            return (
                layer_ok
                and data.get("Version") == 2
                and receipt.get("artifact_digest") == record.get("expected_artifact_digest")
                and receipt.get("layer_digest") == record.get("expected_layer_digest")
                and receipt.get("metadata_sha256") == digest(meta)
                and receipt.get("database_sha256") == record.get("trivy_db_sha256")
                and (not record.get("trivy_db_sha256") or digest(dbfile) == record["trivy_db_sha256"])
            )
        except Exception:
            return False
    if kind == "repo_file":
        f = Path(path)
        return f.is_file() and digest(f) == record.get("expected_sha256")
    return False

def runtime_preflight(controls):
    """Check readiness state and current local inputs; never downloads or updates."""
    required = sorted({CONTROL_TOOLS[x] for x in controls if x in CONTROL_TOOLS})
    checked_at = dt.datetime.now(dt.timezone.utc).isoformat()
    if not required:
        return {"status": "PASS", "required": [], "checked_at": checked_at, "tools": []}
    try:
        state = json.loads(STATE.read_text())
    except Exception as error:
        return {"status": "FAIL", "required": required, "checked_at": checked_at, "error": f"runtime state unavailable: {error}", "tools": []}
    checks = []
    for name in required:
        item = state.get("tools", {}).get(name, {})
        ok = item.get("status") == "READY"
        path = resolve_runtime_path(item.get("runtime_path"))
        kind = item.get("kind")
        if kind == "executable":
            executable = Path(path or "")
            ok = ok and executable.is_file() and os.access(executable, os.X_OK)
            if ok and item.get("observed_sha256"):
                ok = digest(executable) == item["observed_sha256"]
            if ok and item.get("dependency_lock_sha256"):
                try:
                    pip = subprocess.run([str(RUNTIME_ROOT / "venv/checkov/bin/python"), "-m", "pip", "freeze"], capture_output=True, text=True, timeout=30)
                    observed = hashlib.sha256(pip.stdout.strip().encode()).hexdigest()
                    ok = pip.returncode == 0 and observed == item["dependency_lock_sha256"]
                except Exception:
                    ok = False
        elif kind == "image":
            try:
                inspected = subprocess.run(["docker", "image", "inspect", path, "--format", "{{json .RepoDigests}} {{.Os}}/{{.Architecture}}"], capture_output=True, text=True, timeout=20)
                expected_digest = item.get("expected_platform_manifest_digest") or item.get("expected_sha256")
                ok = ok and inspected.returncode == 0 and expected_digest.removeprefix("sha256:") in inspected.stdout and "linux/amd64" in inspected.stdout
            except Exception:
                ok = False
        else:
            ok = False
        artifact_checks = []
        for artifact in TOOL_ARTIFACTS.get(name, []):
            record = state.get("artifacts", {}).get(artifact, {})
            valid = record.get("status") == "READY" and artifact_ready(record)
            artifact_checks.append({"artifact": artifact, "status": "READY" if valid else "NOT_READY", "path": resolve_runtime_path(record.get("runtime_path"))})
            ok = ok and valid
        if name == "zap":
            ok = ok and item.get("addon_inventory_match") is True
        if name == "osv":
            ok = ok and item.get("required_frozen_flags_verified") is True
        checks.append({"tool": name, "status": "READY" if ok else "NOT_READY", "version": item.get("observed_version"), "runtime_path": path, "artifacts": artifact_checks, "reason": None if ok else item.get("reason", "runtime artifact missing, stale, or changed")})
    frozen_ok = state.get("frozen_inputs_status") == "READY"
    return {"status": "PASS" if frozen_ok and all(x["status"] == "READY" for x in checks) else "FAIL", "frozen_inputs_status": "READY" if frozen_ok else "NOT_READY", "required": required, "checked_at": checked_at, "tools": checks}
