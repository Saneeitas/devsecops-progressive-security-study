#!/usr/bin/env python3
"""Mechanical validation for schedules and recorded run directories."""
from __future__ import annotations
import argparse,csv,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RX=re.compile(r"^P-(C[0-6])-R(00[1-5])$")
HISTORICAL_VALID_FAILURE_STAGE={"C0-R003"}
def schedule():
    rows=list(csv.DictReader((ROOT/"research/pilot-schedule-v1.csv").open()))
    assert len(rows)==35
    assert [r["sequence_number"] for r in rows]==[str(i) for i in range(1,36)]
    seen=set()
    for r in rows:
      assert r["configuration"] in {f"C{i}" for i in range(7)}
      assert r["run_id"]==f"P-{r['configuration']}-R{int(r['block']):03d}"
      assert r["run_id"] not in seen; seen.add(r["run_id"])
    for b in range(1,6): assert {r["configuration"] for r in rows if int(r["block"])==b}=={f"C{i}" for i in range(7)}
def runs():
    ids=set()
    for c in ("pilot","final","smoke"):
      for d in (ROOT/"data/raw"/c).glob("*"):
       if not d.is_dir(): continue
       assert d.name not in ids; ids.add(d.name)
       for f in ("run.json","environment.json","timings.json","gate.json","normalized-findings.json"): assert (d/f).exists(),f
       r=json.loads((d/"run.json").read_text())
       required={"schema_version","run_id","classification","configuration","environment","timings","resources","tools","security","outcome","validity"}
       assert required <= set(r), "run.json required fields"
       assert r["classification"]==c, "classification/directory mismatch"
       assert r["timings"]["total_ms"] is not None, "missing total timing"
       assert r["validity"] in {"VALID","INVALID_RETRYABLE","INVALID_NONRETRYABLE"}
       if r["validity"]=="VALID" and d.name not in HISTORICAL_VALID_FAILURE_STAGE:
        assert r["outcome"]["failure_stage"] is None, "valid run cannot have failure_stage"
       if c=="pilot": assert RX.match(d.name) and r["configuration"]==RX.match(d.name).group(1)
def main():
 p=argparse.ArgumentParser(); p.add_argument("--schedule",action="store_true"); p.add_argument("--runs",action="store_true"); a=p.parse_args()
 if a.schedule or not a.runs: schedule()
 if a.runs: runs()
 print("validation: PASS")
if __name__=="__main__":
 try: main()
 except Exception as e: print(f"validation: FAIL: {e}",file=sys.stderr); raise SystemExit(1)
