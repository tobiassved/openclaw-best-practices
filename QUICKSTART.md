# Quick Start Guide

Get started with secure OpenClaw deployment in 15 minutes.

## Prerequisites

- Linux server (Ubuntu 22.04+ recommended)
- Docker installed
- Non-root user account
- Basic understanding of command line

## Step 1: Install OpenClaw

```bash
# Create dedicated user
sudo useradd -r -m -s /bin/bash openclaw
sudo usermod -aG docker openclaw

# Switch to openclaw user
sudo -u openclaw bash
cd ~

# Install OpenClaw (adjust for your installation method)
npm install -g openclaw
```

## Step 2: Configure Securely

```bash
# Generate strong tokens
TOKEN_ADMIN=$(openssl rand -base64 32)
TOKEN_AGENT=$(openssl rand -base64 32)

# Create config directory
mkdir -p ~/.openclaw
chmod 700 ~/.openclaw

# Copy template configuration
cp examples/openclaw-config-template.json ~/.openclaw/openclaw.json

# Replace tokens (do this manually or with sed)
sed -i "s/REPLACE_WITH_STRONG_TOKEN/$TOKEN_ADMIN/" ~/.openclaw/openclaw.json

# Set restrictive permissions
chmod 600 ~/.openclaw/openclaw.json

# Save tokens securely
echo "Admin token: $TOKEN_ADMIN" > ~/tokens.txt
echo "Agent token: $TOKEN_AGENT" >> ~/tokens.txt
chmod 600 ~/tokens.txt
```

## Step 3: Set Up Sandbox

```bash
# Build sandbox container
cd examples
docker build -f Dockerfile.agent-sandbox -t openclaw/sandbox:latest .

# Test sandbox
docker run --rm \
  --read-only \
  --network=none \
  --cap-drop=ALL \
  openclaw/sandbox:latest \
  echo "Sandbox working!"
```

## Step 4: Start Gateway

```bash
# Start OpenClaw gateway
openclaw gateway start

# Verify it's running
curl http://localhost:18789/health
```

## Step 5: Deploy with Docker Compose (Optional)

```bash
# Copy docker-compose.yml
cp examples/docker-compose.yml ~/

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f openclaw-gateway
```

## Step 6: Set Up Monitoring

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Access Grafana
open http://localhost:3000
# Default: admin / changeme (change this!)

# Import OpenClaw dashboard
# Dashboard ID: (create and share in docs/)
```

## Step 7: Test Agent Execution

```bash
# Simple read-only test
curl -X POST http://localhost:18790/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List all files in the current directory",
    "budget": 0.10,
    "user_id": "test-user"
  }'

# Check logs
tail -f /var/log/openclaw/audit.log
```

## Step 8: Security Hardening

```bash
# Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow from 192.168.1.0/24 to any port 18789

# Set up systemd service
sudo cp examples/systemd/openclaw.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Verify service status
sudo systemctl status openclaw
```

## Step 9: Run Security Audit

```bash
# Use the security audit checklist
cat checklists/security-audit.md

# Test sandbox isolation
docker run --rm openclaw/sandbox:latest curl google.com
# Should fail: "Could not resolve host"

# Test file access restrictions
docker run --rm -v /etc:/host-etc:ro openclaw/sandbox:latest cat /host-etc/passwd
# Should fail: read-only filesystem
```

## Step 10: Set Up Monitoring Alerts

```bash
# Configure Prometheus alert rules
cp examples/alert-rules.yml /etc/prometheus/rules/

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload

# Test alerts (trigger a condition and verify)
```

## Common Issues

### Gateway won't start
- Check port 18789 isn't already in use: `netstat -tulpn | grep 18789`
- Verify config file syntax: `openclaw config validate`
- Check logs: `journalctl -u openclaw -f`

### Agent timeout
- Increase timeout in config: `sessionTimeoutSeconds: 3600`
- Check resource limits: `docker stats`
- Review logs for stuck operations

### High costs
- Verify budget caps are set
- Check rate limiting configuration
- Review agent prompts for efficiency

### Permission denied
- Check file ownership: `ls -la ~/.openclaw/`
- Verify Docker socket access: `groups $USER | grep docker`
- Review sandbox volume mounts

## Next Steps

- Read [OpenClaw Configuration Guide](docs/01-openclaw-config.md)
- Review [Security Mechanisms](docs/03-security-mechanisms.md)
- Set up [Monitoring](docs/04-monitoring.md)
- Study [Case Studies](docs/06-case-studies.md)

## Getting Help

- OpenClaw Docs: https://openclaw.dev/docs
- GitHub Issues: https://github.com/tbsp/openclaw/issues
- Discord Community: https://discord.gg/openclaw

## Security Checklist

After completing setup, verify:

- [ ] Gateway binds to localhost only
- [ ] Strong authentication tokens set
- [ ] Sandbox isolation working
- [ ] Budget caps configured
- [ ] Rate limiting enabled
- [ ] Monitoring and alerts active
- [ ] Audit logging enabled
- [ ] Firewall rules in place
- [ ] systemd service hardened
- [ ] Backup system configured

**You're now ready to deploy AI agents securely with OpenClaw!**
