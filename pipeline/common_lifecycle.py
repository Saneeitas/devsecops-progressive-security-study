#!/usr/bin/env python3
"""Disposable PostgreSQL lifecycle shared by C0-C6.

Runtime credentials are randomly generated, passed only through child-process
environment, and deliberately excluded from run artifacts and logs.
"""
from __future__ import annotations
import json, os, re, secrets, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IMAGE="postgres:16-alpine"

def _run(args, env=None, timeout=300):
 return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env=env,timeout=timeout)
def safe_id(run_id): return re.sub(r"[^a-z0-9]+","-",run_id.lower()).strip("-")

class DatabaseLifecycle:
 def __init__(self, run_id):
  suffix=safe_id(run_id); self.name=f"devsecops-exp-{suffix}"; self.volume=f"devsecops-exp-{suffix}-pg"
  self.password=secrets.token_urlsafe(32); self.db="devsecops_experiment"; self.user="postgres"
  self.started=None; self.stages=[]; self.env=None; self.postgresql_version=None
 def start(self):
  started=time.monotonic_ns()
  r=_run(["docker","volume","create",self.volume]); self._require(r,"volume_create")
  r=_run(["docker","run","--pull=never","-d","--name",self.name,"--label","devsecops.experiment=true","-e",f"POSTGRES_USER={self.user}","-e",f"POSTGRES_PASSWORD={self.password}","-e",f"POSTGRES_DB={self.db}","-v",f"{self.volume}:/var/lib/postgresql/data","-p","127.0.0.1::5432",IMAGE]); self._require(r,"container_start")
  self._record("database_container_start",started,0)
  started=time.monotonic_ns(); deadline=time.monotonic()+90
  while time.monotonic()<deadline:
   r=_run(["docker","exec",self.name,"pg_isready","-U",self.user,"-d",self.db],timeout=10)
   if r.returncode==0: break
   time.sleep(1)
  else: raise RuntimeError("database readiness timeout")
  version=_run(["docker","exec",self.name,"postgres","--version"],timeout=10)
  self._require(version,"database_version")
  self.postgresql_version=version.stdout.strip()
  self._record("database_readiness",started,0)
  port=_run(["docker","port",self.name,"5432/tcp"],timeout=15)
  self._require(port,"database_port")
  match=re.search(r":(\d+)\s*$",port.stdout)
  if not match: raise RuntimeError("unable to resolve disposable PostgreSQL host port")
  url=f"postgresql://{self.user}:{self.password}@127.0.0.1:{match.group(1)}/{self.db}"
  self.env={**os.environ,"DATABASE_URL":url,"TEST_DATABASE_URL":url,"NODE_ENV":"test","JWT_SECRET":secrets.token_urlsafe(48),"JWT_EXPIRES_IN":"1h","CORS_ORIGIN":"http://localhost:3000","SEED_ADMIN_PASSWORD":secrets.token_urlsafe(24)+"Aa1!","SEED_USER_PASSWORD":secrets.token_urlsafe(24)+"Bb2!"}
  self.started=time.monotonic_ns()
  return self.env
 def migrate_seed(self):
  for label,args in (("migration",["npm","--prefix","application","run","db:migrate"]),("seed",["npm","--prefix","application","run","db:seed"])):
   started=time.monotonic_ns(); r=_run(args,self.env); self._record(label,started,r.returncode)
   self._require(r,label)
 def tests(self):
  started=time.monotonic_ns(); r=_run(["npm","--prefix","application","test"],self.env); self._record("functional_tests",started,r.returncode); return r
 def cleanup(self):
  started=time.monotonic_ns(); failures=[]
  for label,args in (("container",["docker","rm","-f",self.name]),("volume",["docker","volume","rm","-f",self.volume])):
   try:
    r=_run(args,timeout=20)
    # Docker returns nonzero if a resource was never created; inspect first so
    # absence is successful cleanup while daemon errors remain visible.
    if r.returncode:
     inspect=["docker","inspect",self.name] if label=="container" else ["docker","volume","inspect",self.volume]
     check=_run(inspect,timeout=10)
     if check.returncode==0 or not any(marker in (check.stderr or check.stdout).lower() for marker in ("no such object","no such volume","not found")):
      failures.append({"resource":label,"error":(r.stderr or r.stdout).strip()})
   except Exception as error:
    failures.append({"resource":label,"error":repr(error)})
  self.stages.append({"stage":"database_cleanup","duration_ms":round((time.monotonic_ns()-started)/1_000_000,3),"exit_code":1 if failures else 0,"status":"ERROR" if failures else "OK","errors":failures})
  return {"ok":not failures,"errors":failures}
 def metadata(self):
  return {"image":IMAGE,"container_name":self.name,"volume_name":self.volume,"state_strategy":"unique disposable volume per run; removed on cleanup","stages":self.stages}
 def _record(self,name,started,code):
  self.stages.append({"stage":name,"duration_ms":round((time.monotonic_ns()-started)/1_000_000,3),"exit_code":code})
 def _require(self,r,label):
  if r.returncode: raise RuntimeError(f"{label} failed: {(r.stderr or r.stdout).strip()}")

def expected_functional_invariant(result):
 text=(result.stdout or "")+"\n"+(result.stderr or "")
 # Frozen corpus has twelve tests; V04 intentionally changes only this owner check.
 required_title="does not disclose another user's order"
 counts=bool(re.search(r"Tests\s+1 failed\s*\|\s*11 passed\s*\(12\)",text))
 return {"status":"EXPECTED_CORPUS_TEST_FAILURE" if result.returncode==1 and counts and required_title in text else "UNEXPECTED_FUNCTIONAL_TEST_FAILURE","expected_title":required_title,"native_exit_code":result.returncode,"summary_present":counts and required_title in text}
