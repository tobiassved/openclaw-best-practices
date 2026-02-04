# Appendix: OpenClaw Skills Reference

## Overview

OpenClaw skills extend agent capabilities with specialized functionality. This reference covers built-in skills and custom skill development.

## Built-in Skills

### coding-agent

**Purpose**: Run coding agents (Claude Code, Codex, OpenCode) via background process

**Usage**:
```bash
# Interactive PTY mode required
bash pty:true command:"claude 'Your task here'"

# Background mode
bash pty:true background:true command:"claude 'Build feature X'"

# Monitor progress
process action:log sessionId:XXX
```

**Security Considerations**:
- Always use `pty:true` for proper terminal handling
- Set `workdir` to restrict file access scope
- Use `--allowedTools` to limit capabilities
- Configure budget caps with `--max-budget-usd`

### canvas

**Purpose**: Visual UI for agent interactions

**Security**: Ensure canvas host is bound to localhost only

### bluebubbles

**Purpose**: iMessage integration for agent communication

**Security**: Requires careful authentication and message validation

## Creating Custom Skills

### Skill Structure

```yaml
# skills/my-skill/SKILL.md
---
name: my-skill
description: Brief description of what this skill does
metadata:
  openclaw:
    emoji: 🔧
    requires:
      bins: ["mytool"]
---

# My Skill

Detailed documentation here...
```

### Skill Security Guidelines

1. **Input Validation**: Always validate and sanitize user input
2. **Least Privilege**: Request minimal permissions needed
3. **Error Handling**: Fail safely and provide clear error messages
4. **Logging**: Log all security-relevant actions
5. **Documentation**: Clearly document security implications

### Example: Read-Only Analysis Skill

```markdown
---
name: code-analyzer
description: Analyze codebase for security issues (read-only)
metadata:
  openclaw:
    emoji: 🔍
    requires:
      bins: ["semgrep", "bandit"]
---

# Code Analyzer

This skill performs security analysis on codebases.

## Usage

```bash
bash pty:true command:"code-analyzer analyze /workspace/src"
```

## Security

- Read-only access to codebase
- No network access required
- Results logged to audit trail
- No external data transmission
```

### Skill Permission Model

```json
{
  "skill": "code-analyzer",
  "permissions": {
    "filesystem": {
      "read": ["/workspace/**"],
      "write": ["/workspace/reports/**"],
      "execute": []
    },
    "network": {
      "allowed": false
    },
    "tools": ["Read", "Grep", "Bash(semgrep:*)", "Bash(bandit:*)"]
  }
}
```

## Skill Best Practices

### 1. Single Responsibility
Each skill should do one thing well.

### 2. Composability
Skills should work well with other skills.

### 3. Idempotency
Running a skill multiple times should be safe.

### 4. Observability
Provide progress updates and clear output.

### 5. Error Recovery
Handle failures gracefully and provide recovery options.

## Testing Skills

```python
def test_skill_security():
    """Test that skill respects security boundaries."""

    # Test 1: Rejects unauthorized paths
    result = run_skill("code-analyzer", path="/etc/passwd")
    assert result.error == "Access denied"

    # Test 2: Read-only enforcement
    result = run_skill("code-analyzer", action="modify")
    assert result.error == "Write access denied"

    # Test 3: Network isolation
    result = run_skill("code-analyzer", with_network=True)
    assert result.network_calls == 0
```

## Skill Deployment Checklist

- [ ] Security review completed
- [ ] Input validation implemented
- [ ] Error handling tested
- [ ] Documentation complete
- [ ] Permission boundaries defined
- [ ] Tests passing
- [ ] Logging configured
- [ ] Monitoring added

## Additional Resources

- [OpenClaw Skills Documentation](https://openclaw.dev/docs/skills)
- [Example Skills Repository](https://github.com/openclaw/skills)
- [Skill Development Guide](https://openclaw.dev/docs/skill-development)
