#!/usr/bin/env python3
"""Synthetic outcome-semantic tests. No scanner or corpus execution occurs."""
from experiment import outcome_for_stages

def check(stages, validity, failure):
 result=outcome_for_stages(stages)
 assert result["validity"]==validity, result
 assert result["failure_stage"]==failure, result

check([{"stage":"functional_tests","status":"EXPECTED_CORPUS_TEST_FAILURE"}],"VALID",None)
check([{"stage":"functional_tests","status":"ERROR"}],"INVALID_RETRYABLE","functional_tests")
check([{"stage":"database_readiness","status":"EXPERIMENT_INFRASTRUCTURE_ERROR"}],"INVALID_RETRYABLE","database_readiness")
check([{"stage":"SAST","status":"SCAN_COMPLETED_WITH_FINDINGS"}],"VALID",None)
check([{"stage":"SAST","status":"SCANNER_EXECUTION_ERROR"}],"INVALID_RETRYABLE","SAST")
print("outcome semantics: PASS")
