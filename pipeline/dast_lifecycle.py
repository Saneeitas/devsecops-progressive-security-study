#!/usr/bin/env python3
"""Frozen C6 lifecycle executor for the isolated Compose topology."""
from __future__ import annotations
import argparse, json, os, subprocess, time
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--run-dir",required=True); p.add_argument("--execute",action="store_true"); a=p.parse_args()
 d=Path(a.run_dir); (d/"raw").mkdir(parents=True,exist_ok=True)
 plan={"contract":"research/dast-test-contract-v1.md","steps":["compose down --volumes","compose up postgres","migrate","seed deterministic dataset","start api","wait health","login Alice/admin","create Bob order ID 1","ZAP user pass","ZAP admin pass","compose down"],"outer_timeout_minutes":30,"packaged_scan_timeout_minutes":15}
 (d/"dast-lifecycle-plan.json").write_text(json.dumps(plan,indent=2)+"\n")
 if not a.execute:
   print("DAST lifecycle plan written; no target, application, or scan started.")
   return
 env=os.environ.copy()
 required=("POSTGRES_PASSWORD","JWT_SECRET","SEED_ADMIN_PASSWORD","SEED_USER_PASSWORD")
 if any(not env.get(k) for k in required): raise SystemExit("EXPERIMENT_INFRASTRUCTURE_ERROR: missing ephemeral DAST environment")
 def run(command, timeout=1800):
   r=subprocess.run(command,cwd=Path(__file__).resolve().parents[1],env=env,text=True,capture_output=True,timeout=timeout)
   (d/"logs").mkdir(exist_ok=True)
   label=command[2].replace("/","_") if len(command)>2 else "command"
   (d/"logs"/(label+".log")).write_text((r.stdout or "")+(r.stderr or ""))
   if r.returncode: raise SystemExit("EXPERIMENT_INFRASTRUCTURE_ERROR: lifecycle step failed: "+" ".join(command))
 run(["docker","compose","down","--volumes","--remove-orphans"])
 run(["docker","compose","up","-d","postgres"],300)
 run(["npm","--prefix","application","run","db:migrate"],300)
 run(["npm","--prefix","application","run","db:seed"],300)
 run(["docker","compose","up","-d","--build","api"],600)
 deadline=time.monotonic()+180
 import urllib.request
 while time.monotonic()<deadline:
   try:
    if urllib.request.urlopen("http://localhost:3000/api/health",timeout=3).status==200: break
   except Exception: time.sleep(2)
 else: raise SystemExit("EXPERIMENT_INFRASTRUCTURE_ERROR: API readiness timeout")
 # Tokens are created only in memory by the frozen login hook. The exact two
 # ZAP passes use mounted frozen OpenAPI/context/rules artifacts and never an
 # external target. Reports remain in this run directory.
 raise SystemExit("EXPERIMENT_INFRASTRUCTURE_ERROR: reviewed ZAP pass launcher is required before measured C6 execution")
if __name__=="__main__": main()
