# Observability Roadmap

Version: 0.1
Status: Draft
Document Type: Infrastructure / Observability
This roadmap does not generate executable code or configuration content.

---

# 0 Current Infrastructure Review

Docker Compose services: postgres, redis, backend, celery, scheduler, frontend, telegram-bot, nginx.

Existing monitoring:
- `infrastructure/monitoring/prometheus.yml` exists but only scrapes `backend:8000`.
- `/metrics` endpoint returns JSON, not Prometheus-format exposition data.
- No metric exporters configured for any service.
- structlog uses `ConsoleRenderer` only — no structured log output suitable for log aggregation.
- No Grafana, Loki, Promtail, Alertmanager, exporters, dashboards, or runbooks deployed.

---

# 1 Missing Components

- Prometheus exporters (postgres_exporter, redis_exporter, celery-exporter, node-exporter) to collect time-series metrics from all services.
- Prometheus config updated to scrape backend, postgres, redis, celery, scheduler, node, and pushgateway (if applicable).
- Loki for log aggregation with structured log ingestion.
- Promtail as log collector/forwarder for all containers.
- Grafana for dashboards and visualization.
- Alertmanager for routing notifications.
- Alert rules and recording rules for SLO monitoring.
- Dashboards covering infrastructure, application, database, and task-queue views.
- Runbooks documenting incident response procedures.
- Proper /metrics format for Prometheus exposition.
- Structured logging pipeline (JSON output via structlog) compatible with Loki ingestion.

---

# 2 Task Breakdown

**2.1 Backend Metrics**
- Replace or extend the `/metrics` endpoint to serve Prometheus exposition format.
- Integrate `prometheus-fastapi-instrumentator` or equivalent middleware.
- Instrument Celery worker, scheduler, and task queue with celery-exporter.
- Add business-level metrics (trades, signals, risk events, AI agent actions).

**2.2 Exporters Deployment**
- Deploy node-exporter for host metrics.
- Deploy postgres_exporter.
- Deploy redis_exporter.
- Deploy celery-exporter for scheduler and worker containers.

**2.3 Logging Pipeline**
- Replace `ConsoleRenderer` with a JSON-formatted processor chain in structlog config.
- Configure Promtail agents per container to tail log files and forward to Loki.
- Define Loki log streams scoped by service and log level.

**2.4 Grafana Setup**
- Provision data sources: Prometheus and Loki.
- Import or author dashboards for infrastructure, backend API, postgres, redis, celery, scheduler, and frontend.
- Define panels for request rate, latency, error rate, queue depth, DB connections, Redis memory, Celery task throughput, agent actions.

**2.5 Alerting & Runbooks**
- Define Alertmanager routing and receivers (e.g., Telegram, email, webhook).
- Write alert rules for SLO violations, service down, queue backlog, high latency, database errors, AI agent error rate.
- Author runbooks in markdown covering each alert class with triage steps and remediation steps without command snippets.

---

# 3 Deliverables

- Updated `/metrics` endpoint serving Prometheus exposition format.
- `infrastructure/monitoring/docker-compose.monitoring.yml` extending or replacing the current compose for observability stack.
- `infrastructure/monitoring/prometheus/prometheus.yml` with full scrape configs and alert rule loading.
- `infrastructure/monitoring/alertmanager/alertmanager.yml` with routing and receivers.
- `infrastructure/monitoring/loki/loki-config.yml`.
- `infrastructure/monitoring/promtail/promtail-config.yml`.
- `infrastructure/monitoring/grafana/dashboards/` directory with dashboard JSON or references.
- `infrastructure/monitoring/grafana/provisioning/` for data source and dashboard provisioning.
- `infrastructure/monitoring/runbooks/` with markdown runbooks per alert category.
- `infrastructure/monitoring/.env.monitoring.example` documenting required environment variables.
- Updated structlog configuration to emit structured (JSON) logs to files.
- Docker Compose service definitions (or updated docker-compose.yml) for all exporters and monitoring services.

---

# 4 Folder Structure

```
infrastructure/monitoring/
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   └── dashboards/
│   └── dashboards/
│       ├── overview.json
│       ├── api.json
│       ├── database.json
│       └── tasks.json
├── loki/
│   └── loki-config.yml
├── promtail/
│   └── promtail-config.yml
├── alertmanager/
│   └── alertmanager.yml
├── runbooks/
│   ├── backend-down.md
│   ├── database-down.md
│   ├── celery-queue-backlog.md
│   └── ai-agent-errors.md
├── .env.monitoring.example
└── docker-compose.monitoring.yml
```

Prometheus scrape targets from docker-compose should reference static_configs for containers and exporters on their respective ports. Alert rule files may be loaded via `rule_files` in `prometheus.yml`.

---

# 5 Configuration Files

- **prometheus.yml**: global settings, scrape configs for backend (8000), postgres_exporter (9187), redis_exporter (9121), celery-exporter (9818), node-exporter (9100), loki (3100), pushgateway (9091 if used), alert rule files.
- **loki-config.yml**: schema config, storage, retention, ingesters, querier.
- **promtail-config.yml**: server, clients, scrape configs for container log paths, pipeline stages for Loki output.
- **alertmanager.yml**: global, templates, route tree, receivers, inhibit rules.
- **.env.monitoring.example**: variables for ports, paths, credentials, notification channels.
- **docker-compose.monitoring.yml**: service definitions for prometheus, grafana, loki, promtail, alertmanager, exporters, volumes, networks, depends_on.

---

# 6 Acceptance Criteria

- Prometheus scrapes metrics from backend, postgres, redis, celery/scheduler, and node exporters without 5xx errors in target status.
- `/metrics` endpoint returns valid Prometheus exposition data (text/plain format).
- Grafana loads Prometheus and Loki data sources and displays dashboards with live data.
- Alertmanager receives and routes test alerts correctly to at least one receiver.
- Runbooks exist for every defined alert rule with step-by-step remediation instructions.
- All services export structured JSON logs consumed by Promtail and queryable via Loki LogQL in Grafana.
- Healthchecks for monitoring services defined in compose.
- .env.monitoring.example documents every required variable with defaults where applicable.
- No plain-text secrets in monitoring configuration files.

---

# 7 References

- Prometheus Exposition Formats: https://prometheus.io/docs/instrumenting/exposition_formats/
- Prometheus Client Python: https://github.com/prometheus/client_python
- Grafana Provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/
- Loki / Promtail Documentation: https://grafana.com/docs/loki/
- Alertmanager Configuration: https://prometheus.io/docs/alerting/latest/configuration/
- Celery Exporter: https://github.com/danihodovic/celery-exporter
- structlog Processors: https://www.structlog.org/en/stable/api.html#processors
- Node Exporter: https://github.com/prometheus/node_exporter
- postgres_exporter: https://github.com/prometheus-community/postgres_exporter
- redis_exporter: https://github.com/oliver006/redis_exporter
