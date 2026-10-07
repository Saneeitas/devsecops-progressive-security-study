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
from tool_runtime import runtime_preflight, RUNTIME_ROOT
from scanner_io import CHECKOV_REPORT_FILENAME, resolve_checkov_report

ROOT = Path(__file__).resolve().parents[1]
CORPUS = "eeb2e772ffb60fb214df8b41866be23be89dcf3f"
SPEC = "d808bfc24691ace15c0bbdc2a914a8ce01e6059b"
RUN_RE = re.compile(r"^(?:(P)-)?(C[0-6])-R([0-9]{3})$")
CONTROLS = {
 "SAST": ("Semgrep", "1.178.0"), "SCA": ("OSV-Scanner", "2.6.0"),
 "SECRET_SCANNING": ("Gitleaks", "8.30.1"), "CONTAINER_SCANNING": ("Trivy", "0.74.0"),
 "IAC_SCANNING": ("Checkov", "3.3.8"), "DAST": ("OWASP ZAP", "2.17.0"),
}
INVALIDATING_STATUSES={"ERROR","SCANNER_EXECUTION_ERROR","EXPERIMENT_INFRASTRUCTURE_ERROR","TIMEOUT"}
SEM_IMAGE="docker.io/semgrep/semgrep@sha256:fbba1f23d2ef94630c828e8692758f8bc6353a8089841a396a5c041451966ffb"
TRIVY_IMAGE="docker.io/aquasec/trivy@sha256:ee940acbf1f58ebadb42d01434ce4609530bf1b52536afbd1eee66cd7123c5c9"
ZAP_IMAGE="ghcr.io/zaproxy/zaproxy@sha256:71db37cd5b75663b35758d10aaec05bf6fbac23f5020e3046c70e628a5f84efa"
APP_BASE_IMAGE="node:18.16.0-bullseye-slim@sha256:2b05866efb50b6bbc642e6d1cef908372351ad981453b8a747b1d0c9b5777cd8"
IMAGE_TAG_PREFIX="devsecops-corpus"

def outcome_for_stages(stages, security_gate="NOT_APPLICABLE"):
    """Keep expected corpus behavior and gate results separate from execution failure."""
    failure=next((s["stage"] for s in stages if s.get("status") in INVALIDATING_STATUSES),None)
    validity="VALID" if failure is None else "INVALID_RETRYABLE"
    return {"validity":validity,"success":validity=="VALID","exit_status":0 if validity=="VALID" else 2,
            "security_gate":security_gate,"failure_stage":failure,
            "notes":"Detection-to-ground-truth mapping is a separate manual-review stage."}

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

def cache_preflight():
    path=ROOT/"data/cache-preflight.json"
    try: state=json.loads(path.read_text())
    except Exception as error: return {"status":"FAIL","reason":f"controlled warm-cache preparation is missing: {error}"}
    lock=hashlib.sha256((ROOT/"application/package-lock.json").read_bytes()).hexdigest()
    image=state.get("warm_image_id")
    inspect=cmd(["docker","image","inspect",image,"--format","{{.Id}}"],timeout=20) if image else None
    postgres_id=state.get("postgres_image_id")
    postgres=cmd(["docker","image","inspect","postgres:16-alpine","--format","{{.Id}}"],timeout=20) if postgres_id else None
    base_id=state.get("application_base_image_id")
    base=cmd(["docker","image","inspect",APP_BASE_IMAGE,"--format","{{.Id}}"],timeout=20) if base_id else None
    ok=(state.get("policy")=="controlled_warm" and state.get("source_commit")==git()
        and state.get("package_lock_sha256")==lock and inspect is not None and inspect.returncode==0
        and inspect.stdout.strip()==image and postgres is not None and postgres.returncode==0
        and postgres.stdout.strip()==postgres_id and base is not None and base.returncode==0
        and base.stdout.strip()==base_id)
    return {"status":"PASS" if ok else "FAIL","path":"data/cache-preflight.json","package_lock_sha256":lock,"warm_image_id":image,"postgres_image_id":postgres_id,"application_base_image_id":base_id,"reason":None if ok else "warm cache state, source, dependency lockfile, or Docker image identity differs"}

