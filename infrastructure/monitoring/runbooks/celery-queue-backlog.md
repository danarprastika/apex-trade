# Apex Celery Queue Backlog Runbook

## Alert Name

`apex_celery_queue_backlog`

## Severity

High

## Triage Steps

1. Check Celery worker status, process count, and restart history.
2. Check broker connectivity to Redis and authentication state.
3. Check task throughput, queue depth, oldest pending item, retry count, and dead letter queue size.
4. Check Celery worker logs for task errors, repeated retries, and broker connection failures.
5. Check backend and scheduler logs for upstream task publishing spikes or malformed tasks.
6. Review recent deployments, migrations, or configuration changes affecting task processing.

## Remediation Steps

1. Restart Celery workers if they are unhealthy, stuck, or disconnected from the broker.
2. Scale up Celery workers when backlog is caused by insufficient processing capacity.
3. Check the dead letter queue and requeue safe tasks after root-cause validation.
4. Clear or archive stuck tasks only after confirming they are not required for trading safety or audit reconciliation.
5. Re-check throughput, queue depth, and oldest pending item after remediation.
6. Confirm backend-dependent workflows have resumed normally.

## Escalation Path

Escalate to the engineering lead if backlog exceeds 5,000 tasks, grows continuously after remediation, or affects trading/risk workflows.

## Related Dashboards

- Task Queue Dashboard
- Agent Health Dashboard
- Decision Pipeline Dashboard
- Infrastructure Overview Dashboard
