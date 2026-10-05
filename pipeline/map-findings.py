#!/usr/bin/env python3
"""Apply a reviewed mapping file; never infer seeded IDs from a finding title."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ALLOWED={"SEEDED_TRUE_POSITIVE","SEEDED_FALSE_NEGATIVE","NON_SEEDED_VALID_FINDING","FALSE_POSITIVE","UNRESOLVED"}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--findings",required=True); p.add_argument("--review",required=True); p.add_argument("--output",required=True); a=p.parse_args()
 findings=json.loads(Path(a.findings).read_text()); review=json.loads(Path(a.review).read_text())
 by_id={r["finding_id"]:r for r in review.get("mappings",[])}
 for f in findings:
  r=by_id.get(f["finding_id"])
  if not r: continue
  if r.get("classification") not in ALLOWED or not r.get("rationale"): raise SystemExit("review requires allowed classification and rationale")
  f["classification"]=r["classification"]; f["seeded_vulnerability_ids"]=r.get("seeded_vulnerability_ids",[])
  f["manual_validation"]={"required":True,"status":"VALIDATED","reviewer":r.get("reviewer"),"validated_at":r.get("validated_at"),"rationale":r["rationale"],"evidence":r.get("evidence")}
 Path(a.output).write_text(json.dumps(findings,indent=2)+"\n")
if __name__=="__main__": main()
