# Experimental pipeline harness v1

This common C0-C6 harness reads research/configurations.json. Frozen treatment
artifacts must not be altered during collection.

## Preflight, tool provisioning, and warm cache

Run python3 pipeline/experiment.py preflight before every measured run. A
checksum or lineage mismatch is an EXPERIMENT_INFRASTRUCTURE_ERROR; never
substitute a newer image, ruleset, database, or configuration.

Before a C1-C6 run, provision the pinned local artifacts outside the measured
pipeline and run `python3 pipeline/provision-tools.py`. The generated
`pipeline/runtime/tool-runtime-state.json` is machine-local and ignored by Git.
The run harness performs a read-only readiness check for the tools required by
that configuration before the measured timer starts. A missing binary, image,
database, or frozen checksum fails preflight; measured scanner containers use
`--pull=never` and never install, pull, update, or replace tools. The frozen
Trivy OCI layer is checksum-verified and unpacked before measurement. C0
requires no scanner artifacts.

The current OSV-Scanner 2.6.0 CLI does not provide the frozen descriptor's
`--local-db-path` option. The provisioning report marks OSV NOT_READY, and C2-C6
are blocked before measurement until a protocol amendment resolves the frozen
CLI/database interface. Do not replace the option or use a live advisory
service without that amendment.

Run python3 pipeline/experiment.py warm separately before a measured block.
Warm-up is not a measured run. It prepares npm and Docker caches and records
the warm application, PostgreSQL, and pinned application-base image identities.
C4-C6 build the experimental image with pulling explicitly disabled so its
measured container-build timing uses the warmed local base image. Application
dependency installation remains within that predefined build boundary. Record
unavailable cache preconditions as invalid rather than mixing cache states.

## Common database and functional-test lifecycle

Every C0-C6 run creates a disposable PostgreSQL 16-alpine container and a
unique Docker volume named from the run ID. The container maps PostgreSQL to an
ephemeral loopback port, so it does not depend on a developer database or a
fixed host port. The harness waits with pg_isready, constructs a runtime-only
DATABASE_URL and TEST_DATABASE_URL, applies the existing migration, runs the
existing deterministic seed, and injects the environment into the existing
functional test process. Runtime database passwords, JWT secrets, and seed
passwords are generated per run and never written to artifacts or logs.

Setup timing is the aggregate of dependency preparation, database container
start, readiness, migration, and seed stages; each stage is also retained in
the execution record. C4-C6 additionally record the frozen application's
container build as a separate stage before Trivy. Cleanup
removes only the run-owned container and volume on success, test failure,
scanner failure, timeout, and handled interruption. Run evidence is retained.

The frozen corpus functional invariant is exactly 12 tests: 11 pass and one
fails with the title "does not disclose another user's order". This is the
retained V04 ownership regression: the vulnerable corpus returns 200 where the
secure-suite assertion expects 404. The harness accepts only that exact
one-failure summary as EXPECTED_CORPUS_TEST_FAILURE. Any other test count,
failed title, result, or inability to start tests is an unexpected functional
failure and invalidates the run.

For C6, this common lifecycle precedes a separate DAST database reset/seed.
The DAST runner creates a run-owned internal Docker network, volume, PostgreSQL
container, and API container, then verifies synthetic Alice/Bob/admin logins
and Bob's order ID before the two frozen API passes. JWTs and generated
credentials stay in process/runtime-only files and are redacted from reports.
Cleanup has per-resource timeouts and reports failures while preserving run
evidence. The DAST reset does not reuse common functional-test state.

Tool outputs use the pinned JSON treatments and are retained under each run's
`raw/` directory. Finding normalization remains unresolved by default and is
separate from the synthetic gate. Container and scanner images run with
network disabled except ZAP, which joins only the run-owned internal network
to reach the API target.

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

C0 runs common dependency, database, build, and test stages with no scanner.
C4-C6 build the application image required by Trivy, in the separately timed
container-build stage. C1-C6 enable cumulative controls from the manifest.
Native exits are recorded separately and a detection never prevents later
controls. C6 follows the
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
