#!/usr/bin/env python3
"""Static PA-002 provenance tests; no pipeline, test suite, or scanner runs."""
from argparse import Namespace
import json
import re
from pathlib import Path
from experiment import replacement_provenance, validate_id

base=dict(config="C1",run_id="P-C1-R002-A02",classification="pilot",
          original_slot_id="P-C1-R002",scheduled_order=8,attempt_number=2,
          predecessor_attempt_id="P-C1-R002",
          replacement_reason="unexpected_functional_test_failure")
record=replacement_provenance(Namespace(**base))
assert record["protocol_amendment"] == "PA-002"
assert record["evidence_directory"] == "data/raw/pilot/P-C1-R002-A02"
assert validate_id("C1","P-C1-R002-A02","pilot").group(4) == "02"

schema=json.loads((Path(__file__).resolve().parents[1]/"data/schema/run.schema.json").read_text())
assert "replacement_provenance" in schema["properties"]
assert re.fullmatch(schema["properties"]["run_id"]["pattern"], "P-C1-R002-A02")
assert re.fullmatch(schema["properties"]["run_id"]["pattern"], "P-C1-R002")
assert "replacement_provenance" not in json.loads((Path(__file__).resolve().parents[1]/"data/raw/pilot/P-C1-R002/run.json").read_text())

invalid=dict(base)
invalid["scheduled_order"]=9
try:
    replacement_provenance(Namespace(**invalid))
except ValueError:
    pass
else:
    raise AssertionError("mismatched scheduled order was accepted")

print("replacement provenance: PASS")
