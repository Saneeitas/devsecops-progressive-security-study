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

## Common database and functional-test lifecycle

Every C0-C6 run creates a disposable PostgreSQL 16-alpine container and a
unique Docker volume named from the run ID. The container maps PostgreSQL to an
ephemeral loopback port, so it does not depend on a developer database or a
fixed host port. The harness waits with pg_isready, constructs a runtime-only
DATABASE_URL and TEST_DATABASE_URL, applies the existing migration, runs the
existing deterministic seed, and injects the environment into the existing
functional test process. Runtime database passwords, JWT secrets, and seed
passwords are generated per run and never written to artifacts or logs.

Setup timing is the aggregate of container start, readiness, migration, and
seed stages; each stage is also retained in the execution record. Cleanup
removes only the run-owned container and volume on success, test failure,
scanner failure, timeout, and handled interruption. Run evidence is retained.

The frozen corpus functional invariant is exactly 12 tests: 11 pass and one
fails with the title "does not disclose another user's order". This is the
retained V04 ownership regression: the vulnerable corpus returns 200 where the
secure-suite assertion expects 404. The harness accepts only that exact
one-failure summary as EXPECTED_CORPUS_TEST_FAILURE. Any other test count,
failed title, result, or inability to start tests is an unexpected functional
failure and invalidates the run.

For C6, this common lifecycle precedes the separate frozen DAST reset. The
DAST contract then performs its own fresh reset/seed immediately before its
two API passes; it does not reuse state from functional tests.

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