def environment(postgresql_version="unavailable"):
    def out(a):
        try: return cmd(a).stdout.strip() or None
        except Exception: return None
    return {"os":platform.system(),"os_version":platform.version(),"architecture":platform.machine(),
      "runner_type":"local","runner_name":os.getenv("RUNNER_NAME"),"cpu":platform.processor() or None,
      "cpu_count":os.cpu_count(),"memory_bytes":None,"node_version":out(["node","--version"]) or "unavailable",
      "postgresql_version":postgresql_version,"docker_version":out(["docker","version","--format","{{.Server.Version}}"]),
      "ci_metadata":{"github_run_id":os.getenv("GITHUB_RUN_ID"),"github_runner_os":os.getenv("RUNNER_OS")}}

def stage(name, fn, logdir, finding_exit_codes=()):
    started=time.monotonic_ns()
    try:
        result=fn()
        normalized=getattr(result,"normalized",None)
        if normalized is not None and result.returncode==1 and normalized["normalized_count"]==0: status="SCANNER_EXECUTION_ERROR"
        elif normalized is not None: status="SCAN_COMPLETED_WITH_FINDINGS" if normalized["normalized_count"] else "SCAN_COMPLETED_WITH_NO_FINDINGS"
        else: status="OK" if result.returncode==0 else ("NONZERO_FINDINGS" if result.returncode in finding_exit_codes else "ERROR")
        (logdir/f"{name}.stdout.log").write_text(result.stdout or "")
        (logdir/f"{name}.stderr.log").write_text(result.stderr or "")
        record={"stage":name,"duration_ms":getattr(result,"measurement_duration_ms",ms(started)),"status":status,"exit_code":result.returncode}
        if normalized: record.update(normalized)
        return record
    except subprocess.TimeoutExpired as e:
        (logdir/f"{name}.stderr.log").write_text("stage exceeded its bounded timeout")
        return {"stage":name,"duration_ms":ms(started),"status":"TIMEOUT","exit_code":None,"error":repr(e)}
    except Exception as e:
        (logdir/f"{name}.stderr.log").write_text(repr(e))
        message=str(e); status="SCANNER_EXECUTION_ERROR" if "SCANNER_EXECUTION_ERROR" in message else ("EXPERIMENT_INFRASTRUCTURE_ERROR" if "EXPERIMENT_INFRASTRUCTURE_ERROR" in message else "ERROR")
        return {"stage":name,"duration_ms":ms(started),"status":status,"exit_code":None,"error":repr(e)}

def frozen_command(control, run_dir, trivy_runtime_dir=None):
    raw=run_dir/"raw"; raw.mkdir(exist_ok=True)
    if control=="SAST":
        return ["docker","run","--pull=never","--rm","--network","none","--platform","linux/amd64","-v",f"{ROOT}:/src:ro","-v",f"{RUNTIME_ROOT}/semgrep-rules:/rules:ro",SEM_IMAGE,"semgrep","scan","--config","/rules","--json","--output","/dev/stdout","--error","--include","*.ts","--exclude","application/tests/**","--exclude","application/dist/**","--exclude","application/node_modules/**","/src/application/src"]
    if control=="SCA": return [str(RUNTIME_ROOT/"bin/osv-scanner"),"scan","source","--lockfile","application/package-lock.json","--format","json","--output-file",str(raw/"osv.json"),"--offline","--offline-vulnerabilities"]
    if control=="SECRET_SCANNING": return [str(RUNTIME_ROOT/"bin/gitleaks"),"dir",".","--config","pipeline/security/gitleaks.toml","--report-format","json","--report-path",str(raw/"gitleaks.json"),"--exit-code","1","--no-banner"]
    if control=="CONTAINER_SCANNING":
        iid=run_dir/"container-image.iid"
        if not iid.is_file(): raise RuntimeError("required immutable built-image ID is missing")
        if trivy_runtime_dir is None: raise RuntimeError("Trivy writable runtime cache was not provisioned")
        database=RUNTIME_ROOT/"cache/trivy/db"
        cache_dir=trivy_runtime_dir/"cache"; tmp_dir=trivy_runtime_dir/"tmp"
        return ["docker","run","--pull=never","--rm","--network","none","--read-only","--platform","linux/amd64",
          "--mount",f"type=bind,src={cache_dir},dst=/root/.cache/trivy",
          "--mount",f"type=bind,src={database},dst=/frozen-db,readonly",
          "--mount",f"type=bind,src={tmp_dir},dst=/tmp",
          "-v","/var/run/docker.sock:/var/run/docker.sock",TRIVY_IMAGE,"--cache-dir","/root/.cache/trivy","image",
          "--scanners","vuln","--format","json","--skip-db-update","--skip-java-db-update","--severity","UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL","--ignore-unfixed=false","--exit-code","1",iid.read_text().strip()]
    if control=="IAC_SCANNING":
        output_dir=raw/"checkov-report"
        output_dir.mkdir(parents=True,exist_ok=False)
        return [str(RUNTIME_ROOT/"venv/checkov/bin/checkov"),"--directory","infrastructure/terraform","--framework","terraform","--config-file","pipeline/security/checkov.yaml","--output","json","--output-file-path",str(output_dir),"--skip-download","--soft-fail"]
    raise ValueError("DAST requires lifecycle runner")

