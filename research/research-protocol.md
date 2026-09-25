# Research Protocol

## Working Title
Evaluating the Security Effectiveness and Operational Impact of Progressive Security Control Integration in DevSecOps Pipelines

## Research Area
DevSecOps; Cloud Security; Application Security; Cloud-Native Security.

## Primary Objective
To empirically evaluate how progressively integrating automated security controls into a CI/CD pipeline affects vulnerability-detection effectiveness and operational pipeline performance.

## Research Questions

**RQ1.** How does progressive integration of automated security controls affect vulnerability detection coverage in a CI/CD pipeline?

**RQ2.** How does progressive integration of automated security controls affect CI/CD operational performance?

**RQ3.** What is the marginal security benefit associated with each additional security-control layer?

**RQ4.** What trade-off exists between security effectiveness and operational overhead across different security-control configurations?

## Current Phase
Baseline environment construction. No deliberately seeded vulnerabilities or security scanners are included yet.

## Planned Experimental Progression
0. Baseline: build, test, deploy.
1. Add SAST.
2. Add SCA.
3. Add secret scanning.
4. Add container scanning.
5. Add IaC scanning.
6. Add DAST and a security gate.

## Reproducibility Notes
Record tool versions, runner specifications, application commit SHA, environment configuration, test corpus version, timestamps, and raw measurements for every experimental run.
