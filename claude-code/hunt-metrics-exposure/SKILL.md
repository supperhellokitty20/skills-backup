---
name: hunt-metrics-exposure
description: "Hunt public /metrics, /health, and actuator endpoints leaking AI usage, DB pools, and operational intelligence."
version: 1.1.0
revision_date: 2026-07-25
license: MIT
category: redteam
tags: [metrics, exposure, hunt, redteam]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

## When to Use

The target uses modern observability tooling (Go, .NET, Java, Node.js). These frameworks often expose `/metrics`, `/health`, and `/status` endpoints that are forgotten behind auth. Unlike application data leaks, metrics leaks reveal the ENTIRE operational profile: which AI models are used, how many users are active, database connection exhaustion, and third-party service dependencies.

---

## Phase 1 — Discover Metrics Endpoints

```bash
TARGET="https://target.com"

# Common observability paths
for ep in metrics health status ready live readyz healthz \
  actuator/health actuator/metrics actuator/prometheus \
  Telescope telescope horizon debug; do
  code=$(curl --max-time 30 --connect-timeout 10 -sk -o /tmp/metrics_${ep}.txt -w "%{http_code}" \
    "${TARGET}/${ep}" 2>/dev/null)
  if [ "$code" = "200" ]; then
    size=$(wc -c < /tmp/metrics_${ep}.txt)
    echo "  /${ep}: HTTP 200 (${size} bytes)"
  fi
done
```

---

## Phase 2 — Analyze Prometheus Metrics

```bash
# Count unique metric families (each reveals a subsystem)
grep -c '^# HELP' /tmp/metrics_metrics.txt

# Extract AI/ML model usage
grep -i 'ai_\|model\|llm\|openai\|gemini\|copilot' /tmp/metrics_metrics.txt

# Extract database pool states
grep -i 'db_pool\|database\|connection' /tmp/metrics_metrics.txt

# Extract third-party dependencies
grep -i 'stripe\|openai\|sendgrid\|twilio\|email' /tmp/metrics_metrics.txt

# Extract request volumes (user activity)
grep -i 'http_request\|api_request\|grpc_request' /tmp/metrics_metrics.txt

# Extract circuit breaker states (service health)
grep -i 'circuit_breaker' /tmp/metrics_metrics.txt
```

---

## Phase 3 — Analyze Health/Status Endpoints

```bash
# Spring Boot Actuator
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/actuator/health" | python3 -m json.tool
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/actuator/metrics" | python3 -m json.tool
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/actuator/env" | python3 -m json.tool  # May leak env vars

# Custom health endpoints
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/health" | python3 -m json.tool
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/api/health" | python3 -m json.tool

# Laravel Telescope (if exposed)
curl --max-time 30 --connect-timeout 10 -sk "${TARGET}/telescope/requests" | head -c 500
```

---

## What Metrics Reveal

| Metric | Intelligence Gained |
|--------|-------------------|
| `ai_analyzer_output_total{model="gpt-5-mini"}` | Which AI models are used, usage volume |
| `db_pool_idle_connections{pool="api"}` | Database pool sizing, connection exhaustion risk |
| `circuit_breaker_state{client="stripe"}` | Third-party dependencies and their health |
| `clinical_copilot_sse_active` | Real-time user count for specific features |
| `http_requests_total` | Request volume, peak hours, user activity |
| `app_version` / `build_info` | Deployed version, build timestamps |

---

## Verification

- **Confirmed exposure**: `/metrics` returns Prometheus text format (lines starting with `# HELP` or `# TYPE`)
- **Actuator exposure**: `/actuator/health` returns JSON with component statuses
- **False positive**: Endpoint returns `{"status":"ok"}` only (minimal health check, not a metrics leak)
- **Severity upgrade**: If `/actuator/env` or `/actuator/configprops` is exposed → CRITICAL (environment variables leaked)

---

## What Next

- AI model usage metrics → pivot to `hunt-llm-ai` (prompt injection on discovered models)
- DB pool metrics showing overload → DoS attack surface identified
- Circuit breaker states for Stripe/email → infrastructure dependency map for chained attacks
- Combine with `hunt-schema-enumeration` for full target profile

---

## Verification

Run this self-test to confirm metrics-exposure hunting readiness:

1. **Skill integrity** — confirm the skill file is readable and well-formed:
   ```bash
   grep -q "name: hunt-metrics-exposure" SKILL.md && echo "PASS: skill frontmatter present" || echo "FAIL"
   grep -q "revision_date:" SKILL.md && echo "PASS: revision date present" || echo "FAIL"
   ```

2. **Category check** — confirm the skill has a category:
   ```bash
   grep -q "category:" SKILL.md && echo "PASS: category present" || echo "FAIL"
   ```

3. **Pitfalls section** — confirm pitfalls are documented:
   ```bash
   grep -q "^## Pitfalls" SKILL.md && echo "PASS: pitfalls section present" || echo "FAIL"
   ```

All 3 tests verify the skill is properly structured and ready for use.

---

## Pitfalls
- **Prometheus /metrics without secrets** — metrics endpoints exposing request counts are informational. Need labels containing PII, internal hostnames, or credentials.
- **Spring Boot Actuator /actuator/metrics** — metrics are intentionally exposed for monitoring. Only report if they leak sensitive data (usernames in labels, internal IPs).
- **JMX without auth** — JMX exposure without authentication is critical only if write operations (MBean invocation) are possible. Read-only JMX is informational.
- **Health endpoint without sensitive data** — `/health`, `/status`, `/ready` endpoints are designed to be public. Need leaked internal data.

## MANDATORY ON INVOCATION — PROTOCOL RESTATMENT (END OF FILE)

You have reached the end of this SKILL.md. The invocation protocol below is identical to the one at the top of this file. If you are reading this, the full skill context is loaded — confirm the checklist.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started
