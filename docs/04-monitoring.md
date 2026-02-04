# Monitoring & Error Handling

## Table of Contents

- [Observability Strategy](#observability-strategy)
- [Logging](#logging)
- [Metrics](#metrics)
- [Tracing](#tracing)
- [Alerting](#alerting)
- [Error Handling Patterns](#error-handling-patterns)
- [Incident Response](#incident-response)

## Observability Strategy

AI agents require specialized monitoring due to their autonomous nature:

```
┌─────────────────────────────────────────────────┐
│               Observability Stack                │
├─────────────────────────────────────────────────┤
│  Logs      │  Metrics     │  Traces             │
├────────────┼──────────────┼─────────────────────┤
│ Structured │ Prometheus   │ OpenTelemetry       │
│ JSON logs  │ + Grafana    │ Distributed tracing │
└─────────────────────────────────────────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                           │
                  ┌────────▼────────┐
                  │   Alert Manager  │
                  │   PagerDuty      │
                  └──────────────────┘
```

## Logging

### Structured Logging

```python
import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log_agent_event(self, event_type: str, **kwargs):
        """Log agent event with structured data."""
        self.logger.info('agent_event', extra={
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        })

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }

        # Add extra fields
        if hasattr(record, 'event_type'):
            log_data.update(record.__dict__)
            # Remove standard fields
            for key in ['msg', 'args', 'levelname', 'levelno', 'pathname',
                        'filename', 'module', 'lineno', 'funcName', 'created',
                        'msecs', 'relativeCreated', 'thread', 'threadName',
                        'processName', 'process', 'name']:
                log_data.pop(key, None)

        return json.dumps(log_data)

# Usage
logger = StructuredLogger('openclaw.agent')

logger.log_agent_event('session_started',
    agent_id='abc-123',
    user_id='user-456',
    tools=['Read', 'Edit'],
    budget_usd=5.0
)

logger.log_agent_event('tool_invoked',
    agent_id='abc-123',
    tool='Bash',
    command='git status',
    approved=True
)

logger.log_agent_event('session_completed',
    agent_id='abc-123',
    duration_seconds=180,
    cost_usd=2.34,
    success=True
)
```

### Critical Log Events

**Events that should always be logged:**

| Event | Fields | Severity |
|-------|--------|----------|
| `agent_started` | agent_id, user_id, tools, budget | INFO |
| `tool_invoked` | agent_id, tool, parameters, approved | INFO |
| `tool_blocked` | agent_id, tool, reason | WARNING |
| `approval_requested` | agent_id, action, risk_level | INFO |
| `approval_denied` | agent_id, action, reason | WARNING |
| `budget_exceeded` | agent_id, limit, actual | WARNING |
| `timeout` | agent_id, duration | ERROR |
| `error` | agent_id, error_type, stack_trace | ERROR |
| `security_violation` | agent_id, violation_type, details | CRITICAL |
| `agent_completed` | agent_id, duration, cost, success | INFO |

## Metrics

### Key Metrics to Track

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters
agent_sessions_total = Counter(
    'openclaw_agent_sessions_total',
    'Total agent sessions started',
    ['user_id', 'agent_type']
)

tool_invocations_total = Counter(
    'openclaw_tool_invocations_total',
    'Total tool invocations',
    ['tool', 'status']  # status: success, error, blocked
)

security_violations_total = Counter(
    'openclaw_security_violations_total',
    'Security violations detected',
    ['violation_type']
)

# Histograms
session_duration_seconds = Histogram(
    'openclaw_session_duration_seconds',
    'Agent session duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

api_cost_usd = Histogram(
    'openclaw_api_cost_usd',
    'API cost per session in USD',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Gauges
active_sessions = Gauge(
    'openclaw_active_sessions',
    'Number of currently active agent sessions'
)

budget_remaining_usd = Gauge(
    'openclaw_budget_remaining_usd',
    'Remaining budget in USD',
    ['user_id']
)

# Usage
agent_sessions_total.labels(user_id='user-123', agent_type='developer').inc()
tool_invocations_total.labels(tool='Bash', status='success').inc()
session_duration_seconds.observe(180.5)
api_cost_usd.observe(2.34)
active_sessions.inc()
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "OpenClaw Agent Monitoring",
    "panels": [
      {
        "title": "Active Sessions",
        "targets": [
          {
            "expr": "openclaw_active_sessions"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Session Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, openclaw_session_duration_seconds_bucket)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Cost per Hour",
        "targets": [
          {
            "expr": "rate(openclaw_api_cost_usd_sum[1h])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Security Violations",
        "targets": [
          {
            "expr": "rate(openclaw_security_violations_total[5m])"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

## Tracing

### Distributed Tracing with OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Usage
def execute_agent_session(task: str):
    with tracer.start_as_current_span("agent_session") as span:
        span.set_attribute("agent.id", "abc-123")
        span.set_attribute("agent.type", "developer")

        # Phase 1: Planning
        with tracer.start_as_current_span("planning"):
            plan = create_plan(task)
            span.set_attribute("plan.steps", len(plan.steps))

        # Phase 2: Execution
        with tracer.start_as_current_span("execution"):
            for step in plan.steps:
                with tracer.start_as_current_span(f"step_{step.id}"):
                    execute_step(step)

        # Phase 3: Validation
        with tracer.start_as_current_span("validation"):
            result = validate_result()
            span.set_attribute("validation.passed", result.success)

        return result
```

## Alerting

### Alert Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: openclaw_agent_alerts
    interval: 1m
    rules:
      # Cost alerts
      - alert: HighAPICost
        expr: rate(openclaw_api_cost_usd_sum[1h]) > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API cost detected"
          description: "API costs exceed $50/hour"

      - alert: BudgetExceeded
        expr: openclaw_budget_remaining_usd < 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "User budget exceeded"
          description: "User {{ $labels.user_id }} has exceeded their budget"

      # Security alerts
      - alert: SecurityViolation
        expr: rate(openclaw_security_violations_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Security violation detected"
          description: "{{ $value }} security violations in last 5 minutes"

      # Performance alerts
      - alert: HighSessionDuration
        expr: histogram_quantile(0.95, openclaw_session_duration_seconds_bucket) > 600
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent sessions taking too long"
          description: "P95 session duration is {{ $value }}s"

      # Reliability alerts
      - alert: HighErrorRate
        expr: rate(openclaw_tool_invocations_total{status="error"}[5m]) / rate(openclaw_tool_invocations_total[5m]) > 0.1
        for: 5m
        labels:
          severity: error
        annotations:
          summary: "High tool error rate"
          description: "{{ $value | humanizePercentage }} of tool invocations are failing"

      - alert: AgentStuck
        expr: openclaw_active_sessions > 0 and rate(openclaw_tool_invocations_total[5m]) == 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent appears stuck"
          description: "Active sessions but no tool activity for 10 minutes"
```

### Alert Manager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@example.com'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<key>'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#openclaw-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}'
```

## Error Handling Patterns

### Graceful Degradation

```python
class ResilientAgent:
    def execute(self, task: str, budget: float):
        try:
            return self._execute_with_full_features(task, budget)
        except BudgetExceededError as e:
            logger.warning("Budget exceeded, switching to cheaper model")
            return self._execute_with_cheaper_model(task, budget * 0.5)
        except ModelOverloadedError as e:
            logger.warning("Model overloaded, retrying with backoff")
            time.sleep(2 ** retry_count)
            return self.execute(task, budget)
        except ToolUnavailableError as e:
            logger.error(f"Tool {e.tool} unavailable, using fallback")
            return self._execute_with_fallback_tools(task, budget)
```

### Checkpoint and Recovery

```python
class CheckpointableAgent:
    def __init__(self):
        self.checkpoint_dir = '/workspace/.checkpoints'
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def execute_with_checkpoints(self, plan: Plan):
        """Execute plan with checkpoints for recovery."""
        for i, step in enumerate(plan.steps):
            checkpoint_file = f"{self.checkpoint_dir}/step_{i}.json"

            # Check if we can resume from checkpoint
            if os.path.exists(checkpoint_file):
                logger.info(f"Resuming from checkpoint: step {i}")
                continue

            try:
                result = self.execute_step(step)

                # Save checkpoint
                with open(checkpoint_file, 'w') as f:
                    json.dump({
                        'step': i,
                        'result': result,
                        'timestamp': datetime.utcnow().isoformat()
                    }, f)

            except Exception as e:
                logger.error(f"Step {i} failed: {e}")
                logger.info(f"Progress saved. Resume with --checkpoint={checkpoint_file}")
                raise
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)

            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failures = 0
                logger.info("Circuit breaker CLOSED")

            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"Circuit breaker OPEN after {self.failures} failures")

            raise

# Usage
api_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

try:
    result = api_breaker.call(make_api_request, task)
except CircuitBreakerError:
    logger.error("API is down, using cached response")
    result = get_cached_response()
```

## Incident Response

### Incident Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P0 - Critical | Service down, security breach | Immediate | Agent accessing production secrets |
| P1 - High | Major functionality impaired | < 1 hour | All agents timing out |
| P2 - Medium | Minor functionality impaired | < 4 hours | High error rate on specific tool |
| P3 - Low | Cosmetic or minor issues | < 24 hours | Slow response times |

### Incident Response Playbook

```yaml
incident_response:
  detection:
    - Monitor alerts in Slack/PagerDuty
    - Check Grafana dashboards
    - Review error logs

  initial_response:
    - Acknowledge alert
    - Assess severity
    - Page on-call engineer if P0/P1

  investigation:
    - Check recent deployments
    - Review recent agent sessions
    - Examine error logs and metrics
    - Reproduce issue if possible

  mitigation:
    - Stop affected agents
    - Roll back if caused by deployment
    - Increase rate limits if abuse detected
    - Isolate compromised resources if security issue

  resolution:
    - Apply fix
    - Verify fix in staging
    - Deploy to production
    - Monitor for regression

  post_incident:
    - Write incident report
    - Identify root cause
    - Create action items
    - Update runbooks
```

### Emergency Procedures

```bash
#!/bin/bash
# emergency-stop.sh

# Stop all running agents
echo "Stopping all agent sessions..."
docker ps -q --filter "label=openclaw.agent" | xargs -r docker stop

# Block new agent starts
echo "Disabling agent gateway..."
systemctl stop openclaw

# Rotate compromised credentials
echo "Rotating credentials..."
./rotate-all-credentials.sh

# Send notification
echo "Emergency stop completed" | mail -s "URGENT: OpenClaw Emergency Stop" ops@example.com
```

## Monitoring Checklist

- [ ] Structured logging implemented
- [ ] Critical events logged
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] Alert routing set up (Slack, PagerDuty)
- [ ] Error handling patterns implemented
- [ ] Circuit breakers for external services
- [ ] Checkpoint/recovery for long-running tasks
- [ ] Incident response playbook documented
- [ ] Emergency procedures tested

## Next Steps

- Review [Ethical Guidelines](05-ethical-guidelines.md)
- Study [Case Studies](06-case-studies.md)
- Implement [Security Mechanisms](03-security-mechanisms.md)
