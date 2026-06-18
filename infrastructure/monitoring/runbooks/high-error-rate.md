# Apex High Error Rate Runbook

## Alert Name

`apex_high_error_rate`

## Severity

High

## Triage Steps

1. Check backend, scheduler, Celery, and frontend error logs.
2. Check error distribution by endpoint, status code, agent, and task type.
3. Check dependency errors, including PostgreSQL timeout, Redis timeout, exchange API errors, and broker failures.
4. Check whether the error rate increase started after a deployment, migration, feature flag change, or market-data event.
5. Check circuit breaker, retry, and rate-limiting state.
6. Confirm whether errors affect trading, risk, audit, or user-facing flows.

## Remediation Steps

1. Roll back the recent backend, scheduler, Celery, or frontend deployment if the error spike is release-correlated.
2. Check circuit breaker status and reset or isolate failing dependencies when safe.
3. Throttle traffic if overload is confirmed and user safety is not compromised.
4. Disable or pause affected high-risk agent workflows if errors affect trading or risk decisions.
5. Re-check error rate, endpoint distribution, and dependency health after remediation.
6. Open a post-incident review if the incident affected trading, audit, or governance workflows.

## Escalation Path

Escalate immediately if error rate exceeds 20%, affects trading execution, blocks risk controls, or causes audit log gaps.

## Related Dashboards

- Agent Health Dashboard
- API Service Dashboard
- Decision Pipeline Dashboard
- Execution Quality Dashboard
- Security and Audit Dashboard
