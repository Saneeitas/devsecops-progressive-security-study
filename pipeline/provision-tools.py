#!/usr/bin/env python3
"""Provisioning-time, non-scanning checks for pinned local tool artifacts.

This command is intentionally separate from measured runs. It only inspects
versions, image identities, and frozen checksums; it never scans corpus files.
"""
from __future__ import annotations
import base64, datetime as dt, hashlib, json, os, platform, shutil, subprocess, sys, tarfile, uuid
from pathlib import Path
from tool_runtime import ROOT,RUNTIME_ROOT,STATE,digest

VERSIONS=json.loads((ROOT/"research/tool-versions.json").read_text())
def run(args,timeout=300):
 cleanup_name=None
 if len(args)>1 and args[0:2]==["docker","run"]:
  cleanup_name="devsecops-provision-"+uuid.uuid4().hex[:10]
  args=args[:2]+["--name",cleanup_name]+args[2:]
 try:
  p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
  return p.returncode,(p.stdout+p.stderr).strip()
 except Exception as e:
  if cleanup_name:
   try: subprocess.run(["docker","rm","-f",cleanup_name],cwd=ROOT,text=True,capture_output=True,timeout=20)
   except Exception: pass
  return 127,repr(e)
def run_image_version(args,version,timeout=300):
 """Observe the pinned image's version output, then stop the version-only process.

 Some scanner CLIs keep initializing telemetry/update helpers after printing
 their version. The container is disposable and receives no target or corpus.
 """
 name="devsecops-version-"+uuid.uuid4().hex[:10]
 command=[x for x in args if x!="--rm"]
 command=command[:2]+["-d","--name",name]+command[2:]
 try:
  started=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=60)
  if started.returncode: return started.returncode,(started.stdout+started.stderr).strip()
  for _ in range(timeout):
   logs=subprocess.run(["docker","logs",name],cwd=ROOT,text=True,capture_output=True,timeout=15)
   output=(logs.stdout+logs.stderr).strip()
   if version in output: return 0,output
   state=subprocess.run(["docker","inspect",name,"--format","{{.State.Running}} {{.State.ExitCode}}"],cwd=ROOT,text=True,capture_output=True,timeout=15)
   if state.returncode or state.stdout.startswith("false"):
    return 1,output or "pinned image version command exited before reporting expected version"
   __import__("time").sleep(1)
  return 124,output or "pinned image version output timed out"
 except Exception as error:
  return 127,repr(error)
 finally:
  try: subprocess.run(["docker","rm","-f",name],cwd=ROOT,text=True,capture_output=True,timeout=20)
  except Exception: pass
