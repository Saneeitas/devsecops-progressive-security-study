#!/usr/bin/env python3
"""Verify and install the frozen Trivy DB OCI layer into the local cache.

This is provisioning-time work, never part of a measured pipeline run.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

from tool_runtime import ROOT, RUNTIME_ROOT, digest


def main() -> int:
    descriptor = json.loads((ROOT / "pipeline/security/trivy-database-v1.json").read_text())
    archive = RUNTIME_ROOT / "cache/trivy/db-layer.tar.gz"
    target = RUNTIME_ROOT / "cache/trivy/db"
    if not archive.is_file():
        raise SystemExit(f"frozen Trivy DB layer is missing: {archive}")
    actual_layer = f"sha256:{digest(archive)}"
    if actual_layer != descriptor["layer_digest"]:
        raise SystemExit("frozen Trivy DB layer checksum mismatch")
    if archive.stat().st_size != descriptor["layer_size_bytes"]:
        raise SystemExit("frozen Trivy DB layer size mismatch")

    with tarfile.open(archive, "r:gz") as layer:
        members = layer.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not (member.isfile() or member.isdir()):
                raise SystemExit("Trivy DB archive contains an unsafe or unsupported member")
        layer.extractall(target, filter="data")

    database = target / "trivy.db"
    metadata = target / "metadata.json"
    if not database.is_file() or not metadata.is_file():
        raise SystemExit("frozen Trivy layer did not contain expected DB files")
    observed = json.loads(metadata.read_text())
    if observed.get("Version") != 2 or not observed.get("UpdatedAt"):
        raise SystemExit("frozen Trivy DB metadata is incomplete or unexpected")
    receipt = {
        "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "artifact_digest": descriptor["artifact_digest"],
        "layer_digest": actual_layer,
        "layer_size_bytes": archive.stat().st_size,
        "metadata_sha256": digest(metadata),
        "database_sha256": digest(database),
        "observed_metadata": observed,
        "java_database": "not provisioned; frozen treatment disables Java DB",
    }
    (target / "provenance.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "READY", "layer_digest": actual_layer, "database_sha256": receipt["database_sha256"], "metadata": observed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
