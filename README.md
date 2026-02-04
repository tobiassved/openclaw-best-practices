# OpenClaw & AI Agent Best Practices

> **A comprehensive guide to building, deploying, and operating AI agents responsibly with OpenClaw**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-blue.svg)](https://github.com/tbsp/openclaw)

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Security Model](#security-model)
- [Contributing](#contributing)

## 🎯 Overview

This repository provides battle-tested guidelines, patterns, and anti-patterns for deploying AI agents in production environments. Based on real-world experience with OpenClaw, Claude Code, Codex, and other autonomous coding agents.

**Who is this for?**
- DevOps engineers deploying AI agent infrastructure
- Developers building agent-driven workflows
- Security teams auditing AI agent deployments
- Product managers defining agent capabilities and boundaries

**What you'll learn:**
- How to configure OpenClaw securely for production use
- Design patterns for responsible agent behavior
- Security mechanisms: sandboxing, permissions, rate limiting
- Error handling, monitoring, and observability
- Ethical guidelines for autonomous agent behavior
- Real-world case studies of what can go wrong (and how to prevent it)

## 🚀 Quick Start

### Pre-flight Security Checklist

Before deploying any AI agent to production:

- [ ] Review [OpenClaw Configuration Guide](docs/01-openclaw-config.md)
- [ ] Implement [Sandbox Isolation](docs/03-security-mechanisms.md#sandboxing)
- [ ] Set up [Permission Boundaries](docs/03-security-mechanisms.md#permissions)
- [ ] Configure [Rate Limiting](docs/03-security-mechanisms.md#rate-limiting)
- [ ] Establish [Monitoring & Alerts](docs/04-monitoring.md)
- [ ] Review [Ethical Guidelines](docs/05-ethical-guidelines.md)
- [ ] Complete [Security Audit Checklist](checklists/security-audit.md)

### Threat Model

AI agents present unique security challenges:

| Threat | Impact | Mitigation |
|--------|--------|------------|
| **Command Injection** | Critical | Sandbox all bash commands, validate inputs |
| **Data Exfiltration** | High | Network isolation, audit file access |
| **Resource Exhaustion** | High | Rate limiting, budget caps, timeouts |
| **Privilege Escalation** | Critical | Drop privileges, use least-privilege containers |
| **Prompt Injection** | Medium | Input validation, system prompt hardening |
| **Unintended Actions** | High | Approval workflows, dry-run mode, audit logs |

## 📚 Documentation

### Core Guides

1. **[OpenClaw Configuration](docs/01-openclaw-config.md)**
   - Installation and setup
   - Security-first configuration
   - Environment isolation
   - Gateway and bridge protocols

2. **[Responsible Agent Design](docs/02-agent-design.md)**
   - Defining agent boundaries
   - Tool selection and scoping
   - Prompt engineering for safety
   - Approval workflows and human-in-the-loop

3. **[Security Mechanisms](docs/03-security-mechanisms.md)**
   - Docker sandboxing
   - Permission models
   - Rate limiting and budget controls
   - Network isolation
   - Credential management

4. **[Monitoring & Error Handling](docs/04-monitoring.md)**
   - Observability patterns
   - Error handling strategies
   - Logging and audit trails
   - Alerting and incident response

5. **[Ethical Guidelines](docs/05-ethical-guidelines.md)**
   - Transparency and disclosure
   - User consent and agency
   - Data privacy and retention
   - Bias and fairness considerations

6. **[Case Studies](docs/06-case-studies.md)**
   - Real incidents and lessons learned
   - Common failure modes
   - Post-mortems and prevention strategies

### Additional Resources

- [Security Audit Checklist](checklists/security-audit.md)
- [Agent Deployment Checklist](checklists/deployment.md)
- [Code Examples](examples/)
- [OpenClaw Skills Reference](docs/appendix-skills.md)

## 🔐 Security Model

### Defense in Depth

OpenClaw agent security relies on multiple layers:

```
┌─────────────────────────────────────────┐
│   API Rate Limiting & Budget Caps       │  ← Cost & abuse protection
├─────────────────────────────────────────┤
│   Permission System & Approval Flows    │  ← User consent & control
├─────────────────────────────────────────┤
│   Tool Allowlists & Input Validation    │  ← Capability restrictions
├─────────────────────────────────────────┤
│   Docker Sandbox / Process Isolation    │  ← Execution containment
├─────────────────────────────────────────┤
│   Network Policies & Firewall Rules     │  ← Communication boundaries
├─────────────────────────────────────────┤
│   Audit Logging & Monitoring            │  ← Detection & response
└─────────────────────────────────────────┘
```

### Principle of Least Privilege

**Never grant agents more access than absolutely required:**

- Use `allowedTools` to restrict available capabilities
- Run agents in unprivileged containers
- Use separate credentials with minimal scopes
- Implement time-based access controls
- Audit all privileged operations

### Fail-Safe Defaults

**Design systems to fail safely:**

- Default to requiring approval (not bypassing)
- Timeout long-running operations
- Reject ambiguous or dangerous commands
- Log all failures for review
- Preserve state before destructive actions

## 🛠️ Examples

### Secure Worker API Configuration

```python
# examples/secure-worker-api.py
import http.server
import subprocess
import json

ALLOWED_TOOLS = ['Read', 'Grep', 'Glob']  # Read-only tools
MAX_BUDGET = 0.50  # Cost cap per request
TIMEOUT = 300  # 5 minute timeout

def run_agent(prompt):
    cmd = [
        'claude', '-p',
        '--max-budget-usd', str(MAX_BUDGET),
        '--allowedTools', ' '.join(ALLOWED_TOOLS),
        '--dangerously-skip-permissions',  # Only in isolated sandbox!
        prompt
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        cwd='/workspace',  # Restricted working directory
        env={'HOME': '/tmp'}  # Minimal environment
    )
    return result.stdout
```

See [examples/](examples/) for more patterns.

## 🏗️ Architecture Patterns

### Pattern 1: Gatekeeper Agent

Use a supervisory agent to review and approve actions:

```
User Request → Orchestrator Agent → [Approval Check] → Worker Agent → Execution
```

### Pattern 2: Read-Only Exploration

Separate read and write permissions across agent stages:

```
Phase 1: Exploration Agent (Read-only tools) → Analysis
Phase 2: Human Review → Approval
Phase 3: Execution Agent (Write tools) → Changes
```

### Pattern 3: Sandboxed Validation

Test changes in isolation before applying to production:

```
Agent → Sandbox Environment → Run Tests → [Pass] → Apply to Production
```

## 📊 Monitoring Essentials

### Key Metrics

- **API Cost**: Track spending per agent, session, and user
- **Tool Usage**: Monitor which tools are invoked and how often
- **Error Rates**: Alert on elevated failure rates
- **Execution Time**: Detect hanging or runaway processes
- **Permission Denials**: Investigate blocked operations

### Alert Thresholds

```yaml
alerts:
  - name: high_api_cost
    threshold: 5 USD/hour
    action: page_on_call

  - name: elevated_bash_usage
    threshold: 50 commands/session
    action: notify_security_team

  - name: permission_bypass_attempt
    threshold: 1 occurrence
    action: terminate_session
```

## ⚖️ Ethical Considerations

### Transparency

**Users must know when they're interacting with an AI agent:**

- Clearly label agent-generated content
- Disclose agent capabilities and limitations
- Provide opt-out mechanisms
- Document data retention policies

### Accountability

**Establish clear ownership and responsibility:**

- Human oversight for high-impact decisions
- Audit trails for all agent actions
- Rollback procedures for mistakes
- Incident response plans

### Bias & Fairness

**Agents inherit biases from training data:**

- Test for bias in decision-making
- Provide mechanisms for feedback and correction
- Document known limitations
- Regular bias audits

## 🧪 Testing & Validation

### Pre-Deployment Checklist

- [ ] Unit tests for permission boundaries
- [ ] Integration tests with real agent sessions
- [ ] Penetration testing (command injection, etc.)
- [ ] Load testing (rate limits, resource exhaustion)
- [ ] Chaos engineering (network failures, timeouts)
- [ ] Red team review of security controls

### Continuous Validation

- Automated security scans on configuration changes
- Regular credential rotation
- Dependency vulnerability scanning
- Agent behavior audits

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

**Areas where we need help:**
- Additional case studies and post-mortems
- Security patterns for specific deployment scenarios
- Tool-specific hardening guides
- Translations to other languages

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- OpenClaw project and community
- Anthropic for Claude Code
- OpenAI for Codex
- Security researchers who've shared their findings

## 📞 Contact

- **Security Issues**: security@[your-domain] (private disclosure)
- **General Questions**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**⚠️ Important Disclaimer**

AI agents are powerful tools that require careful deployment. This guide provides recommendations based on current best practices, but security is an evolving field. Always perform your own security assessment before deploying agents in production environments.

**No warranty is provided. Use at your own risk.**