def control_environment(control, base_env):
    result=dict(base_env)
    if control=="SCA":
        result["OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY"]=str(RUNTIME_ROOT/"cache/osv")
    return result

def normalize_scanner(control, result, run_dir):
    raw=run_dir/"raw"; name={"SAST":"semgrep","SCA":"osv","SECRET_SCANNING":"gitleaks","CONTAINER_SCANNING":"trivy","IAC_SCANNING":"checkov"}[control]
    raw_path=resolve_checkov_report(raw/"checkov-report") if name=="checkov" else raw/f"{name}.json"
    if name in ("semgrep","trivy"):
        raw_path.write_text(result.stdout or "{}")
    if not raw_path.exists():
        raise RuntimeError(f"{name} did not produce its required JSON artifact")
    normalized_path=raw/f"{name}.normalized.json"
    p=subprocess.run([sys.executable,"pipeline/normalize_findings.py","--tool",name,"--input",str(raw_path),"--run-id",run_dir.name,"--output",str(normalized_path)],cwd=ROOT,text=True,capture_output=True,timeout=60)
    if p.returncode: raise RuntimeError(f"normalizer failed: {p.stderr}")
    return {"raw_artifact":str(raw_path.relative_to(run_dir)),"normalized_artifact":str(normalized_path.relative_to(run_dir)),"normalized_count":len(json.loads(normalized_path.read_text()))}

def secret_artifact_check(run_dir, values):
    secrets_to_check=[value.encode() for value in values if isinstance(value,str) and len(value)>=16]
    checked=0; matches=[]
    for path in run_dir.rglob("*"):
        if not path.is_file(): continue
        checked+=1
        try: content=path.read_bytes()
        except Exception: matches.append(path.relative_to(run_dir).as_posix()); continue
        if any(value in content for value in secrets_to_check): matches.append(path.relative_to(run_dir).as_posix())
    return {"stage":"secret_artifact_check","status":"ERROR" if matches else "OK","duration_ms":None,"exit_code":1 if matches else 0,"files_checked":checked,"leaked_file_count":len(matches)}

