# PA-003 final-study environment controls

**APPROVED — PA-003 — October 10, 2026**

Source-document provenance: explicit PI declaration in the ChatGPT research conversation on October 10, 2026; based on the revised PA-003 package and approved-candidate schedule.

Use the controlled Mac/Docker environment, frozen artifacts, pinned images, and controlled warm-cache policy. Docker Resource Saver remains disabled; Docker allocation is unchanged. Before each run check Docker/image/cache references, disk space, host contention, and stale experiment-owned resources.

Use AC power and process-bound sleep prevention outside measured timing where supported. Record power, readiness delay, competing activity, Docker restart, cache state, source commit, image identity, scheduled position, and predecessor. Host deviations are retained and reported; they justify replacement only when they cause a frozen invalidity condition. CPU/peak-memory remains null unless separately approved calibration is adopted.
