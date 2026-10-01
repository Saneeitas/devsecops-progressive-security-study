# Raw experimental data

Raw data is intentionally empty until experimental execution begins.

```text
data/raw/
├── pilot/
│   └── P-C<configuration>-R<run-number>/
└── final/
    └── C<configuration>-R<run-number>/
```

Each run directory will contain one `run.json` validated by `data/schema/run.schema.json`, normalized findings (one JSON object per finding or an array validated item-by-item against `finding.schema.json`), and immutable native tool artifacts. Pilot IDs use `P-C0-R001`; final IDs use `C0-R001`. Pilot and final data must never be combined.

Raw outputs are append-only. Corrections belong in versioned derived data with provenance rather than overwriting source artifacts. Do not commit credentials, environment secrets, or deployed cloud state. Each record must identify corpus and pipeline commits, exact tools, cache condition, timestamps, and success/failure.