def execute_control(control, run_dir, env):
    control_env=control_environment(control,env)
    if control=="IAC_SCANNING":
        for key in ("BC_API_KEY","PRISMA_API_URL","CKV_CHECK","CKV_SKIP_CHECK","CKV_FRAMEWORK","CHECKOV_EXPERIMENTAL_CHECKS_DIR"): control_env.pop(key,None)
    trivy_runtime_dir=None
    if control=="CONTAINER_SCANNING":
        cache_parent=RUNTIME_ROOT/"cache/trivy/runtime"
        cache_parent.mkdir(parents=True,exist_ok=True)
        trivy_runtime_dir=cache_parent/run_dir.name
        if trivy_runtime_dir.exists(): raise RuntimeError("run-derived Trivy runtime cache already exists")
        (trivy_runtime_dir/"cache").mkdir(parents=True)
        (trivy_runtime_dir/"tmp").mkdir()
        (trivy_runtime_dir/"cache/db").symlink_to("/frozen-db")
    try:
        scanner_started=time.monotonic_ns()
        result=cmd(frozen_command(control,run_dir,trivy_runtime_dir),timeout=900,env=control_env)
        scanner_duration=round((time.monotonic_ns()-scanner_started)/1_000_000,3)
        (run_dir/"logs"/f"{control}.scanner.stderr.log").write_text(result.stderr or "")
        if control=="CONTAINER_SCANNING": (run_dir/"raw/trivy.json").write_text(result.stdout or "")
        if result.returncode not in (0,1):
            raise RuntimeError(f"SCANNER_EXECUTION_ERROR: native exit {result.returncode}: {result.stderr[-2000:]}")
        try:
            normalized=normalize_scanner(control,result,run_dir)
        except Exception as error:
            if control=="CONTAINER_SCANNING" and result.returncode==1:
                raise RuntimeError(f"SCANNER_EXECUTION_ERROR: Trivy did not produce a valid JSON report: {error}") from error
            raise
        completed=subprocess.CompletedProcess([],result.returncode,result.stdout,result.stderr)
        completed.normalized=normalized
        completed.measurement_duration_ms=scanner_duration
        return completed
    finally:
        if trivy_runtime_dir is not None and trivy_runtime_dir.exists():
            cleanup=subprocess.run([sys.executable,"-c","import shutil,sys; shutil.rmtree(sys.argv[1])",str(trivy_runtime_dir)],cwd=ROOT,text=True,capture_output=True,timeout=15)
            (run_dir/"logs"/"trivy-runtime-cache-cleanup.log").write_text(cleanup.stdout+cleanup.stderr)
            if cleanup.returncode:
                raise RuntimeError("EXPERIMENT_INFRASTRUCTURE_ERROR: Trivy writable runtime cache cleanup failed")

def execute_dast(run_dir, image_tag, env):
    result=cmd(["python3","pipeline/dast_lifecycle.py","--run-dir",str(run_dir),"--image",image_tag,"--execute"],timeout=1850,env=env)
    lifecycle_path=run_dir/"dast-lifecycle.json"
    if result.returncode or not lifecycle_path.is_file():
        lifecycle=json.loads(lifecycle_path.read_text()) if lifecycle_path.is_file() else {}
        scanner_error=any(item.get("status")=="ERROR" or item.get("native_exit_code")==3 for item in lifecycle.get("zap_passes",[]))
        category="SCANNER_EXECUTION_ERROR" if scanner_error else "EXPERIMENT_INFRASTRUCTURE_ERROR"
        raise RuntimeError(f"{category}: DAST lifecycle did not complete cleanly: {result.stderr[-2000:]}")
    lifecycle=json.loads(lifecycle_path.read_text()); parsed=[]
    for item in lifecycle.get("zap_passes",[]):
        raw=run_dir/"raw"/item["raw_artifact"]
        normalized=run_dir/"raw"/f"zap-{item['pass']}.normalized.json"
        p=subprocess.run([sys.executable,"pipeline/normalize_findings.py","--tool","zap","--input",str(raw),"--run-id",run_dir.name,"--output",str(normalized)],cwd=ROOT,text=True,capture_output=True,timeout=60)
        if p.returncode: raise RuntimeError(f"DAST normalizer failed: {p.stderr}")
        parsed.extend(json.loads(normalized.read_text()))
    combined=run_dir/"raw/zap.normalized.json"; combined.write_text(json.dumps(parsed,indent=2)+"\n")
    completed=subprocess.CompletedProcess([],0,result.stdout,result.stderr)
    completed.normalized={"raw_artifact":"raw/zap-user.json + raw/zap-admin.json","normalized_artifact":"raw/zap.normalized.json","normalized_count":len(parsed),"passes":lifecycle.get("zap_passes",[])}
    return completed

