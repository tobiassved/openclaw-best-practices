# Agent Deployment Checklist

## Pre-Deployment

### Requirements
- [ ] Agent purpose clearly defined
- [ ] Success criteria documented
- [ ] Scope and boundaries established
- [ ] Escalation path defined
- [ ] Owner assigned

### Design
- [ ] Agent archetype selected (explorer/reviewer/builder/deployer)
- [ ] Tool set minimized to required capabilities
- [ ] Permission model defined
- [ ] Approval workflow configured
- [ ] Input/output validation designed

### Security
- [ ] Security audit checklist completed
- [ ] Threat model reviewed
- [ ] Sandbox configuration tested
- [ ] Credentials scoped and tested
- [ ] Rate limits configured

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Load tests pass (if applicable)
- [ ] Tested in staging environment

## Deployment

### Configuration
- [ ] Configuration file reviewed
- [ ] Secrets properly managed
- [ ] Environment variables set
- [ ] Resource limits configured
- [ ] Backup plan prepared

### Infrastructure
- [ ] Docker container built and tagged
- [ ] Container image scanned for vulnerabilities
- [ ] systemd service file created
- [ ] Health check endpoint configured
- [ ] Monitoring dashboards created

### Deployment Steps
- [ ] Deploy to staging first
- [ ] Verify staging deployment
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Verify production deployment
- [ ] Monitor for errors (30 min)

## Post-Deployment

### Verification
- [ ] Agent responds to requests
- [ ] Logging working correctly
- [ ] Metrics being collected
- [ ] Alerts firing correctly (test with dummy event)
- [ ] Backup process verified

### Documentation
- [ ] Deployment documented
- [ ] Runbooks updated
- [ ] Architecture diagrams updated
- [ ] Team notified of deployment
- [ ] User documentation published

### Monitoring
- [ ] Dashboard URL shared with team
- [ ] On-call rotation updated
- [ ] Alert channels verified
- [ ] Log aggregation confirmed
- [ ] Cost tracking enabled

## Ongoing Maintenance

### Daily
- [ ] Check error rates in dashboard
- [ ] Review security alerts
- [ ] Monitor budget usage

### Weekly
- [ ] Review agent sessions
- [ ] Check for unusual patterns
- [ ] Review approval rejection rate
- [ ] Update documentation as needed

### Monthly
- [ ] Security audit
- [ ] Performance review
- [ ] Cost optimization review
- [ ] Rotate credentials
- [ ] Update dependencies

### Quarterly
- [ ] Full security assessment
- [ ] Architecture review
- [ ] Capacity planning
- [ ] User feedback review
- [ ] Roadmap update

---

## Deployment Sign-Off

**Deployment Engineer**: ____________________
**Security Reviewer**: ____________________
**Product Owner**: ____________________
**Date**: ____________________

**Production ready**: ☐ Yes ☐ No

**Conditions** (if any):
