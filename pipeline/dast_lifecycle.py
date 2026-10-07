#!/usr/bin/env python3
"""Build deterministic, isolated DAST preconditions and the frozen two-pass ZAP run."""
from __future__ import annotations
import argparse, datetime as dt, json, os, secrets, subprocess, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IMAGE_ZAP="ghcr.io/zaproxy/zaproxy@sha256:71db37cd5b75663b35758d10aaec05bf6fbac23f5020e3046c70e628a5f84efa"
OUTER_TIMEOUT=1800

class DastError(RuntimeError): pass

def docker(args,timeout=30,check=True,env=None):
    try: p=subprocess.run(["docker",*args],cwd=ROOT,text=True,capture_output=True,timeout=timeout,env=env)
    except subprocess.TimeoutExpired as e: raise DastError(f"Docker command timed out after {timeout}s: {args[0]}") from e
    if check and p.returncode: raise DastError(f"Docker {args[0]} failed ({p.returncode}): {(p.stderr or p.stdout)[-2000:]}")
    return p

def api_node_script(dataset):
    actors=dataset["actors"]
    expected={x["email"]:{"id":x["expected_id_after_clean_reset"],"role":x["role"]} for x in dataset["expected_users"]}
    return r'''const http=require('http');
const actors=JSON.parse(process.env.DAST_ACTORS);
const expected=JSON.parse(process.env.DAST_EXPECTED_USERS);
function req(path,method='GET',body=null,token=null){return new Promise((resolve,reject)=>{
 const data=body===null?null:Buffer.from(JSON.stringify(body));
 const headers={'Content-Type':'application/json'}; if(token) headers.Authorization='Bearer '+token; if(data) headers['Content-Length']=data.length;
 const r=http.request({hostname:'127.0.0.1',port:3000,path,method,headers},res=>{let raw='';res.setEncoding('utf8');res.on('data',x=>raw+=x);res.on('end',()=>{let parsed={};try{parsed=raw?JSON.parse(raw):{}}catch{} resolve({status:res.statusCode,body:parsed})})});
 r.on('error',reject); if(data)r.write(data);r.end();
})}
(async()=>{
 const identities={}; const tokens={};
 for(const email of [actors.normal_user_a,actors.normal_user_b,actors.admin]){
  const password=email===actors.admin?process.env.SEED_ADMIN_PASSWORD:process.env.SEED_USER_PASSWORD;
  const login=await req('/api/auth/login','POST',{email,password});
  const want=expected[email]; const user=login.body.user||{};
  if(login.status!==200||!login.body.token||user.id!==want.expected_id_after_clean_reset||user.role!==want.role)throw new Error('synthetic identity assertion failed');
  identities[email]=login.body.token;
 }
 const order=await req('/api/orders','POST',{items:[{productId:1,quantity:1}]},identities[actors.normal_user_b]);
 const orderId=(order.body.order||{}).id;
 if(order.status!==201||orderId!==Number(process.env.DAST_EXPECTED_ORDER_ID))throw new Error('Bob order fixture assertion failed');
 const alice=await req('/api/orders/'+orderId,'GET',null,identities[actors.normal_user_a]);
 if(![200,403,404].includes(alice.status))throw new Error('Alice order precondition request returned an invalid HTTP status');
 process.stdout.write(JSON.stringify({tokens:{alice:identities[actors.normal_user_a],admin:identities[actors.admin]},alice_login:'OK',bob_login:'OK',admin_login:'OK',bob_order_id:orderId,alice_cross_user_request_status:alice.status}));
})().catch(()=>{process.stderr.write('synthetic API precondition assertion failed\n');process.exit(2)});'''

def identity_environment(dataset):
    expected={x["email"]:{"expected_id_after_clean_reset":x["expected_id_after_clean_reset"],"role":x["role"]} for x in dataset["expected_users"]}
    return {"DAST_ACTORS":json.dumps(dataset["actors"],separators=(",",":")),"DAST_EXPECTED_USERS":json.dumps(expected,separators=(",",":")),"DAST_EXPECTED_ORDER_ID":str(dataset["precondition_order"]["expected_id_after_clean_reset"])}

def write_json(path,obj): path.write_text(json.dumps(obj,indent=2)+"\n")