def run(args):
    validate_id(args.config,args.run_id,args.classification)
    if args.classification not in ("smoke","pilot","final"): raise ValueError("invalid classification")
    run_dir=ROOT/"data/raw"/args.classification/args.run_id
    if run_dir.exists(): raise RuntimeError("duplicate run ID: existing directory is never overwritten")
    run_dir.mkdir(parents=True); logs=run_dir/"logs"; logs.mkdir(); (run_dir/"raw").mkdir()
    started_at=iso(); preflight=artifact_preflight()
    (run_dir/"preflight.json").write_text(json.dumps(preflight,indent=2)+"\n")
    if preflight["status"]!="PASS":
        outcome={"validity":"INVALID_NONRETRYABLE","reason":"EXPERIMENT_INFRASTRUCTURE_ERROR: artifact preflight failed"}
        (run_dir/"run.json").write_text(json.dumps({"run_id":args.run_id,"classification":args.classification,"configuration":args.config,"outcome":outcome},indent=2)+"\n")
        return 2
    cfg=configuration(args.config)
    tool_preflight=runtime_preflight(cfg["controls_enabled"],run_dir)
    (run_dir/"tool-preflight.json").write_text(json.dumps(tool_preflight,indent=2)+"\n")
    cache_state=cache_preflight()
    (run_dir/"cache-preflight.json").write_text(json.dumps(cache_state,indent=2)+"\n")
    if tool_preflight["status"]!="PASS" or cache_state["status"]!="PASS":
        failed_preflight="tool_preflight" if tool_preflight["status"]!="PASS" else "cache_preflight"
        outcome={"validity":"INVALID_NONRETRYABLE","success":False,"exit_status":2,"security_gate":"NOT_APPLICABLE","failure_stage":failed_preflight,"notes":"EXPERIMENT_INFRASTRUCTURE_ERROR: required pre-provisioned tools/artifacts are not READY; measured stages were not started."}
        record={"schema_version":"1.0","run_id":args.run_id,"classification":args.classification,"configuration":args.config,"corpus_commit":CORPUS,"pipeline_commit":git(),"timestamp":started_at,"environment":environment(),"cache":{"policy":"controlled_warm","condition":"unknown","primed":False,"dependency_cache_hit":None,"docker_cache_condition":"unknown","notes":"tool preflight failed before measured execution"},"timings":{"clock":"monotonic_wall_clock","pipeline_started_at":started_at,"pipeline_ended_at":iso(),"total_ms":0,"setup_ms":0,"build_ms":None,"functional_test_ms":None,"deployment_startup_ms":None,"dast_ms":None,"security_controls":[]},"resources":{"measurement_available":False,"cpu_utilization_percent":None,"peak_memory_bytes":None,"sampling_interval_ms":None,"method":None},"tools":[],"security":{"finding_count":0,"normalized_finding_count":0,"finding_artifact":"normalized-findings.json","vulnerability_detection":[]},"execution":[],"outcome":outcome,"validity":outcome["validity"]}
        (run_dir/"run.json").write_text(json.dumps(record,indent=2)+"\n"); (run_dir/"environment.json").write_text(json.dumps(record["environment"],indent=2)+"\n"); (run_dir/"timings.json").write_text(json.dumps(record["timings"],indent=2)+"\n"); (run_dir/"gate.json").write_text(json.dumps({"status":"NOT_APPLICABLE","reason":"tools were not ready; no controls executed"},indent=2)+"\n"); (run_dir/"normalized-findings.json").write_text("[]\n")
        return 2
    started=time.monotonic_ns(); started_at=iso(); stages=[]; lifecycle=None; image_tag=f"{IMAGE_TAG_PREFIX}:{args.run_id.lower()}"; image_built=False
    # Measured production execution is intentionally explicit; no hidden scanner substitution.
    if not args.execute:
        (run_dir/"README.txt").write_text("DRY-RUN harness validation only; no pipeline stage or scanner executed.\n")
        validity="INVALID_RETRYABLE"; reason="DRY_RUN_NOT_A_MEASURED_EXPERIMENT"
    else:
        try:
            dep=stage("dependency_setup",lambda:cmd(["npm","ci"],ROOT/"application",timeout=900),logs); stages.append(dep)
            if dep["status"]!="OK": raise RuntimeError("dependency/setup preparation failed")
            lifecycle=DatabaseLifecycle(args.run_id); test_env=lifecycle.start(); lifecycle.migrate_seed()
            for item in lifecycle.stages:
                stages.append({"stage":item["stage"],"duration_ms":item["duration_ms"],"status":"OK","exit_code":item["exit_code"]})
            tsbuild=stage("build",lambda:cmd(["npm","run","build"],ROOT/"application",timeout=300,env=test_env),logs); stages.append(tsbuild)
            if tsbuild["status"]!="OK": raise RuntimeError("TypeScript application build failed")
            test_result=lifecycle.tests()
            (logs/"functional_tests.stdout.log").write_text(test_result.stdout or "")
            (logs/"functional_tests.stderr.log").write_text(test_result.stderr or "")
            invariant=expected_functional_invariant(test_result)
            stages.append({"stage":"functional_tests","duration_ms":lifecycle.stages[-1]["duration_ms"],"status":"EXPECTED_CORPUS_TEST_FAILURE" if invariant["status"]=="EXPECTED_CORPUS_TEST_FAILURE" else "ERROR","exit_code":test_result.returncode,"invariant":invariant})
            if invariant["status"]!="EXPECTED_CORPUS_TEST_FAILURE": raise RuntimeError("UNEXPECTED_FUNCTIONAL_TEST_FAILURE: frozen V04 test invariant did not match")
            if args.config in {"C4","C5","C6"}:
                build=stage("container_build",lambda:cmd(["docker","build","--pull=false","--iidfile",str(run_dir/"container-image.iid"),"--tag",image_tag,"application"],timeout=900),logs)
                stages.append(build); image_built=build["status"]=="OK"
            for control in cfg["controls_enabled"]:
                if control=="DAST":
                    dast_stage=stage("DAST",lambda:execute_dast(run_dir,image_tag,test_env),logs)
                    stages.append(dast_stage)
                    lifecycle_record=run_dir/"dast-lifecycle.json"
                    if lifecycle_record.is_file():
                        for scan in json.loads(lifecycle_record.read_text()).get("zap_passes",[]):
                            stages.append({"stage":"ZAP_"+scan["pass"].upper()+"_API_PASS","duration_ms":scan.get("duration_ms"),"status":"OK" if scan.get("status")=="COMPLETED" else "SCANNER_EXECUTION_ERROR","exit_code":scan.get("native_exit_code"),"raw_artifact":"raw/"+scan.get("raw_artifact","")})
                else: stages.append(stage(control,lambda c=control:execute_control(c,run_dir,test_env),logs,finding_exit_codes=(1,)))
        except Exception as error:
            stages.append({"stage":"common_lifecycle","duration_ms":None,"status":"ERROR","exit_code":None,"error":repr(error)})
        finally:
            if lifecycle:
                lifecycle.cleanup()
                item=lifecycle.stages[-1]
                stages.append({"stage":item["stage"],"duration_ms":item["duration_ms"],"status":item.get("status","OK"),"exit_code":item["exit_code"],"errors":item.get("errors",[])})
            image_check=cmd(["docker","image","inspect",image_tag,"--format","{{.Id}}"],timeout=20)
            if image_built or image_check.returncode==0:
                stages.append(stage("container_image_cleanup",lambda:cmd(["docker","image","rm",image_tag],timeout=30),logs))
        reason=None
    by_stage={s["stage"]:s for s in stages}
    controls=[{"control":c,"tool":CONTROLS[c][0],"duration_ms":by_stage.get(c,{}).get("duration_ms")} for c in cfg["controls_enabled"]]
    normalized=[]; normalized_files=[]
    for filename in ("semgrep.normalized.json","osv.normalized.json","gitleaks.normalized.json","trivy.normalized.json","checkov.normalized.json","zap.normalized.json"):
        path=run_dir/"raw"/filename
        if path.is_file(): normalized.extend(json.loads(path.read_text())); normalized_files.append(str(path.relative_to(run_dir)))
    (run_dir/"normalized-findings.json").write_text(json.dumps(normalized,indent=2)+"\n")
    runtime_secrets=[]
    if lifecycle and lifecycle.env:
        runtime_secrets.extend(lifecycle.env.get(key) for key in ("DATABASE_URL","TEST_DATABASE_URL","JWT_SECRET","SEED_ADMIN_PASSWORD","SEED_USER_PASSWORD"))
        runtime_secrets.append(lifecycle.password)
    secret_check=secret_artifact_check(run_dir,runtime_secrets)
    stages.append(secret_check)
    run_gate="NOT_APPLICABLE" if not cfg["controls_enabled"] else ("ERROR" if any(s.get("status") in {"SCANNER_EXECUTION_ERROR","EXPERIMENT_INFRASTRUCTURE_ERROR","TIMEOUT","ERROR"} for s in stages if s["stage"] in cfg["controls_enabled"] or s["stage"].startswith("ZAP_")) else "PASS")
    outcome=outcome_for_stages(stages,security_gate=run_gate) if args.execute else {"validity":"INVALID_RETRYABLE","success":False,"exit_status":2,"security_gate":"NOT_APPLICABLE","failure_stage":reason,"notes":"Dry-run harness validation only; no measured stages executed."}
    tool_records=[]
    for control in cfg["controls_enabled"]:
        result=by_stage.get(control,{})
        tool_records.append({"control":control,"name":CONTROLS[control][0],"version":CONTROLS[control][1],"executed":control in by_stage,"native_exit_code":result.get("exit_code"),"artifact":result.get("raw_artifact") or ("raw/zap-user.json + raw/zap-admin.json" if control=="DAST" and control in by_stage else None)})
    setup_names={"dependency_setup","database_container_start","database_readiness","migration","seed"}
    dast_result=json.loads((run_dir/"dast-lifecycle.json").read_text()) if (run_dir/"dast-lifecycle.json").is_file() else {}
    dast_steps={x.get("stage"):x.get("duration_ms") for x in dast_result.get("steps",[])}
    deployment_ms=sum(dast_steps.get(key) or 0 for key in ("application_start","application_readiness")) or None
    record={"schema_version":"1.0","run_id":args.run_id,"classification":args.classification,"configuration":args.config,
      "corpus_commit":CORPUS,"pipeline_commit":git(),"timestamp":started_at,"environment":environment(lifecycle.postgresql_version if lifecycle else "unavailable"),
      "cache":{"policy":"controlled_warm","condition":"warm" if cache_state["status"]=="PASS" else "unknown","primed":cache_state["status"]=="PASS","dependency_cache_hit":None,"docker_cache_condition":"warm" if cache_state["status"]=="PASS" else "unknown","notes":"Separate controlled warm-up and immutable cache identities verified before measured timer."},
      "timings":{"clock":"monotonic_wall_clock","pipeline_started_at":started_at,"pipeline_ended_at":iso(),"total_ms":ms(started),"setup_ms":round(sum(s.get("duration_ms") or 0 for s in stages if s["stage"] in setup_names),3),"dependency_setup_ms":by_stage.get("dependency_setup",{}).get("duration_ms"),"database_container_start_ms":by_stage.get("database_container_start",{}).get("duration_ms"),"database_readiness_ms":by_stage.get("database_readiness",{}).get("duration_ms"),"migration_ms":by_stage.get("migration",{}).get("duration_ms"),"seed_ms":by_stage.get("seed",{}).get("duration_ms"),"build_ms":by_stage.get("build",{}).get("duration_ms"),"container_build_ms":by_stage.get("container_build",{}).get("duration_ms"),"functional_test_ms":by_stage.get("functional_tests",{}).get("duration_ms"),"deployment_startup_ms":deployment_ms,"dast_database_start_ms":dast_steps.get("database_start"),"dast_database_readiness_ms":dast_steps.get("database_readiness"),"dast_migration_ms":dast_steps.get("migration"),"dast_seed_ms":dast_steps.get("seed"),"dast_ms":by_stage.get("DAST",{}).get("duration_ms"),"zap_user_pass_ms":by_stage.get("ZAP_USER_API_PASS",{}).get("duration_ms"),"zap_admin_pass_ms":by_stage.get("ZAP_ADMIN_API_PASS",{}).get("duration_ms"),"security_controls":controls},
      "resources":{"measurement_available":False,"cpu_utilization_percent":None,"peak_memory_bytes":None,"sampling_interval_ms":None,"method":None},
      "tools":tool_records,
      "security":{"finding_count":len(normalized),"normalized_finding_count":len(normalized),"finding_artifact":"normalized-findings.json","vulnerability_detection":[]},
      "execution":stages,
      "outcome":outcome,
      "validity":outcome["validity"]}
    (run_dir/"run.json").write_text(json.dumps(record,indent=2)+"\n")
    (run_dir/"environment.json").write_text(json.dumps(record["environment"],indent=2)+"\n")
    (run_dir/"timings.json").write_text(json.dumps(record["timings"],indent=2)+"\n")
    gate={"status":run_gate,"triggering_controls":[],"triggering_findings":[],"policy_reason":"All enabled controls completed before this synthetic gate evaluation; normalized findings remain UNRESOLVED pending the separate mapping stage."}
    if args.execute and cfg["controls_enabled"]:
        gate_proc=cmd([sys.executable,"pipeline/evaluate-gate.py","--run",str(run_dir/"run.json"),"--findings",str(run_dir/"normalized-findings.json"),"--output",str(run_dir/"gate.json")],timeout=60)
        if gate_proc.returncode: gate={"status":"ERROR","triggering_controls":[],"triggering_findings":[],"policy_reason":"Synthetic gate evaluator failed after controls completed."}; outcome["security_gate"]="ERROR"
        else: gate=json.loads((run_dir/"gate.json").read_text()); outcome["security_gate"]=gate["status"]
    else: (run_dir/"gate.json").write_text(json.dumps(gate,indent=2)+"\n")
    record["outcome"]=outcome
    (run_dir/"run.json").write_text(json.dumps(record,indent=2)+"\n")
    return 0 if not args.execute else record["outcome"]["exit_status"]

