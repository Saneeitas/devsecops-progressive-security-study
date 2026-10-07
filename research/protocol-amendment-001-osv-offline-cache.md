# Protocol Amendment PA-001: OSV-Scanner 2.6.0 offline cache

## Identification

- **Amendment ID:** PA-001
- **Affected control:** C2 / OSV-Scanner SCA (also enabled cumulatively in C3–C6)
- **Scanner:** OSV-Scanner 2.6.0
- **Discovery phase:** implementation/runtime preflight
- **Timing:** identified before any OSV scan of corpus-v1 and before pilot or final data collection

## Original specification and problem

The original frozen treatment specified `--local-db-path` as its local
database mechanism. The exact frozen OSV-Scanner 2.6.0 binary does not expose
that flag in `scan source --help`; the prescribed invocation cannot be used
as written. This interface incompatibility was found during runtime preflight,
before observing any OSV detection result.

## Investigation evidence

Investigation used the exact local OSV-Scanner 2.6.0 binary (which reports
osv-scalibr 0.5.2), the frozen npm `all.zip`, and a disposable synthetic npm
lockfile. The test ran in a temporary directory with network access blocked.
It did not use `application/package-lock.json`, any other corpus file, or any
V01–V12 target. The exact binary loaded the unchanged archive from
`<controlled-cache-root>/osv-scalibr/npm/all.zip` and completed the synthetic
lockfile operation in offline mode. The temporary fixture and cache paths were
removed after the test.

The archive identity remains:

- GCS generation: `1790875957849873`
- Size: `217297800` bytes
- MD5 (base64): `tkWSeWnYUpzWbsr9u+8lXA==`
- SHA-256 (local verification): `44f5dbed8f6f5b71b086b8eb17b4b728fac2257d842d3335a7ba72a9408b0792`

The OSV descriptor changed from SHA-256
`4a9f30db6f3a81535c03d2a885a2ad182ba50fd94dda1f6a7def6a9beac33014` to
`5dad87805ec759b393d514c1cfe7b3b89f299286856acc6383994619fddc3e57` to
record the supported cache interface. The archive's size and checksums were
verified unchanged before and after staging it at the corrected cache path.

The official OSV-Scanner 2.6.0 offline documentation describes the
`OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY` environment variable, but describes a
cache child directory named `osv-scanner/`. The exact frozen binary
mechanically loaded the database from a child named `osv-scalibr/`. This
documentation/runtime layout discrepancy is retained here rather than
silently assuming the documented subdirectory. See the
[official 2.6.0 offline-mode documentation](https://github.com/google/osv-scanner/blob/v2.6.0/docs/offline-mode.md).

## Corrected treatment

For measured or smoke execution, the harness will:

1. Use the controlled experiment cache root `${DEVSECOPS_RUNTIME_ROOT}/cache/osv`.
2. Set `OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY` to that root.
3. Make the unchanged frozen archive available at
   `<controlled-cache-root>/osv-scalibr/npm/all.zip`.
4. Invoke OSV-Scanner 2.6.0 against only `application/package-lock.json`, in
   JSON format, with `--offline` and the existing `--offline-vulnerabilities`
   flag.
5. Never pass `--local-db-path` or `--download-offline-databases`.

Offline mode is required so the measured invocation cannot use network-based
features. The frozen archive is provisioned and verified before the measured
timer begins; the measured process must not download or refresh advisory data.

The corrected invocation pattern is:

```sh
OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY="$OSV_CACHE_ROOT" \
  osv-scanner scan source \
    --lockfile application/package-lock.json \
    --format json \
    --output-file artifacts/osv-scanner.json \
    --offline \
    --offline-vulnerabilities
```

Here `$OSV_CACHE_ROOT/osv-scalibr/npm/all.zip` is the verified frozen archive.

## Methodological impact

Changed:

- OSV CLI/cache implementation
- Runtime advisory archive placement

Unchanged:

- OSV-Scanner version 2.6.0
- Advisory dataset, GCS generation, and archive bytes/checksums
- Target `application/package-lock.json`
- C2 SCA purpose and C0–C6 cumulative configuration design
- Vulnerability corpus and expected ground truth
- Timing boundaries and gate policy
- All other scanner treatments, OpenAPI, DAST behavior, and V01–V12
- Pilot schedule

PA-001 was established before any OSV corpus outcome was observed and before
pilot/final collection. It was not motivated by detection performance. It
corrects the executable cache interface while preserving the planned SCA
question and advisory source.