def redact(text,secrets_to_hide):
    for value in secrets_to_hide:
        if value: text=text.replace(value,"[REDACTED]")
    return text

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--run-dir",required=True); ap.add_argument("--image",required=True); ap.add_argument("--execute",action="store_true"); ap.add_argument("--prepare-only",action="store_true"); a=ap.parse_args()
    d=Path(a.run_dir).resolve(); raw=d/"raw"; logs=d/"logs"; raw.mkdir(parents=True,exist_ok=True); logs.mkdir(exist_ok=True)
    suffix="".join(c.lower() if c.isalnum() else "-" for c in d.name).strip("-")
    prefix="devsecops-dast-"+suffix; network=prefix+"-net"; volume=prefix+"-pg"; pg=prefix+"-postgres"; api=prefix+"-api"
    dataset=json.loads((ROOT/"pipeline/security/dast-dataset-v1.json").read_text()); context=json.loads((ROOT/"pipeline/security/zap-context-v1.json").read_text())
    plan={"contract":"research/dast-test-contract-v1.md","steps":["create isolated internal Docker network and fresh volume","start PostgreSQL 16-alpine without published ports","wait readiness","run migrations and seed in the application image on the internal network","start application container without published ports","verify health from inside the application container","authenticate synthetic Alice/Bob/admin and establish order precondition from inside the network","run frozen ZAP user API pass","run frozen ZAP admin API pass","bounded cleanup"],"outer_timeout_seconds":OUTER_TIMEOUT,"network":network,"volume":volume,"application_image":a.image}
    write_json(d/"dast-lifecycle-plan.json",plan)
    if not a.execute: print("DAST plan only; no runtime or target started."); return 0
    start=time.monotonic_ns(); wall_deadline=time.monotonic()+OUTER_TIMEOUT; names=[]; errors=[]; envfile=None; tokens={}; timings=[]; result={"status":"ERROR","steps":[],"cleanup":{"status":"NOT_RUN"}}
    runtime_db_password=secrets.token_urlsafe(32); jwt=secrets.token_urlsafe(48)
    seed_admin=os.environ.get("SEED_ADMIN_PASSWORD"); seed_user=os.environ.get("SEED_USER_PASSWORD")
    if not seed_admin or not seed_user: raise DastError("DAST precondition environment lacks generated synthetic seed passwords")
    try:
        t=time.monotonic_ns(); docker(["network","create","--internal",network]); result["steps"].append({"stage":"network_create","duration_ms":round((time.monotonic_ns()-t)/1e6,3)}); names.append(("network",network))
        t=time.monotonic_ns(); docker(["volume","create",volume]); result["steps"].append({"stage":"database_volume_create","duration_ms":round((time.monotonic_ns()-t)/1e6,3)}); names.append(("volume",volume))
        fd,envpath=tempfile.mkstemp(prefix="dast-runtime-",suffix=".env"); os.close(fd); envfile=Path(envpath); os.chmod(envfile,0o600)
        pg_env={"POSTGRES_USER":"postgres","POSTGRES_PASSWORD":runtime_db_password,"POSTGRES_DB":"devsecops_dast"}
        envfile.write_text("".join(f"{k}={v}\n" for k,v in pg_env.items()))
        t=time.monotonic_ns(); docker(["run","--pull=never","-d","--name",pg,"--label","devsecops.experiment=dast","--network",network,"--network-alias","postgres","--env-file",str(envfile),"--mount",f"type=volume,src={volume},dst=/var/lib/postgresql/data","postgres:16-alpine"]); names.append(("container",pg)); result["steps"].append({"stage":"database_start","duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
        t=time.monotonic_ns(); deadline=min(wall_deadline,time.monotonic()+90)
        while time.monotonic()<deadline:
            check=docker(["exec",pg,"pg_isready","-U","postgres","-d","devsecops_dast"],check=False,timeout=10)
            if check.returncode==0: break
            time.sleep(1)
        else: raise DastError("DAST database readiness timed out")
        result["steps"].append({"stage":"database_readiness","duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
        database_url="postgresql://postgres:"+runtime_db_password+"@postgres:5432/devsecops_dast"
        app_env={"PORT":"3000","NODE_ENV":"production","DATABASE_URL":database_url,"JWT_SECRET":jwt,"JWT_EXPIRES_IN":"1h","CORS_ORIGIN":"http://localhost:3000","SEED_ADMIN_PASSWORD":seed_admin,"SEED_USER_PASSWORD":seed_user,**identity_environment(dataset)}
        envfile.write_text("".join(f"{k}={v}\n" for k,v in app_env.items())); os.chmod(envfile,0o600)
        for label,script in (("migration","dist/db/migrate.js"),("seed","dist/db/seed.js")):
            t=time.monotonic_ns(); docker(["run","--pull=never","--rm","--network",network,"--env-file",str(envfile),"--entrypoint","node",a.image,script],timeout=300); result["steps"].append({"stage":label,"duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
        envfile.write_text("".join(f"{k}={v}\n" for k,v in app_env.items())); os.chmod(envfile,0o600)
        t=time.monotonic_ns(); docker(["run","--pull=never","-d","--name",api,"--label","devsecops.experiment=dast","--network",network,"--network-alias","api","--env-file",str(envfile),a.image]); names.append(("container",api)); result["steps"].append({"stage":"application_start","duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
        t=time.monotonic_ns(); ready=False; app_deadline=min(wall_deadline,time.monotonic()+180)
        health_script="const h=require('http');h.get('http://127.0.0.1:3000/api/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"
        while time.monotonic()<app_deadline:
            check=docker(["exec",api,"node","-e",health_script],check=False,timeout=10)
            if check.returncode==0: ready=True; break
            time.sleep(2)
        if not ready: raise DastError("DAST application health readiness timed out")
        result["steps"].append({"stage":"application_readiness","duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
        t=time.monotonic_ns(); identity_script=api_node_script(dataset)
        identity=docker(["exec",api,"node","-e",identity_script],check=False,timeout=90)
        if identity.returncode: raise DastError("synthetic DAST identity/order precondition checks failed")
        try: identity_result=json.loads(identity.stdout)
        except Exception as e: raise DastError("synthetic DAST precondition result was invalid JSON") from e
        if identity_result.get("bob_order_id")!=dataset["precondition_order"]["expected_id_after_clean_reset"]: raise DastError("Bob order fixture did not resolve to the frozen order ID")
        tokens[dataset["actors"]["normal_user_a"]]=identity_result["tokens"]["alice"]
        tokens[dataset["actors"]["admin"]]=identity_result["tokens"]["admin"]
        result["steps"].append({"stage":"synthetic_auth_and_order_preconditions","duration_ms":round((time.monotonic_ns()-t)/1e6,3),"alice_login":identity_result["alice_login"],"bob_login":identity_result["bob_login"],"admin_login":identity_result["admin_login"],"bob_order_id":identity_result["bob_order_id"],"alice_cross_user_request_status":identity_result["alice_cross_user_request_status"]})
        if a.prepare_only:
            result["status"]="PRECONDITIONS_READY"; return_code=0
        else:
            # Render only the frozen target/token substitutions into a runtime
            # private ZAP context. Scanner modes, rules, payloads, and endpoints
            # remain fixed by the checked-in contract.
            results=[]; openapi=ROOT/"pipeline/security/openapi-corpus-v1.yaml"; rules=ROOT/"pipeline/security/zap-rules.conf"
            principals={"alice@example.com":dataset["actors"]["normal_user_a"],"admin@example.com":dataset["actors"]["admin"]}
            token_env={}
            for pass_spec in context["passes"]:
                principal=principals[pass_spec["principal"]]
                token_env[pass_spec["token_environment_variable"]]=tokens[principal]
            for pass_spec in context["passes"]:
                pass_id=pass_spec["id"]; principal=principals[pass_spec["principal"]]
                if time.monotonic()>=wall_deadline: raise DastError("DAST outer timeout reached")
                report=f"/zap/wrk/zap-{pass_id}.json"; token=tokens[principal]
                header=context["authentication"]["header"]; scheme=context["authentication"]["scheme"]
                token=token_env[pass_spec["token_environment_variable"]]
                replacer=" ".join(["-config","replacer.full_list(0).description=DAST bearer context","-config","replacer.full_list(0).enabled=true","-config","replacer.full_list(0).matchtype=REQ_HEADER","-config",f"replacer.full_list(0).matchstr={header}","-config",f"replacer.full_list(0).replacement={scheme} {token}"])
                command=["docker","run","--pull=never","--rm","--platform","linux/amd64","--network",network,"-v",f"{ROOT}:/research:ro","-v",f"{raw}:/zap/wrk","--entrypoint","zap-api-scan.py",IMAGE_ZAP,"-t","/research/pipeline/security/openapi-corpus-v1.yaml","-f","openapi","-c","/research/pipeline/security/zap-rules.conf","-J",report,"-T","15","-z",replacer]
                # Secrets are excluded from command logs and exception text.
                t=time.monotonic_ns()
                try: p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=min(900,max(1,int(wall_deadline-time.monotonic()))))
                except subprocess.TimeoutExpired as e: raise DastError(f"ZAP {pass_id} pass timed out") from e
                (logs/f"zap-{pass_id}.stdout.log").write_text(redact(p.stdout or "",tokens.values())); (logs/f"zap-{pass_id}.stderr.log").write_text(redact(p.stderr or "",tokens.values()))
                report_path=raw/f"zap-{pass_id}.json"
                if report_path.exists(): report_path.write_text(redact(report_path.read_text(errors="replace"),tokens.values()))
                results.append({"pass":pass_id,"status":"COMPLETED" if p.returncode in (0,1,2) else "ERROR","native_exit_code":p.returncode,"raw_artifact":f"zap-{pass_id}.json","duration_ms":round((time.monotonic_ns()-t)/1e6,3)})
                if p.returncode==3: raise DastError(f"ZAP {pass_id} operational execution error")
            result["zap_passes"]=results; result["status"]="COMPLETED"; return_code=0
    except Exception as e:
        result["status"]="ERROR"; result["error"]=str(e); return_code=2
    finally:
        secrets_for_scan=[runtime_db_password,jwt,seed_admin,seed_user,*tokens.values()]
        tokens.clear()
        if envfile:
            try: envfile.unlink(missing_ok=True)
            except Exception as e: errors.append({"resource":"runtime-env-file","error":repr(e)})
        cleanup_start=time.monotonic_ns(); cleanup=[]
        for kind,name in reversed(names):
            try:
                args={"container":["rm","-f",name],"network":["network","rm",name],"volume":["volume","rm",name]}[kind]
                r=docker(args,timeout=20,check=False)
                if r.returncode:
                    check=docker(({"container":["inspect",name],"network":["network","inspect",name],"volume":["volume","inspect",name]}[kind]),timeout=10,check=False)
                    absent=check.returncode!=0 and any(marker in (check.stderr or check.stdout).lower() for marker in ("no such object","no such volume","not found"))
                    cleanup.append({"resource":kind,"name":name,"status":"REMOVED" if absent else "ERROR","detail":None if absent else (r.stderr or r.stdout)[-1000:]})
                else: cleanup.append({"resource":kind,"name":name,"status":"REMOVED"})
            except Exception as e: cleanup.append({"resource":kind,"name":name,"status":"ERROR","detail":repr(e)})
        result["cleanup"]={"status":"OK" if all(x["status"]!="ERROR" for x in cleanup) and not errors else "ERROR","duration_ms":round((time.monotonic_ns()-cleanup_start)/1e6,3),"resources":cleanup,"errors":errors}
        checked=0; leaked=[]
        for path in d.rglob("*"):
            if not path.is_file(): continue
            checked+=1
            try: content=path.read_bytes()
            except Exception: leaked.append(path.relative_to(d).as_posix()); continue
            if any(value and value.encode() in content for value in secrets_for_scan): leaked.append(path.relative_to(d).as_posix())
        result["secret_artifact_check"]={"status":"FAIL" if leaked else "PASS","files_checked":checked,"leaked_file_count":len(leaked)}
        result["total_ms"]=round((time.monotonic_ns()-start)/1e6,3)
        write_json(d/"dast-lifecycle.json",result)
    if result["cleanup"]["status"]!="OK": return_code=2
    if result.get("secret_artifact_check",{}).get("status")!="PASS": return_code=2
    return return_code

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e: print(f"EXPERIMENT_INFRASTRUCTURE_ERROR: {e}",file=__import__("sys").stderr); raise SystemExit(2)
