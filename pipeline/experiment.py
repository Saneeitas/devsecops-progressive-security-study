#!/usr/bin/env python3
"""Common, configuration-driven experimental pipeline harness.

This program deliberately contains no scanner-specific detection logic. It
orchestrates frozen treatments, persists evidence, and records errors without
turning them into negative findings.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, platform, re, shutil, subprocess, sys, time
from pathlib import Path
from common_lifecycle import DatabaseLifecycle, expected_functional_invariant

ROOT = Path(__file__).resolve().parents[1]
CORPUS = "eeb2e772ffb60fb214df8b41866be23be89dcf3f"
SPEC = "d808bfc24691ace15c0bbdc2a914a8ce01e6059b"
RUN_RE = re.compile(r"^(?:(P)-)?(C[0-6])-R([0-9]{3})$")
CONTROLS = {
 "SAST": ("Semgrep", "1.178.0"), "SCA": ("OSV-Scanner", "2.6.0"),
 "SECRET_SCANNING": ("Gitleaks", "8.30.1"), "CONTAINER_SCANNING": ("Trivy", "0.74.0"),
 "IAC_SCANNING": ("Checkov", "3.3.8"), "DAST": ("OWASP ZAP", "2.17.0"),
}

def cmd(args, cwd=ROOT, timeout=None, env=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env)
def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def load(path): return json.loads((ROOT/path).read_text())
def iso(): return dt.datetime.now(dt.timezone.utc).isoformat()
def ms(start): return round((time.monotonic_ns()-start)/1_000_000, 3)
def git(ref="HEAD"):
    r=cmd(["git","rev-parse",ref]); return r.stdout.strip() if r.returncode==0 else None

def configuration(config):
    for item in load("research/configurations.json")["configurations"]:
        if item["id"] == config: return item
    raise ValueError("unknown configuration")
def validate_id(config, run_id, classification):
    m=RUN_RE.fullmatch(run_id or "")
    if not m or m.group(2) != config: raise ValueError("run ID must match --config exactly")
    if classification == "pilot" and not m.group(1): raise ValueError("pilot IDs require P-Cx-Rnnn")
    if classification in ("final","smoke") and m.group(1): raise ValueError("only pilot IDs use P- prefix")

def artifact_preflight():
    m=load("research/experiment-artifacts-v1.json"); checks=[]
    def visit(o):
        if isinstance(o, dict):
            if "path" in o and "sha256" in o:
                got=sha(o["path"]); checks.append({"path":o["path"],"expected":o["sha256"],"actual":got,"ok":got==o["sha256"]})
            for x in o.values(): visit(x)
        elif isinstance(o,list):
            for x in o: visit(x)
    visit(m)
    checks += [
      {"path":"git:corpus-v1", "expected":CORPUS, "actual":git("corpus-v1^{}"), "ok":git("corpus-v1^{}")==CORPUS},
      {"path":"git:experiment-spec-v1", "expected":SPEC, "actual":git("experiment-spec-v1^{}"), "ok":git("experiment-spec-v1^{}")==SPEC},
    ]
    return {"checked_at":iso(),"status":"PASS" if all(x["ok"] for x in checks) else "FAIL","checks":checks}

def environment():
    def out(a):
        try: return cmd(a).stdout.strip() or None
        except Exception: return None
    return {"os":platform.system(),"os_version":platform.version(),"architecture":platform.machine(),
      "runner_type":"local","runner_name":os.getenv("RUNNER_NAME"),"cpu":platform.processor() or None,
      "cpu_count":os.cpu_count(),"memory_bytes":None,"node_version":out(["node","--version"]) or "unavailable",
      "postgresql_version":None,"docker_version":out(["docker","version","--format","{{.Server.Version}}"]),
      "ci_metadata":{"github_run_id":os.getenv("GITHUB_RUN_ID"),"github_runner_os":os.getenv("RUNNER_OS")}}

def stage(name, fn, logdir):
    started=time.monotonic_ns()
    try:
        result=fn()
        status="OK" if result.returncode==0 else "ERROR"
        (logdir/f"{name}.stdout.log").write_text(result.stdout or "")
        (logdir/f"{name}.stderr.log").write_text(result.stderr or "")
        return {"stage":name,"duration_ms":ms(started),"status":status,"exit_code":result.returncode}
    except Exception as e:
        (logdir/f"{name}.stderr.log").write_text(repr(e))
        return {"stage":name,"duration_ms":ms(started),"status":"ERROR","exit_code":None,"error":repr(e)}

def frozen_command(control, run_dir):
    raw=run_dir/"raw"; raw.mkdir(exist_ok=True)
    if control=="SAST":
        return ["docker","run","--rm","--network","none","semgrep/semgrep:1.178.0","semgrep","scan","--config","/rules","--json","application/src"]
    if control=="SCA": return ["osv-scanner","scan","source","--lockfile","application/package-lock.json","--format","json"]
    if control=="SECRET_SCANNING": return ["gitleaks","dir",".","--config","pipeline/security/gitleaks.toml","--report-format","json","--no-banner"]
    if control=="CONTAINER_SCANNING": return ["trivy","image","--scanners","vuln","--format","json","--skip-db-update","--skip-java-db-update","devsecops-corpus"]
    if control=="IAC_SCANNING": return ["checkov","--directory","infrastructure/terraform","--framework","terraform","--output","json","--skip-download","--soft-fail"]
    raise ValueError("DAST requires lifecycle runner")

def run(args):
    validate_id(args.config,args.run_id,args.classification)
    if args.classification not in ("smoke","pilot","final"): raise ValueError("invalid classification")
    run_dir=ROOT/"data/raw"/args.classification/args.run_id
    if run_dir.exists(): raise RuntimeError("duplicate run ID: existing directory is never overwritten")
    run_dir.mkdir(parents=True); logs=run_dir/"logs"; logs.mkdir(); (run_dir/"raw").mkdir()
    started=time.monotonic_ns(); started_at=iso(); preflight=artifact_preflight()
    (run_dir/"preflight.json").write_text(json.dumps(preflight,indent=2)+"\n")
    if preflight["status"]!="PASS":
        outcome={"validity":"INVALID_NONRETRYABLE","reason":"EXPERIMENT_INFRASTRUCTURE_ERROR: artifact preflight failed"}
        (run_dir/"run.json").write_text(json.dumps({"run_id":args.run_id,"classification":args.classification,"configuration":args.config,"outcome":outcome},indent=2)+"\n")
        return 2
    cfg=configuration(args.config); stages=[]; lifecycle=None
    # Measured production execution is intentionally explicit; no hidden scanner substitution.
    if not args.execute:
        (run_dir/"README.txt").write_text("DRY-RUN harness validation only; no pipeline stage or scanner executed.\n")
        validity="INVALID_RETRYABLE"; reason="DRY_RUN_NOT_A_MEASURED_EXPERIMENT"
    else:
        try:
            stages.append(stage("dependency_setup",lambda:cmd(["npm","ci"],ROOT/"application"),logs))
            lifecycle=DatabaseLifecycle(args.run_id); test_env=lifecycle.start(); lifecycle.migrate_seed()
            for item in lifecycle.stages:
                stages.append({"stage":item["stage"],"duration_ms":item["duration_ms"],"status":"OK","exit_code":item["exit_code"]})
            stages.append(stage("build",lambda:cmd(["npm","run","build"],ROOT/"application",env=test_env),logs))
            test_result=lifecycle.tests()
            (logs/"functional_tests.stdout.log").write_text(test_result.stdout or "")
            (logs/"functional_tests.stderr.log").write_text(test_result.stderr or "")
            invariant=expected_functional_invariant(test_result)
            stages.append({"stage":"functional_tests","duration_ms":lifecycle.stages[-1]["duration_ms"],"status":"EXPECTED_CORPUS_TEST_FAILURE" if invariant["status"]=="EXPECTED_CORPUS_TEST_FAILURE" else "ERROR","exit_code":test_result.returncode,"invariant":invariant})
            for control in cfg["controls_enabled"]:
                if control=="DAST":
                    stages.append(stage("DAST",lambda:cmd(["python3","pipeline/dast_lifecycle.py","--run-dir",str(run_dir),"--execute"],timeout=1800,env=test_env),logs))
                else: stages.append(stage(control,lambda c=control:cmd(frozen_command(c,run_dir),env=test_env),logs))
        except Exception as error:
            stages.append({"stage":"common_lifecycle","duration_ms":None,"status":"ERROR","exit_code":None,"error":repr(error)})
        finally:
            if lifecycle:
                lifecycle.cleanup()
                item=lifecycle.stages[-1]
                stages.append({"stage":item["stage"],"duration_ms":item["duration_ms"],"status":"OK","exit_code":item["exit_code"]})
        validity="VALID" if all(s["status"] in ("OK","EXPECTED_CORPUS_TEST_FAILURE") for s in stages) else "INVALID_RETRYABLE"; reason=None
    by_stage={s["stage"]:s for s in stages}
    controls=[{"control":c,"tool":CONTROLS[c][0],"duration_ms":by_stage.get(c,{}).get("duration_ms")} for c in cfg["controls_enabled"]]
    record={"schema_version":"1.0","run_id":args.run_id,"classification":args.classification,"configuration":args.config,
      "corpus_commit":CORPUS,"pipeline_commit":git(),"timestamp":started_at,"environment":environment(),
      "cache":{"policy":"controlled_warm","condition":"unknown","primed":False,"dependency_cache_hit":None,"docker_cache_condition":"unknown","notes":"Cache must be warmed by the separate warm command before measured runs."},
      "timings":{"clock":"monotonic_wall_clock","pipeline_started_at":started_at,"pipeline_ended_at":iso(),"total_ms":ms(started),"setup_ms":round(sum(s.get("duration_ms") or 0 for s in stages if s["stage"] in ("database_container_start","database_readiness","migration","seed")),3),"build_ms":by_stage.get("build",{}).get("duration_ms"),"functional_test_ms":by_stage.get("functional_tests",{}).get("duration_ms"),"deployment_startup_ms":None,"dast_ms":by_stage.get("DAST",{}).get("duration_ms"),"security_controls":controls},
      "resources":{"measurement_available":False,"cpu_utilization_percent":None,"peak_memory_bytes":None,"sampling_interval_ms":None,"method":None},
      "tools":[{"control":c,"name":CONTROLS[c][0],"version":CONTROLS[c][1],"executed":False,"native_exit_code":None,"artifact":None} for c in cfg["controls_enabled"]],
      "security":{"finding_count":0,"normalized_finding_count":0,"finding_artifact":"normalized-findings.json","vulnerability_detection":[]},
      "execution":stages,
      "outcome":{"success":validity=="VALID","exit_status":0 if validity=="VALID" else 2,"security_gate":"NOT_APPLICABLE","failure_stage":reason or next((s["stage"] for s in stages if s["status"]!="OK"),None),"notes":"Detection-to-ground-truth mapping is a separate manual-review stage."},
      "validity":validity}
    (run_dir/"run.json").write_text(json.dumps(record,indent=2)+"\n")
    (run_dir/"environment.json").write_text(json.dumps(record["environment"],indent=2)+"\n")
    (run_dir/"timings.json").write_text(json.dumps(record["timings"],indent=2)+"\n")
    (run_dir/"gate.json").write_text(json.dumps({"status":"NOT_APPLICABLE","reason":"gate evaluates after all configured controls"},indent=2)+"\n")
    (run_dir/"normalized-findings.json").write_text("[]\n")
    return 0 if not args.execute else record["outcome"]["exit_status"]

def warm():
    p=ROOT/"data/cache-preflight.json"; p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"prepared_at":iso(),"policy":"controlled_warm","note":"Warm-up must be run separately and is not a measured run."},indent=2)+"\n")
    print(p)
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="command",required=True)
    r=sub.add_parser("run"); r.add_argument("--config",required=True); r.add_argument("--run-id",required=True); r.add_argument("--class",dest="classification",required=True); r.add_argument("--execute",action="store_true")
    sub.add_parser("preflight"); sub.add_parser("warm")
    a=ap.parse_args()
    if a.command=="preflight": print(json.dumps(artifact_preflight(),indent=2)); return 0
    if a.command=="warm": warm(); return 0
    return run(a)
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e: print(f"EXPERIMENT_INFRASTRUCTURE_ERROR: {e}",file=sys.stderr); raise SystemExit(2)
