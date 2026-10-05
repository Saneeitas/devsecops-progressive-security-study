#!/usr/bin/env python3
"""Normalize frozen-tool JSON reports without assigning seeded-vulnerability IDs."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def sev(value):
    v=str(value or "UNKNOWN").upper()
    return {"ERROR":"HIGH","WARNING":"MEDIUM","WARN":"MEDIUM","FATAL":"CRITICAL"}.get(v,v if v in {"INFO","LOW","MEDIUM","HIGH","CRITICAL"} else "UNKNOWN")
def finding(tool, control, run, rid, title, severity, uri, line=None, raw=None, description=""):
    fp=hashlib.sha256(f"{tool}|{rid}|{uri}|{line}".encode()).hexdigest()
    return {"finding_id":fp[:24],"run_id":run,"tool":tool,"tool_version":"unknown","control":control,"rule_id":rid or "unknown","title":title or rid or "Untitled finding","description":description or "","severity":sev(severity),"native_severity":str(severity) if severity else None,"locations":[{"uri":uri or "unknown","start_line":line,"end_line":line,"component":None}],"classification":"UNRESOLVED","seeded_vulnerability_ids":[],"fingerprint":fp,"raw_artifact":raw,"manual_validation":{"required":True,"status":"PENDING","reviewer":None,"validated_at":None,"rationale":None,"evidence":None}}
def parse(tool, d, run, raw):
    out=[]
    if tool=="semgrep":
        for x in d.get("results",[]): out.append(finding("Semgrep","SAST",run,x.get("check_id"),x.get("extra",{}).get("message"),x.get("extra",{}).get("severity"),x.get("path"),x.get("start",{}).get("line"),raw,x.get("extra",{}).get("metadata",{}).get("shortlink","")))
    elif tool=="gitleaks":
        for x in d: out.append(finding("Gitleaks","SECRET_SCANNING",run,x.get("RuleID"),x.get("Description"),"HIGH",x.get("File"),x.get("StartLine"),raw))
    elif tool=="trivy":
        for r in d.get("Results",[]):
            for x in r.get("Vulnerabilities",[]) or []: out.append(finding("Trivy","CONTAINER_SCANNING",run,x.get("VulnerabilityID"),x.get("Title"),x.get("Severity"),r.get("Target"),None,raw,x.get("Description","")))
    elif tool=="checkov":
        for x in d.get("results",{}).get("failed_checks",[]): out.append(finding("Checkov","IAC_SCANNING",run,x.get("check_id"),x.get("check_name"),x.get("severity"),x.get("file_path"),x.get("file_line_range",[None])[0],raw,x.get("description","")))
    elif tool=="osv":
        for x in d.get("results",[]): 
            for p in x.get("packages",[]): 
                for v in p.get("vulnerabilities",[]): out.append(finding("OSV-Scanner","SCA",run,v.get("id"),v.get("summary"),"UNKNOWN","application/package-lock.json",None,raw))
    elif tool=="zap":
        for x in d.get("site",[]):
            for a in x.get("alerts",[]): out.append(finding("OWASP ZAP","DAST",run,a.get("pluginid"),a.get("alert"),a.get("riskdesc","").split()[0],a.get("url"),None,raw,a.get("desc","")))
    return out
def main():
    p=argparse.ArgumentParser(); p.add_argument("--tool",choices=["semgrep","osv","gitleaks","trivy","checkov","zap"],required=True); p.add_argument("--input",required=True); p.add_argument("--run-id",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    d=json.loads(Path(a.input).read_text()); Path(a.output).write_text(json.dumps(parse(a.tool,d,a.run_id,a.input),indent=2)+"\n")
if __name__=="__main__": main()
