# Experimental pipeline harness v1

This common C0-C6 harness reads research/configurations.json. Frozen treatment
artifacts must not be altered during collection.

## Preflight and warm cache

Run python3 pipeline/experiment.py preflight before every measured run. A
checksum or lineage mismatch is an EXPERIMENT_INFRASTRUCTURE_ERROR; never
substitute a newer image, ruleset, database, or configuration.

Run python3 pipeline/experiment.py warm separately before a measured block.
Warm-up is not a measured run. Record unavailable cache preconditions as
invalid rather than mixing cache states.

## Smoke and measured execution

Use ./pipeline/run-experiment.sh --config C3 --run-id C3-R001 --class smoke
to verify mechanics. Without --execute this creates only smoke artifacts under
data/raw/smoke and does not execute a scanner.

The future measured interface is:

    ./pipeline/run-experiment.sh --config C3 --run-id P-C3-R001 --class pilot --execute

The harness rejects malformed, duplicate, or mismatched IDs. It preserves raw
outputs, logs, preflight, environment, timings, gate, and normalized findings
under data/raw/<class>/<run-id>. Invalid runs are retained and replacement IDs
are documented instead of overwriting history.

C0 runs common setup/build/test/container preparation with no scanner. C1-C6
enable cumulative controls from the manifest. Native exits are recorded
separately and a detection never prevents later controls. C6 follows the
frozen two-pass lifecycle documented in research/dast-test-contract-v1.md;
its outer timeout is 30 minutes.

## Normalization, mapping, and validation

pipeline/normalize_findings.py adapts Semgrep, OSV-Scanner, Gitleaks, Trivy,
Checkov, and ZAP JSON while retaining raw reports. New findings remain
UNRESOLVED; a separate manual mapping record supplies provenance and one of
the permitted classifications. The synthetic gate evaluates after all
configured controls complete.

research/pilot-schedule-v1.csv is a deterministic five-block schedule. Each
block contains C0-C6 once; configuration order rotates one place per block.
Run python3 pipeline/validate-experiment.py --schedule to validate it and
python3 pipeline/validate-experiment.py --runs for dataset structure.

Do not execute the pilot schedule until separately authorized.