def file_item(name,version,rel,verify,sha=None):
 p=Path(rel); code,out=run(verify) if p.exists() else (127,"executable not present")
 good=p.is_file() and os.access(p,os.X_OK) and code==0 and version in out and (not sha or digest(p)==sha)
 got=digest(p) if good else None
 return {"name":name,"expected_version":version,"observed_version":out.splitlines()[0] if code==0 and out else None,"provisioning_method":"official pinned local release / isolated environment","kind":"executable","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/"+str(p.relative_to(RUNTIME_ROOT)),"expected_sha256":sha,"observed_sha256":got,"status":"READY" if good else "NOT_READY","verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),"reason":None if good else out}
def image_item(name,version,ref,expected_digest,platform_digest,verify_args,index_digest=None):
 code,out=run(["docker","image","inspect",ref,"--format","{{json .RepoDigests}} {{.Id}} {{.Os}}/{{.Architecture}}"],30)
 ready=code==0 and expected_digest in out and "linux/amd64" in out
 vcode,vout=run_image_version(verify_args,version,300) if ready else (127,"pinned image missing or digest does not match")
 ready=ready and vcode==0 and version in vout
 return {"name":name,"expected_version":version,"observed_version":version if vcode==0 and version in vout else None,"version_command_output_first_line":vout.splitlines()[0] if vcode==0 and vout else None,"provisioning_method":"official Linux/amd64 image pinned by frozen platform manifest digest","kind":"image","runtime_path":ref,"expected_sha256":expected_digest,"observed_sha256":expected_digest if ready else None,"expected_index_digest":index_digest,"expected_platform_manifest_digest":platform_digest,"observed_platform":"linux/amd64" if ready else None,"status":"READY" if ready else "NOT_READY","verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),"reason":None if ready else (out or vout)}
def md5_base64(path):
 h=hashlib.md5()
 with path.open("rb") as stream:
  for block in iter(lambda:stream.read(1024*1024),b""): h.update(block)
 return base64.b64encode(h.digest()).decode()
def prepare_osv_database(descriptor):
 root=RUNTIME_ROOT/"cache/osv"; source=root/"npm-all.zip"; target=root/descriptor["cache_layout"]
 if not source.is_file(): return False,target
 try:
  source_ok=source.stat().st_size==descriptor["size_bytes"] and md5_base64(source)==descriptor["md5_base64"]
  if not source_ok: return False,target
  target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():
   try: os.link(source,target)
   except OSError: shutil.copyfile(source,target)
  target_ok=target.is_file() and target.stat().st_size==descriptor["size_bytes"] and md5_base64(target)==descriptor["md5_base64"]
  return target_ok,target
 except OSError:
  return False,target
def main():
 RUNTIME_ROOT.mkdir(parents=True,exist_ok=True); (ROOT/"pipeline/runtime").mkdir(exist_ok=True)
 tool={x["control"]:x for x in VERSIONS["tools"]}; state={"schema_version":"1.0","machine_local":True,"platform":platform.platform(),"verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),"tools":{}}
 sem=tool["SAST"]; semplatform=sem["architecture"]["linux/amd64"]; semref="docker.io/semgrep/semgrep@"+semplatform
 state["tools"]["semgrep"]=image_item("Semgrep",sem["version"],semref,semplatform,semplatform,["docker","run","--rm","--network","none","--platform","linux/amd64",semref,"semgrep","--version"],sem["container_digest"])
 osv=tool["SCA"]; osvpath=RUNTIME_ROOT/"bin/osv-scanner"; osvitem=file_item("OSV-Scanner",osv["version"],osvpath,[str(osvpath),"--version"])
 if osvpath.exists():
  _,help_text=run([str(osvpath),"scan","source","--help"])
  descriptor=json.loads((ROOT/"pipeline/security/osv-database-v1.json").read_text())
  supported={flag for flag in ("--lockfile","--offline","--offline-vulnerabilities","--local-db-path","--download-offline-databases") if flag in help_text}
  required=set(descriptor["scanner_flags"])
  required_supported=required|{"--lockfile"}
  archive_ready,db_target=prepare_osv_database(descriptor)
  first=(osvitem.get("observed_version") or "").splitlines()[0]
  osv_version=first.rsplit(" ",1)[-1] if first.startswith("osv-scanner version:") else None
  osvitem["observed_version"]=osv_version
  osvitem["verified_supported_flags"]=sorted(required_supported & supported)
  osvitem["observed_cli_flags"]=sorted(supported)
  osvitem["treatment_flags"]=descriptor["scanner_flags"]
  osvitem["prohibited_treatment_flags"]=descriptor["prohibited_flags"]
  osvitem["offline_policy"]={"environment_variable":descriptor["cache_root_environment_variable"],"cache_root":"${DEVSECOPS_RUNTIME_ROOT}/cache/osv","database_path":"${DEVSECOPS_RUNTIME_ROOT}/cache/osv/"+descriptor["cache_layout"],"cache_layout":descriptor["cache_layout"],"network_disabled":"--offline" in required,"archive_ready":archive_ready}
  no_unsupported=("--local-db-path" not in required and "--download-offline-databases" not in required)
  if (osv_version!=osv["version"] or not required_supported.issubset(supported) or not no_unsupported or not archive_ready):
   osvitem.update({"status":"NOT_READY","reason":"OSV version, PA-001 offline flags, or unchanged frozen archive cache layout failed verification."})
 state["tools"]["osv"]=osvitem
 g=tool["SECRET_SCANNING"]; gp=RUNTIME_ROOT/"bin/gitleaks"; state["tools"]["gitleaks"]=file_item("Gitleaks",g["version"],gp,[str(gp),"version"])
 tr=tool["CONTAINER_SCANNING"]; trplatform=tr["architecture"]["linux/amd64"]; trref="docker.io/aquasec/trivy@"+trplatform; state["tools"]["trivy"]=image_item("Trivy",tr["version"],trref,trplatform,trplatform,["docker","run","--rm","--network","none","--platform","linux/amd64",trref,"--version"],tr["container_digest"])
 ck=tool["IAC_SCANNING"]; cp=RUNTIME_ROOT/"venv/checkov/bin/checkov"; checkov_item=file_item("Checkov",ck["version"],cp,[str(cp),"--version"])
 checkov_python=RUNTIME_ROOT/"venv/checkov/bin/python"
 forbidden=("BC_API_KEY","PRISMA_API_URL","CKV_CHECK","CKV_SKIP_CHECK","CKV_FRAMEWORK","CHECKOV_EXPERIMENTAL_CHECKS_DIR")
 checkov_item["credential_and_override_environment_unset"]=all(not os.environ.get(k) for k in forbidden)
 if checkov_item["status"]=="READY":
  freeze=run([str(checkov_python),"-m","pip","freeze"])
  if freeze[0]==0:
   freeze_path=RUNTIME_ROOT/"cache/checkov-environment-freeze.txt"; freeze_path.parent.mkdir(parents=True,exist_ok=True); freeze_path.write_text(freeze[1]+"\n")
   checkov_item["dependency_lock_path"]="${DEVSECOPS_RUNTIME_ROOT}/cache/checkov-environment-freeze.txt"; checkov_item["dependency_lock_sha256"]=hashlib.sha256(freeze[1].encode()).hexdigest()
  else: checkov_item.update({"status":"NOT_READY","reason":"unable to record isolated Python dependency state"})
 if not checkov_item["credential_and_override_environment_unset"]: checkov_item.update({"status":"NOT_READY","reason":"Checkov credential or environment override is set"})
 state["tools"]["checkov"]=checkov_item
 zap=tool["DAST"]; zapplatform=zap["architecture"]["linux/amd64"]; zref="ghcr.io/zaproxy/zaproxy@"+zapplatform; zapitem=image_item("OWASP ZAP",zap["version"],zref,zapplatform,zapplatform,["docker","run","--rm","--network","none","--platform","linux/amd64",zref,"zap.sh","-cmd","-version"],zap["container_digest"])
 if zapitem["status"]=="READY":
  acode,aout=run(["docker","run","--rm","--network","none","--platform","linux/amd64",zref,"zap.sh","-cmd","-addonlist"],300)
  def inventory_rows(text):
   found=[]
   for line in text.splitlines():
    fields=line.split("\t")
    if len(fields)>=5 and fields[1] not in ("ID","id") and fields[2].startswith("v"): found.append(tuple(fields[:4]))
   return sorted(found)
  expected_rows=inventory_rows((ROOT/"pipeline/security/zap-addon-inventory-v1.txt").read_text())
  observed_rows=inventory_rows(aout)
  zapitem["addon_inventory_match"]=acode==0 and expected_rows==observed_rows
  zapitem["observed_addon_count"]=len(observed_rows)
  if not zapitem["addon_inventory_match"]: zapitem.update({"status":"NOT_READY","reason":"installed ZAP add-on names/versions differ from frozen inventory"})
 state["tools"]["zap"]=zapitem
 frozen={"semgrep_rules":"pipeline/security/semgrep-rules-v1.json","gitleaks_config":"pipeline/security/gitleaks.toml","checkov_config":"pipeline/security/checkov.yaml","zap_inventory":"pipeline/security/zap-addon-inventory-v1.txt","openapi":"pipeline/security/openapi-corpus-v1.yaml","zap_context":"pipeline/security/zap-context-v1.json","zap_rules":"pipeline/security/zap-rules.conf","dast_dataset":"pipeline/security/dast-dataset-v1.json","osv_descriptor":"pipeline/security/osv-database-v1.json","trivy_descriptor":"pipeline/security/trivy-database-v1.json","dast_contract":"research/dast-test-contract-v1.md","pa001":"research/protocol-amendment-001-osv-offline-cache.md"}
 manifest=json.loads((ROOT/"research/experiment-artifacts-v1.json").read_text())
 state["frozen_inputs"]={k:{"path":v,"sha256":digest(ROOT/v)} for k,v in frozen.items()}
 expected={"semgrep_rules":manifest["semgrep_rules"],"gitleaks_config":manifest["configurations"]["gitleaks"],"checkov_config":manifest["configurations"]["checkov"],"zap_inventory":manifest["zap_addons"]["inventory"],"openapi":manifest["dast"]["openapi"],"zap_context":manifest["dast"]["context"],"zap_rules":manifest["configurations"]["zap_rules"],"dast_dataset":manifest["dast"]["dataset"],"osv_descriptor":manifest["osv_advisory_database"],"trivy_descriptor":manifest["trivy_database"],"dast_contract":manifest["dast"]["contract"],"pa001":manifest["protocol_amendments"]["pa001"]}
 for key,value in expected.items(): state["frozen_inputs"][key]["status"]="READY" if state["frozen_inputs"][key]["sha256"]==value["sha256"] else "NOT_READY"
 artifacts={}
 semarchive=RUNTIME_ROOT/"cache/semgrep-rules-v1.tar.gz"; semmeta=json.loads((ROOT/"pipeline/security/semgrep-rules-v1.json").read_text()); semroot=RUNTIME_ROOT/"semgrep-rules"
 try:
  if semarchive.is_file() and digest(semarchive)==semmeta["source_archive_sha256"]:
   semroot.mkdir(parents=True,exist_ok=True)
   with tarfile.open(semarchive,"r:gz") as tf:
    for member in tf.getmembers():
     parts=Path(member.name).parts
     if len(parts)>1 and parts[1] in ("javascript","typescript") and member.isfile() and Path(parts[-1]).suffix==".yaml":
      rel=Path(*parts[1:]); low=rel.as_posix()
      if "/security/" in low:
       target=semroot/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(tf.extractfile(member).read())
  entries=[]
  for f in sorted([*semroot.rglob("*.yaml")]): entries.append(f"{digest(f)}  {f.relative_to(semroot).as_posix()}\n")
  composite=hashlib.sha256("".join(entries).encode()).hexdigest()
  ok=len(entries)==semmeta["selection"]["rule_file_count"] and composite==semmeta["selection"]["sorted_file_digest_manifest_sha256"]
  artifacts["semgrep_rules"]={"kind":"directory","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/semgrep-rules","expected_sha256":semmeta["selection"]["sorted_file_digest_manifest_sha256"],"observed_sha256":composite,"status":"READY" if ok else "NOT_READY"}
 except Exception as e: artifacts["semgrep_rules"]={"kind":"directory","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/semgrep-rules","status":"NOT_READY","reason":repr(e)}
 osvmeta=json.loads((ROOT/"pipeline/security/osv-database-v1.json").read_text()); osvdb=RUNTIME_ROOT/"cache/osv"/osvmeta["cache_layout"]
 if osvdb.exists():
  actual_b64=md5_base64(osvdb); size=osvdb.stat().st_size; ok=size==osvmeta["size_bytes"] and actual_b64==osvmeta["md5_base64"]
  artifacts["osv_database"]={"kind":"file","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/cache/osv/"+osvmeta["cache_layout"],"expected_md5_base64":osvmeta["md5_base64"],"observed_md5_base64":actual_b64,"expected_size_bytes":osvmeta["size_bytes"],"observed_size_bytes":size,"status":"READY" if ok else "NOT_READY"}
 else: artifacts["osv_database"]={"kind":"file","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/cache/osv/"+osvmeta["cache_layout"],"status":"NOT_READY"}
 for key,rel,expected_sha in (("gitleaks_config","pipeline/security/gitleaks.toml",manifest["configurations"]["gitleaks"]["sha256"]),("checkov_config","pipeline/security/checkov.yaml",manifest["configurations"]["checkov"]["sha256"]),("zap_inventory","pipeline/security/zap-addon-inventory-v1.txt",manifest["zap_addons"]["inventory"]["sha256"]),("openapi","pipeline/security/openapi-corpus-v1.yaml",manifest["dast"]["openapi"]["sha256"]),("zap_context","pipeline/security/zap-context-v1.json",manifest["dast"]["context"]["sha256"])):
  actual=digest(ROOT/rel); artifacts[key]={"kind":"file","runtime_path":str(ROOT/rel),"expected_sha256":expected_sha,"observed_sha256":actual,"status":"READY" if actual==expected_sha else "NOT_READY"}
 trmeta=json.loads((ROOT/"pipeline/security/trivy-database-v1.json").read_text()); trdir=RUNTIME_ROOT/"cache/trivy/db"; metadata=trdir/"metadata.json"; receipt=trdir/"provenance.json"; dbfile=trdir/"trivy.db"
 if metadata.exists():
  try:
   data=json.loads(metadata.read_text()); provenance=json.loads(receipt.read_text())
   ok=data.get("Version")==2 and provenance.get("artifact_digest")==trmeta["artifact_digest"] and provenance.get("layer_digest")==trmeta["layer_digest"] and provenance.get("metadata_sha256")==digest(metadata) and dbfile.is_file()
  except Exception: ok=False
  artifacts["trivy_database"]={"kind":"metadata","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/cache/trivy/db/metadata.json","expected_artifact_digest":trmeta["artifact_digest"],"expected_layer_digest":trmeta["layer_digest"],"expected_layer_size_bytes":trmeta["layer_size_bytes"],"trivy_db_sha256":digest(dbfile) if ok else None,"observed_metadata":data if ok else None,"status":"READY" if ok else "NOT_READY"}
 else: artifacts["trivy_database"]={"kind":"metadata","runtime_path":"${DEVSECOPS_RUNTIME_ROOT}/cache/trivy/db/metadata.json","expected_artifact_digest":trmeta["artifact_digest"],"expected_layer_digest":trmeta["layer_digest"],"status":"NOT_READY"}
 state["artifacts"]=artifacts
 state["frozen_inputs_status"]="READY" if all(x.get("status")=="READY" for x in state["frozen_inputs"].values()) else "NOT_READY"
 state["status"]="READY" if all(x["status"]=="READY" for x in state["tools"].values()) and state["frozen_inputs_status"]=="READY" and all(x.get("status")=="READY" for x in state["artifacts"].values()) else "NOT_READY"
 STATE.write_text(json.dumps(state,indent=2)+"\n"); print(json.dumps(state,indent=2)); return 0 if state["status"]=="READY" else 2
if __name__=="__main__": raise SystemExit(main())