def warm():
    p=ROOT/"data/cache-preflight.json"; p.parent.mkdir(exist_ok=True)
    dependency=cmd(["npm","ci"],ROOT/"application",timeout=1800)
    if dependency.returncode: raise RuntimeError(f"warm dependency preparation failed: {dependency.stderr[-1000:]}")
    db=cmd(["docker","pull","postgres:16-alpine"],timeout=900)
    if db.returncode: raise RuntimeError(f"warm PostgreSQL image preparation failed: {db.stderr[-1000:]}")
    pgid=cmd(["docker","image","inspect","postgres:16-alpine","--format","{{.Id}}"],timeout=20)
    if pgid.returncode: raise RuntimeError("warm PostgreSQL image identity could not be recorded")
    baseid=cmd(["docker","image","inspect",APP_BASE_IMAGE,"--format","{{.Id}}"],timeout=20)
    if baseid.returncode: raise RuntimeError("pinned application base image identity could not be recorded")
    tag="devsecops-study-warm:"+git()[:12]
    build=cmd(["docker","build","--tag",tag,"application"],timeout=1800)
    if build.returncode: raise RuntimeError(f"warm application image build failed: {build.stderr[-1000:]}")
    inspect=cmd(["docker","image","inspect",tag,"--format","{{.Id}}"],timeout=20)
    if inspect.returncode: raise RuntimeError("warm image identity could not be recorded")
    p.write_text(json.dumps({"prepared_at":iso(),"policy":"controlled_warm","source_commit":git(),"package_lock_sha256":hashlib.sha256((ROOT/"application/package-lock.json").read_bytes()).hexdigest(),"postgres_image":"postgres:16-alpine","postgres_image_id":pgid.stdout.strip(),"application_base_image":APP_BASE_IMAGE,"application_base_image_id":baseid.stdout.strip(),"warm_image_tag":tag,"warm_image_id":inspect.stdout.strip(),"scanner_downloads_during_measurement":False},indent=2)+"\n")
    print(json.dumps({"cache_state":str(p),"warm_image_id":inspect.stdout.strip(),"status":"READY"},indent=2))
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
