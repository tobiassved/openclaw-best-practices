# Security Audit Checklist

## Configuration Security

- [ ] OpenClaw runs as non-root user
- [ ] Gateway binds to localhost or private network only (not 0.0.0.0)
- [ ] Authentication enabled with strong tokens (32+ character random strings)
- [ ] TLS/SSL configured for all network communication
- [ ] Token expiration dates set and monitored
- [ ] Configuration file permissions set to 600
- [ ] Secrets not hardcoded in configuration files

## Sandbox & Isolation

- [ ] Docker sandbox enabled
- [ ] Read-only root filesystem (except tmpfs/volumes)
- [ ] All Linux capabilities dropped (--cap-drop=ALL)
- [ ] No new privileges flag set
- [ ] Resource limits configured (CPU, memory, PIDs)
- [ ] Network isolation enabled or allowlist proxy configured
- [ ] Workspace restricted to specific directory

## Permission System

- [ ] Default permission mode set to 'default' (requires approval)
- [ ] Tool allowlist configured (not wildcard '*')
- [ ] Destructive commands blocked (rm, dd, mkfs)
- [ ] Sensitive paths blocked (.ssh, .aws, .env, /etc)
- [ ] Bash command filtering enabled
- [ ] Network access restricted or denied

## Budget & Rate Limiting

- [ ] Per-session budget cap set ($5-10 recommended)
- [ ] Daily budget cap set
- [ ] Session timeout configured (30 min recommended)
- [ ] Rate limiting enabled (requests per minute/hour)
- [ ] Cost alerts configured at thresholds
- [ ] Budget monitoring dashboard created

## Credential Management

- [ ] No credentials in code or configuration
- [ ] Short-lived credentials used (< 1 hour)
- [ ] Credentials scoped to minimum required permissions
- [ ] Credential rotation schedule established
- [ ] Secrets management system in place
- [ ] Credentials never logged or exposed

## Input Validation

- [ ] User input sanitized before processing
- [ ] Prompt injection defenses implemented
- [ ] File path validation prevents directory traversal
- [ ] Command injection protections in place
- [ ] Maximum input length enforced

## Logging & Monitoring

- [ ] Audit logging enabled
- [ ] All agent actions logged
- [ ] Secrets redacted from logs
- [ ] Log aggregation configured
- [ ] Security event monitoring enabled
- [ ] SIEM integration configured
- [ ] Log retention policy defined

## Alerting

- [ ] Security violation alerts configured
- [ ] Budget exceeded alerts enabled
- [ ] Unusual activity detection in place
- [ ] Alert routing configured (email, Slack, PagerDuty)
- [ ] On-call escalation defined
- [ ] Alert response procedures documented

## Network Security

- [ ] Firewall rules restrict access to OpenClaw ports
- [ ] Reverse proxy with TLS termination configured
- [ ] VPN or Tailscale for remote access
- [ ] Network segmentation between dev/staging/prod
- [ ] Allowlist for external API access

## Testing & Validation

- [ ] Security tests written and passing
- [ ] Penetration testing performed
- [ ] Dependency vulnerability scanning enabled
- [ ] Container image scanning enabled
- [ ] Regular security audits scheduled

## Incident Response

- [ ] Incident response plan documented
- [ ] Emergency stop procedure tested
- [ ] Backup and restore procedures verified
- [ ] Contact information current
- [ ] Post-mortem template ready

## Compliance

- [ ] Data retention policy defined
- [ ] Privacy policy published
- [ ] GDPR compliance reviewed (if applicable)
- [ ] User consent mechanisms in place
- [ ] Data deletion process implemented

## Documentation

- [ ] Security policies documented
- [ ] Agent capabilities and limitations documented
- [ ] Runbooks created for common scenarios
- [ ] Architecture diagrams current
- [ ] Change log maintained

---

## Audit Sign-Off

**Auditor**: ____________________
**Date**: ____________________
**Status**: ☐ Pass ☐ Pass with conditions ☐ Fail
**Next audit date**: ____________________

**Notes**:
