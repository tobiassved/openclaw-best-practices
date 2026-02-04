# Security Mechanisms

## Table of Contents

- [Defense in Depth](#defense-in-depth)
- [Sandboxing](#sandboxing)
- [Permission Models](#permission-models)
- [Rate Limiting](#rate-limiting)
- [Network Isolation](#network-isolation)
- [Credential Management](#credential-management)
- [Input Validation](#input-validation)
- [Audit Logging](#audit-logging)

## Defense in Depth

Security for AI agents requires multiple overlapping layers. No single control is sufficient.

```
┌─────────────────────────────────────────────────┐
│         Input Validation & Rate Limiting        │ Layer 7: API Gateway
├─────────────────────────────────────────────────┤
│         Permission System & Approvals           │ Layer 6: Authorization
├─────────────────────────────────────────────────┤
│         Tool Allowlists & Command Filters       │ Layer 5: Capability Control
├─────────────────────────────────────────────────┤
│         Process Isolation & Resource Limits     │ Layer 4: Runtime Containment
├─────────────────────────────────────────────────┤
│         Docker/Container Sandboxing             │ Layer 3: OS Virtualization
├─────────────────────────────────────────────────┤
│         Network Policies & Firewalls            │ Layer 2: Network Segmentation
├─────────────────────────────────────────────────┤
│         Audit Logs & SIEM Integration           │ Layer 1: Detection & Response
└─────────────────────────────────────────────────┘
```

## Sandboxing

### Docker-Based Sandboxing

**Most robust isolation for agent execution:**

```dockerfile
# Dockerfile.agent-sandbox
FROM ubuntu:22.04

# Create unprivileged user
RUN useradd -m -u 1000 agent && \
    mkdir /workspace && \
    chown agent:agent /workspace

# Install minimal required tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    git \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Drop to unprivileged user
USER agent
WORKDIR /workspace

# No entrypoint - injected at runtime
```

**Launch with security constraints:**

```bash
docker run \
  --rm \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  --network=none \
  --memory=2g \
  --cpus=2 \
  --pids-limit=512 \
  -v /workspace:/workspace:rw \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  agent-sandbox:latest \
  claude -p --max-budget-usd 1.0 "Your task here"
```

**Security flags explained:**

| Flag | Purpose |
|------|---------|
| `--read-only` | Filesystem is immutable (except tmpfs and volumes) |
| `--tmpfs` | Writable temp space with size limit and noexec |
| `--security-opt=no-new-privileges` | Prevents privilege escalation |
| `--cap-drop=ALL` | Removes all Linux capabilities |
| `--network=none` | No network access |
| `--memory=2g` | Memory limit prevents DoS |
| `--cpus=2` | CPU limit prevents resource exhaustion |
| `--pids-limit=512` | Prevents fork bombs |

### gVisor for Enhanced Isolation

**Even stronger isolation with gVisor:**

```bash
# Install gVisor
curl -fsSL https://gvisor.dev/archive.key | sudo apt-key add -
sudo add-apt-repository "deb https://storage.googleapis.com/gvisor/releases release main"
sudo apt-get update && sudo apt-get install -y runsc

# Configure Docker to use runsc
sudo tee /etc/docker/daemon.json <<EOF
{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc"
    }
  }
}
EOF
sudo systemctl restart docker

# Run with gVisor
docker run --runtime=runsc --rm agent-sandbox:latest
```

### Firejail for Process Isolation

**Lightweight alternative to Docker:**

```bash
# Install Firejail
sudo apt-get install firejail

# Create Firejail profile
cat > ~/.config/firejail/claude-agent.profile <<EOF
# Disable network
net none

# Whitelist directories
whitelist /workspace
read-only /workspace/config

# Blacklist sensitive paths
blacklist ~/.ssh
blacklist ~/.aws
blacklist ~/.config/openclaw

# Drop capabilities
caps.drop all

# Resource limits
rlimit-as 2147483648  # 2GB memory
rlimit-cpu 3600       # 1 hour CPU time
rlimit-nproc 512      # Max processes

# Seccomp filter
seccomp
EOF

# Run with Firejail
firejail --profile=claude-agent claude -p "Your task"
```

## Permission Models

### Three-Tier Permission System

**1. No permissions (Read-only)**

```json
{
  "agent": "explorer",
  "permissions": "none",
  "tools": ["Read", "Grep", "Glob"]
}
```

**2. Approval required (Default)**

```json
{
  "agent": "developer",
  "permissions": "default",
  "approval_required": ["Edit", "Write", "Bash"]
}
```

**3. Trusted automation (Restricted)**

```json
{
  "agent": "ci-agent",
  "permissions": "trusted",
  "tools": ["Read", "Bash(npm test)", "Bash(git:*)"],
  "approval_required": ["Bash(git push)"]
}
```

### File System Permissions

**Granular path-based controls:**

```python
class FileSystemPermissions:
    def __init__(self):
        self.rules = [
            # Allow reading from workspace
            Rule(path="/workspace/*", operation="read", allow=True),

            # Allow writing to output directory
            Rule(path="/workspace/output/*", operation="write", allow=True),

            # Block sensitive directories
            Rule(path="/home/*/.ssh/*", operation="*", allow=False),
            Rule(path="/home/*/.aws/*", operation="*", allow=False),
            Rule(path="/etc/*", operation="*", allow=False),

            # Block writing to critical config
            Rule(path="/workspace/.git/*", operation="write", allow=False),
            Rule(path="/workspace/package.json", operation="write", allow=False),
        ]

    def check(self, path: str, operation: str) -> bool:
        """Check if operation is allowed on path."""
        for rule in self.rules:
            if rule.matches(path, operation):
                return rule.allow
        # Default deny
        return False
```

### Command-Level Permissions

**Control bash command execution:**

```python
class BashPermissions:
    ALLOWED_COMMANDS = {
        'git': ['status', 'diff', 'log', 'show'],
        'npm': ['test', 'run test'],
        'pytest': ['*'],
        'ls': ['*'],
        'cat': ['*'],
        'grep': ['*'],
    }

    BLOCKED_COMMANDS = [
        'rm',
        'dd',
        'mkfs',
        'fdisk',
        'curl',
        'wget',
        'nc',
        'nmap',
        'sudo',
        'su',
    ]

    REQUIRES_APPROVAL = [
        'git push',
        'git commit',
        'npm publish',
        'docker',
    ]

    def check(self, command: str) -> tuple[bool, str]:
        """
        Check if command is allowed.
        Returns (allowed, reason)
        """
        cmd_parts = command.split()
        if not cmd_parts:
            return False, "Empty command"

        base_cmd = cmd_parts[0]

        # Check blocklist
        if base_cmd in self.BLOCKED_COMMANDS:
            return False, f"Command '{base_cmd}' is blocked"

        # Check allowlist
        if base_cmd in self.ALLOWED_COMMANDS:
            allowed_args = self.ALLOWED_COMMANDS[base_cmd]
            if '*' in allowed_args:
                return True, "Allowed"

            # Check if subcommand is allowed
            if len(cmd_parts) > 1 and cmd_parts[1] in allowed_args:
                return True, "Allowed"

            return False, f"Subcommand not allowed: {command}"

        # Check approval required
        if any(command.startswith(pattern) for pattern in self.REQUIRES_APPROVAL):
            return True, "Requires approval"

        # Default deny
        return False, "Command not in allowlist"
```

## Rate Limiting

### API Request Rate Limiting

**Prevent abuse and control costs:**

```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
            'cost_per_hour_usd': 50.0,
            'cost_per_day_usd': 500.0,
        }
        self.counters = defaultdict(lambda: {'requests': [], 'cost': []})

    def check(self, user_id: str, cost_usd: float = 0.0) -> tuple[bool, str]:
        """Check if request is allowed under rate limits."""
        now = datetime.now()
        user = self.counters[user_id]

        # Clean old entries
        user['requests'] = [t for t in user['requests'] if now - t < timedelta(days=1)]
        user['cost'] = [(t, c) for t, c in user['cost'] if now - t < timedelta(days=1)]

        # Check request rate limits
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        requests_last_minute = sum(1 for t in user['requests'] if t > minute_ago)
        requests_last_hour = sum(1 for t in user['requests'] if t > hour_ago)
        requests_last_day = len(user['requests'])

        if requests_last_minute >= self.limits['requests_per_minute']:
            return False, f"Rate limit: {self.limits['requests_per_minute']} requests/minute"

        if requests_last_hour >= self.limits['requests_per_hour']:
            return False, f"Rate limit: {self.limits['requests_per_hour']} requests/hour"

        if requests_last_day >= self.limits['requests_per_day']:
            return False, f"Rate limit: {self.limits['requests_per_day']} requests/day"

        # Check cost limits
        cost_last_hour = sum(c for t, c in user['cost'] if t > hour_ago)
        cost_last_day = sum(c for t, c in user['cost'])

        if cost_last_hour + cost_usd > self.limits['cost_per_hour_usd']:
            return False, f"Budget limit: ${self.limits['cost_per_hour_usd']}/hour"

        if cost_last_day + cost_usd > self.limits['cost_per_day_usd']:
            return False, f"Budget limit: ${self.limits['cost_per_day_usd']}/day"

        # Record request
        user['requests'].append(now)
        if cost_usd > 0:
            user['cost'].append((now, cost_usd))

        return True, "OK"
```

### Token Bucket Algorithm

**Smooth rate limiting with burst allowance:**

```python
import time

class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        """
        rate: tokens per second
        capacity: maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume tokens. Returns True if allowed."""
        now = time.time()

        # Refill bucket based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

# Usage
limiter = TokenBucket(rate=1.0, capacity=10.0)  # 1 req/sec, burst of 10

if limiter.consume():
    execute_agent_request()
else:
    return "Rate limit exceeded. Try again later."
```

## Network Isolation

### iptables Firewall Rules

**Block agent network access:**

```bash
#!/bin/bash
# agent-firewall.sh

# Create chain for agent traffic
iptables -N AGENT_FILTER

# Block all agent outbound by default
iptables -A AGENT_FILTER -j REJECT

# Allow specific destinations (internal API)
iptables -I AGENT_FILTER -d 192.168.1.10 -p tcp --dport 443 -j ACCEPT

# Allow DNS
iptables -I AGENT_FILTER -d 8.8.8.8 -p udp --dport 53 -j ACCEPT

# Route agent container traffic through filter
iptables -A DOCKER-USER -s 172.17.0.0/16 -j AGENT_FILTER
```

### Docker Network Policies

**Isolated networks for agents:**

```bash
# Create isolated network
docker network create \
  --driver bridge \
  --subnet 172.20.0.0/16 \
  --opt "com.docker.network.bridge.enable_ip_masquerade=false" \
  agent-network

# Run agent with no external network
docker run --network agent-network agent-sandbox

# Or completely disable networking
docker run --network none agent-sandbox
```

### Allowlist-Based Network Access

**If network access is required, use an allowlist proxy:**

```python
# allowlist-proxy.py
from mitmproxy import http

ALLOWED_DOMAINS = [
    'api.internal.company.com',
    'github.com',
    'pypi.org',
]

def request(flow: http.HTTPFlow) -> None:
    """Intercept and filter requests."""
    host = flow.request.pretty_host

    if not any(host.endswith(domain) for domain in ALLOWED_DOMAINS):
        flow.response = http.Response.make(
            403,
            b"Access to this domain is not allowed",
        )
```

```bash
# Run agent with allowlist proxy
docker run \
  --network agent-network \
  -e HTTP_PROXY=http://allowlist-proxy:8080 \
  -e HTTPS_PROXY=http://allowlist-proxy:8080 \
  agent-sandbox
```

## Credential Management

### Never Embed Credentials

**❌ Bad: Hardcoded credentials**

```json
{
  "aws": {
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}
```

**✅ Good: Use secrets management**

```bash
# Use AWS IAM roles (best)
# Instance profile or ECS task role

# Or use secrets manager
aws secretsmanager get-secret-value --secret-id agent-credentials
```

### Short-Lived Credentials

**Generate temporary credentials for agents:**

```python
import boto3
from datetime import datetime, timedelta

def create_agent_credentials(duration_hours: int = 1) -> dict:
    """Create temporary AWS credentials for agent."""
    sts = boto3.client('sts')

    response = sts.assume_role(
        RoleArn='arn:aws:iam::ACCOUNT:role/AgentRole',
        RoleSessionName='agent-session',
        DurationSeconds=duration_hours * 3600,
        Policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::agent-workspace/*"
            }]
        })
    )

    return {
        'access_key': response['Credentials']['AccessKeyId'],
        'secret_key': response['Credentials']['SecretAccessKey'],
        'session_token': response['Credentials']['SessionToken'],
        'expiration': response['Credentials']['Expiration'],
    }
```

### Credential Scoping

**Minimize credential permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::agent-workspace/${agent_id}/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "192.168.1.100/32"
        },
        "DateGreaterThan": {
          "aws:CurrentTime": "2026-02-04T00:00:00Z"
        },
        "DateLessThan": {
          "aws:CurrentTime": "2026-02-04T23:59:59Z"
        }
      }
    }
  ]
}
```

## Input Validation

### Sanitize User Input

**Prevent injection attacks:**

```python
import re
import shlex
from typing import Optional

def sanitize_prompt(user_input: str) -> str:
    """Sanitize user input before passing to agent."""

    # Remove null bytes
    user_input = user_input.replace('\0', '')

    # Check length
    if len(user_input) > 10000:
        raise ValueError("Input too long")

    # Check for prompt injection attempts
    dangerous_patterns = [
        r'ignore\s+previous\s+instructions',
        r'disregard.*system\s+prompt',
        r'new\s+instructions:',
        r'jailbreak',
        r'<\s*system\s*>',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            raise SecurityError(f"Input contains dangerous pattern: {pattern}")

    return user_input

def sanitize_bash_argument(arg: str) -> str:
    """Sanitize bash command arguments."""

    # Use shlex for proper shell escaping
    return shlex.quote(arg)

def validate_file_path(path: str) -> Optional[str]:
    """Validate file path to prevent directory traversal."""

    # Resolve to absolute path
    abs_path = os.path.abspath(path)

    # Check if within allowed workspace
    if not abs_path.startswith('/workspace/'):
        raise SecurityError(f"Path outside workspace: {abs_path}")

    # Block hidden files in sensitive locations
    if '/.ssh/' in abs_path or '/.aws/' in abs_path:
        raise SecurityError(f"Access to sensitive path denied: {abs_path}")

    return abs_path
```

### Content Security Policy for Agent Output

**Sanitize agent-generated content before displaying:**

```python
import bleach

def sanitize_agent_output(output: str) -> str:
    """Sanitize HTML output from agents."""

    allowed_tags = ['p', 'br', 'strong', 'em', 'code', 'pre']
    allowed_attrs = {}

    clean = bleach.clean(
        output,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

    return clean
```

## Audit Logging

### Comprehensive Audit Trail

**Log all agent actions:**

```python
import json
import hashlib
from datetime import datetime

class AuditLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file

    def log(self, event_type: str, data: dict):
        """Log an audit event."""

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': data,
        }

        # Add integrity hash
        event['hash'] = self._compute_hash(event)

        # Write to append-only log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def _compute_hash(self, event: dict) -> str:
        """Compute hash for tamper detection."""
        # Sort keys for deterministic hashing
        canonical = json.dumps(event, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

# Usage
audit = AuditLogger('/var/log/openclaw/audit.log')

audit.log('agent_started', {
    'agent_id': 'abc-123',
    'user_id': 'user-456',
    'tools': ['Read', 'Grep'],
    'budget_usd': 1.0,
})

audit.log('tool_invoked', {
    'agent_id': 'abc-123',
    'tool': 'Bash',
    'command': 'git status',
    'approved': True,
})

audit.log('agent_completed', {
    'agent_id': 'abc-123',
    'cost_usd': 0.42,
    'duration_seconds': 120,
    'success': True,
})
```

### SIEM Integration

**Forward logs to security monitoring:**

```python
import syslog

class SyslogAuditLogger:
    def __init__(self, facility=syslog.LOG_LOCAL0):
        syslog.openlog('openclaw-agent', syslog.LOG_PID, facility)

    def log_security_event(self, severity: str, message: str, data: dict):
        """Log security event to syslog."""

        level = {
            'critical': syslog.LOG_CRIT,
            'error': syslog.LOG_ERR,
            'warning': syslog.LOG_WARNING,
            'info': syslog.LOG_INFO,
        }[severity]

        syslog.syslog(level, f"{message} | {json.dumps(data)}")

# Usage
logger = SyslogAuditLogger()

logger.log_security_event('warning', 'Agent attempted blocked command', {
    'agent_id': 'abc-123',
    'command': 'rm -rf /',
    'blocked_by': 'command_filter',
})
```

## Security Checklist

- [ ] Agents run in Docker containers with security constraints
- [ ] Read-only root filesystem (except tmpfs)
- [ ] Network isolation or allowlist-based proxy
- [ ] All capabilities dropped
- [ ] Resource limits (CPU, memory, PIDs) set
- [ ] Permission system enforced
- [ ] Command allowlist/blocklist configured
- [ ] Rate limiting enabled
- [ ] Credentials use short-lived tokens
- [ ] Input validation on all user input
- [ ] Audit logging enabled
- [ ] SIEM integration configured
- [ ] Regular security audits scheduled

## Next Steps

- Set up [Monitoring & Error Handling](04-monitoring.md)
- Review [Ethical Guidelines](05-ethical-guidelines.md)
- Study [Case Studies](06-case-studies.md)
