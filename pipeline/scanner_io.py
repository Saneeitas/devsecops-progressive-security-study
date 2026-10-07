"""Strict scanner report paths and JSON validation for frozen treatments."""
from __future__ import annotations

import json
from pathlib import Path

CHECKOV_REPORT_FILENAME = "results_json.json"


def resolve_checkov_report(output_dir: Path) -> Path:
    """Resolve Checkov's concrete JSON file; reject missing/ambiguous output."""
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        raise ValueError(f"Checkov output path is not a directory: {output_dir}")
    entries = sorted(output_dir.iterdir(), key=lambda item: item.name)
    expected = output_dir / CHECKOV_REPORT_FILENAME
    if len(entries) != 1 or entries[0] != expected or not expected.is_file():
        names = [item.name for item in entries]
        raise ValueError(
            "Checkov must produce exactly "
            f"{CHECKOV_REPORT_FILENAME}; found {names}"
        )
    return expected


def load_json_report(path: Path) -> object:
    """Load one concrete JSON file and reject directories or malformed JSON."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"scanner input must be a concrete report file: {path}")
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid scanner JSON report {path}: {error}") from error


def validate_report(tool: str, document: object) -> None:
    """Validate minimal native structure before normalization."""
    if tool == "checkov":
        if not isinstance(document, dict):
            raise ValueError("Checkov report root must be an object")
        results = document.get("results")
        if not isinstance(results, dict) or not isinstance(results.get("failed_checks"), list):
            raise ValueError("Checkov report must contain results.failed_checks array")
        if any(not isinstance(item, dict) for item in results["failed_checks"]):
            raise ValueError("Checkov failed_checks entries must be objects")
    elif tool == "trivy":
        if not isinstance(document, dict) or "SchemaVersion" not in document or "ArtifactType" not in document:
            raise ValueError("Trivy report must contain SchemaVersion and ArtifactType")
        results = document.get("Results") or []
        if not isinstance(results, list):
            raise ValueError("Trivy Results must be an array when present")
        for result in results:
            if not isinstance(result, dict):
                raise ValueError("Trivy Results entries must be objects")
            vulnerabilities = result.get("Vulnerabilities")
            if vulnerabilities is not None and not isinstance(vulnerabilities, list):
                raise ValueError("Trivy Vulnerabilities values must be arrays or null")
