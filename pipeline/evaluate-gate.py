#!/usr/bin/env python3
"""Derive the final experimental gate after all configured controls finish."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--run",required=True); p.add_argument("--findings",required=True); p.add_argument("--output",required=True); a=p.parse_args()
 run=json.loads(Path(a.run).read_text()); findings=json.loads(Path(a.findings).read_text())
 execution_errors=[x for x in run.get("execution",[]) if x.get("status") in {"ERROR","SCANNER_EXECUTION_ERROR","EXPERIMENT_INFRASTRUCTURE_ERROR","TIMEOUT"}]
 triggers=[x["finding_id"] for x in findings if x.get("classification") in {"SEEDED_TRUE_POSITIVE","NON_SEEDED_VALID_FINDING"}]
 gate={"status":"ERROR" if execution_errors else ("FAIL" if triggers else "PASS"),"triggering_controls":sorted({x["control"] for x in findings if x["finding_id"] in triggers}),"triggering_findings":triggers,"policy_reason":"All enabled controls completed before this synthetic gate was evaluated.","native_exit_codes":"Preserved in run execution records."}
 Path(a.output).write_text(json.dumps(gate,indent=2)+"\n")
if __name__=="__main__": main()
