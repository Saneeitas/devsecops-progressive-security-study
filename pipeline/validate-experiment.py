#!/usr/bin/env python3
"""Mechanical validation for schedules and recorded run directories."""
from __future__ import annotations
import argparse,csv,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PILOT_RX=re.compile(r"^P-(C[0-6])-R(00[1-5])(?:-A(0[23]))?$")
FINAL_RX=re.compile(r"^(C[0-6])-R([0-9]{3})(?:-A(0[23]))?$")
FINAL_SCHEDULE_PATH=ROOT/"research/final-schedule-pa003.csv"
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

def final_schedule():
    assert FINAL_SCHEDULE_PATH.is_file(), "approved final schedule is unavailable"
    rows=list(csv.DictReader(FINAL_SCHEDULE_PATH.open()))
    assert len(rows)==140, "final schedule must contain 140 slots"
    seen=set(); orders=set(); configurations={f"C{i}":0 for i in range(7)}; by_block={}
    for r in rows:
      assert r["configuration"] in {f"C{i}" for i in range(7)}
      match=FINAL_RX.fullmatch(r["run_id"]); assert match and not match.group(3), "invalid final original run ID"
      assert r["run_id"] not in seen; seen.add(r["run_id"])
      assert r["run_id"].startswith(f"{r['configuration']}-"), "final configuration/run ID mismatch"
      order=schedule_order(r); assert 1 <= order <= 140, "final scheduled order is out of range"
      assert order not in orders, "duplicate final scheduled order"; orders.add(order)
      configurations[r["configuration"]]+=1
      by_block.setdefault(int(r["block"]),set()).add(r["configuration"])
    assert orders==set(range(1,141)), "final schedule orders must be 1..140"
    assert set(by_block)==set(range(1,21)) and all(items==set(configurations) for items in by_block.values()), "each final block must contain C0-C6"
    assert all(count==20 for count in configurations.values()), "each final configuration must appear 20 times"
    return {r["run_id"]:r for r in rows}

def schedule_order(row):
    if row.get("sequence_number"): return int(row["sequence_number"])
    return (int(row["block"])-1)*7+int(row["ordinal_position"])

def final_provenance(match, record, final_rows, directory):
    original=f"{match.group(1)}-R{match.group(2)}"
    assert original in final_rows, "final run does not map to an approved scheduled slot"
    assert record["configuration"]==match.group(1), "final configuration/run ID mismatch"
    if not match.group(3):
      assert "replacement_provenance" not in record, "original final run cannot contain replacement provenance"
      return original
    provenance=record.get("replacement_provenance")
    assert provenance, "final replacement requires PA-003 provenance"
    assert provenance["original_scheduled_slot_id"]==original
    assert provenance["configuration"]==match.group(1)
    assert provenance["scheduled_order"]==schedule_order(final_rows[original])
    assert provenance["attempt_number"]==int(match.group(3))
    predecessor=original if provenance["attempt_number"]==2 else f"{original}-A02"
    assert provenance["predecessor_attempt_id"]==predecessor
    assert provenance["evidence_directory"]==f"data/raw/final/{directory.name}"
    assert provenance["protocol_amendment"]=="PA-003"
    previous=ROOT/"data/raw/final"/predecessor/"run.json"
    assert previous.exists(), "final replacement predecessor record is missing"
    assert json.loads(previous.read_text())["validity"]=="INVALID_RETRYABLE", "final replacement predecessor must be INVALID_RETRYABLE"
    return original

def register_run_identity(seen, classification, run_id):
    """Register a run within its evidence classification namespace."""
    key=(classification,run_id)
    assert key not in seen, "duplicate run ID within classification"
    seen.add(key)

def assert_final_slot_limits(final_slots):
    for slot,attempts in final_slots.items():
      assert len(attempts)<=3, f"final slot exceeds three total attempts: {slot}"
      assert sum(r["validity"]=="VALID" for r in attempts)<=1, f"final slot has multiple VALID attempts: {slot}"

def runs():
    schedule_rows={r["run_id"]:r for r in csv.DictReader((ROOT/"research/pilot-schedule-v1.csv").open())}
    ids=set(); final_rows=None; final_slots={}
    for c in ("pilot","final","smoke"):
      for d in (ROOT/"data/raw"/c).glob("*"):
       if not d.is_dir(): continue
       register_run_identity(ids,c,d.name)
       for f in ("run.json","environment.json","timings.json","gate.json","normalized-findings.json"): assert (d/f).exists(),f
       r=json.loads((d/"run.json").read_text())
       required={"schema_version","run_id","classification","configuration","environment","timings","resources","tools","security","outcome","validity"}
       assert required <= set(r), "run.json required fields"
       assert r["classification"]==c, "classification/directory mismatch"
       assert r["timings"]["total_ms"] is not None, "missing total timing"
       assert r["validity"] in {"VALID","INVALID_RETRYABLE","INVALID_NONRETRYABLE"}
       if r["validity"]=="VALID" and d.name not in HISTORICAL_VALID_FAILURE_STAGE:
        assert r["outcome"]["failure_stage"] is None, "valid run cannot have failure_stage"
       if c=="pilot":
        match=PILOT_RX.match(d.name); assert match and r["configuration"]==match.group(1)
        original=f"P-{match.group(1)}-R{match.group(2)}"
        assert original in schedule_rows, "pilot run does not map to a frozen scheduled slot"
        if match.group(3):
         provenance=r.get("replacement_provenance")
         assert provenance, "replacement run requires PA-002 provenance"
         assert provenance["original_scheduled_slot_id"]==original
         assert provenance["configuration"]==match.group(1)
         assert provenance["scheduled_order"]==int(schedule_rows[original]["sequence_number"])
         assert provenance["attempt_number"]==int(match.group(3))
         predecessor=original if provenance["attempt_number"]==2 else f"{original}-A02"
         assert provenance["predecessor_attempt_id"]==predecessor
         assert provenance["evidence_directory"]==f"data/raw/pilot/{d.name}"
         assert provenance["protocol_amendment"]=="PA-002"
         previous=ROOT/"data/raw/pilot"/predecessor/"run.json"
         assert previous.exists(), "replacement predecessor record is missing"
         assert json.loads(previous.read_text())["validity"]=="INVALID_RETRYABLE", "replacement predecessor must be INVALID_RETRYABLE"
        else: assert "replacement_provenance" not in r, "original scheduled run cannot contain replacement provenance"
       if c=="final":
        if final_rows is None: final_rows=final_schedule()
        match=FINAL_RX.fullmatch(d.name); assert match, "unsupported final namespace format"
        slot=final_provenance(match,r,final_rows,d)
        final_slots.setdefault(slot,[]).append(r)
    assert_final_slot_limits(final_slots)
def main():
 p=argparse.ArgumentParser(); p.add_argument("--schedule",action="store_true"); p.add_argument("--runs",action="store_true"); a=p.parse_args()
 if a.schedule or not a.runs: schedule()
 if a.runs: runs()
 print("validation: PASS")
if __name__=="__main__":
 try: main()
 except Exception as e: print(f"validation: FAIL: {e}",file=sys.stderr); raise SystemExit(1)
