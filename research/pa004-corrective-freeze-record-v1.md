# PA-004 corrective-freeze record v1

- **Corrective protocol record:** PA-004, approved October 11, 2026
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Governance:** independent, PI-led
- **Original PA-003 freeze commit:** `d9fa60ebfd249290aa0e0049b89116258046de70`
- **Original PA-003 tag:** `final-study-pa003-v1`
- **Approved final schedule SHA-256:** `92736c0e80b4104fbccec0fa3a4ce420266fa36215ba05094bdac9afea61f42d`

## Correction identity

PA-004 corrects the post-freeze global dataset-validator identity from `run_id` to `(classification, run_id)`. This permits the separately namespaced smoke, pilot, and final datasets to contain an identical ID string while retaining rejection of a duplicate in the same classification.

| Artifact | SHA-256 |
|---|---|
| Pre-correction validator recorded by PA-003 freeze manifest | `de840910cf77d8bdf0d7fad35527aa551a3c90ce583b7aa852f0aa677e51f1b9` |
| PA-004 corrected validator | `3764eb44a988ab8821cd3bef8dfee18fd717d076aed8132ab450a025e1212943` |
| PA-004 namespace regression test | `ca212da460adfec023ea57e21baaa2c607ad4a022ad723042fa6c6ca175c4679` |
| Approved PA-004 amendment | `760b4fb0fa6e103c2236127a9a278a2120e086b7e6c392015f9673cc8d1feb9d` |
| Incomplete Block-1 evidence checkpoint | `22fb39158cf062cd0474ff681826c4a7126166728be4ee9edbf1c41689b1315f` |

## Frozen scientific state retained

The PA-003 schedule, protocol, scanner configurations, artifacts, corpus, functional-test expectations, timing boundaries, gate rules, statistical analysis plan, and pilot evidence remain unchanged. Three final observations retained before PA-004 are `C2-R001`, `C0-R001`, and `C6-R001`; their raw evidence remains unstaged and immutable. No experimental execution occurred during the PA-004 corrective freeze.

The original PA-003 freeze manifest remains historically intact and deliberately retains its pre-correction validator hash. This record identifies the authorized PA-004 correction without rewriting PA-003 provenance.
