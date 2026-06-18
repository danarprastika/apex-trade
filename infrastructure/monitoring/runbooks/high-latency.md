# Apex High Latency Runbook

## Alert Name

`apex_high_latency`

## Severity

High

## Triage Steps

1. Check slow query logs, long-running transactions, and database lock activity.
2. Check database connection pool usage, saturation, and wait time.
3. Check Redis latency, memory usage, and command duration.
4. Check external API latency for exchange, market data, and notification providers.
5. Check backend, scheduler, and Celery request/task duration distributions.
6. Check infrastructure resource usage for CPU, memory, disk I/O, and network pressure.

## Remediation Steps

1. Scale up resources for backend, database, Redis, Celery, or scheduler if saturation is confirmed.
2. Optimize or pause slow queries when safe and after confirming they are not required for trading safety.
3. Check network latency and connectivity between backend, database, Redis, Celery, and external APIs.
4. Reduce concurrency or throttle non-critical traffic if overload is confirmed.
5. Re-check p95, p99, slow query, Redis latency, and external API latency after remediation.
6. Confirm risk and audit workflows remain within required latency thresholds.

## Escalation Path

Escalate to the on-call engineer if p99 latency exceeds 5 seconds, latency affects trading decisions, or recovery is not immediate.

## Related Dashboards

- Agent Health Dashboard
- API Service Dashboard
- Database Health Dashboard
- Redis Health Dashboard
- Decision Pipeline Dashboard
