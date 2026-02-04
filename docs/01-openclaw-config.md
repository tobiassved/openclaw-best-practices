# OpenClaw Configuration Best Practices

## Table of Contents

- [Installation](#installation)
- [Security-First Configuration](#security-first-configuration)
- [Environment Isolation](#environment-isolation)
- [Gateway Configuration](#gateway-configuration)
- [Authentication & Authorization](#authentication--authorization)
- [Network Security](#network-security)
- [Production Deployment](#production-deployment)

## Installation

### Prerequisites

Before installing OpenClaw, ensure your environment meets these security requirements:

```bash
# 1. Dedicated user account (never run as root)
sudo useradd -r -m -s /bin/bash openclaw
sudo usermod -aG docker openclaw  # Only if Docker is required

# 2. Secure home directory
sudo chmod 750 /home/openclaw
sudo chown openclaw:openclaw /home/openclaw

# 3. Install OpenClaw as the dedicated user
sudo -u openclaw bash
cd ~
npm install -g openclaw  # Or follow official installation method
```

### Post-Installation Hardening

```bash
# Set restrictive permissions on config directory
chmod 700 ~/.openclaw
chmod 600 ~/.openclaw/openclaw.json

# Verify installation integrity
openclaw doctor

# Test in sandbox mode first
openclaw --help
```

## Security-First Configuration

### Minimal Configuration Template

Create `~/.openclaw/openclaw.json` with minimal required settings:

```json
{
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1",
    "auth": {
      "enabled": true,
      "tokens": []
    }
  },
  "agents": {
    "defaultPermissionMode": "default",
    "sandboxEnabled": true,
    "maxBudgetUsd": 5.0
  },
  "logging": {
    "level": "info",
    "auditLog": "/var/log/openclaw/audit.log"
  }
}
```

### Critical Security Settings

#### 1. Gateway Binding

**❌ NEVER bind to 0.0.0.0 in production:**

```json
{
  "gateway": {
    "bind": "0.0.0.0"  // ❌ Exposes to entire network
  }
}
```

**✅ Bind to localhost or specific interface:**

```json
{
  "gateway": {
    "bind": "127.0.0.1"  // ✅ Local only
  }
}
```

**For remote access, use SSH tunneling:**

```bash
# On client machine
ssh -L 18789:localhost:18789 user@openclaw-server

# Access via localhost:18789
```

#### 2. Authentication

**Always enable authentication for gateway access:**

```json
{
  "gateway": {
    "auth": {
      "enabled": true,
      "tokens": [
        {
          "name": "ulla-bella",
          "token": "strong-random-token-here",
          "permissions": ["chat", "sessions:read"],
          "expiresAt": "2026-12-31T23:59:59Z"
        }
      ]
    }
  }
}
```

**Generate strong tokens:**

```bash
# Linux/macOS
openssl rand -base64 32

# Or use uuidgen
uuidgen
```

#### 3. Permission Modes

Configure default permission behavior:

```json
{
  "agents": {
    "defaultPermissionMode": "default",  // Require approval for writes
    "dangerouslySkipPermissions": false  // NEVER set to true in production
  }
}
```

**Permission modes explained:**

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Prompt for approval on write operations | Production (recommended) |
| `acceptEdits` | Auto-approve file edits, prompt for bash | Development |
| `dontAsk` | Auto-approve everything | Testing only |
| `bypassPermissions` | Skip all checks | **NEVER in production** |

#### 4. Budget Controls

Prevent runaway costs:

```json
{
  "agents": {
    "maxBudgetUsd": 5.0,          // Per-session limit
    "dailyBudgetUsd": 50.0,       // Daily aggregate limit
    "budgetAlertThreshold": 0.8   // Alert at 80% usage
  }
}
```

#### 5. Tool Restrictions

Limit available tools by default:

```json
{
  "agents": {
    "defaultAllowedTools": [
      "Read",
      "Grep",
      "Glob"
    ],
    "disallowedTools": [
      "Bash(rm:*)",      // Block destructive commands
      "Bash(curl:*)",    // Block network access
      "Write(/etc/*)"    // Block system file writes
    ]
  }
}
```

## Environment Isolation

### Docker Sandbox Configuration

**Best practice: Run agents in Docker containers**

```json
{
  "sandbox": {
    "enabled": true,
    "provider": "docker",
    "docker": {
      "image": "openclaw/sandbox:latest",
      "cpuLimit": "2",
      "memoryLimit": "2g",
      "networkMode": "none",
      "readOnlyRootFilesystem": true,
      "securityOpt": ["no-new-privileges"],
      "capDrop": ["ALL"],
      "volumes": [
        {
          "host": "/workspace",
          "container": "/workspace",
          "readOnly": false
        }
      ]
    }
  }
}
```

### Workspace Isolation

**Restrict agent file system access:**

```json
{
  "workspace": {
    "root": "/home/openclaw/workspace",
    "allowParentAccess": false,
    "excludePaths": [
      "~/.ssh",
      "~/.aws",
      "~/.openclaw/openclaw.json",
      "/etc",
      "/var"
    ]
  }
}
```

### Environment Variables

**Never expose sensitive credentials:**

```json
{
  "sandbox": {
    "docker": {
      "env": {
        // ❌ NEVER do this
        "AWS_SECRET_ACCESS_KEY": "actual-secret-key",

        // ✅ Use credential helpers instead
        "AWS_SHARED_CREDENTIALS_FILE": "/workspace/.aws/credentials"
      }
    }
  }
}
```

**Use secrets management:**

```bash
# Mount read-only credentials
docker run \
  -v /path/to/credentials:/workspace/.credentials:ro \
  -e CREDENTIAL_PATH=/workspace/.credentials \
  openclaw/sandbox
```

## Gateway Configuration

### WebSocket Gateway

The gateway is OpenClaw's control plane. Secure it carefully:

```json
{
  "gateway": {
    "port": 18789,
    "bind": "127.0.0.1",
    "tls": {
      "enabled": true,
      "cert": "/etc/openclaw/tls/server.crt",
      "key": "/etc/openclaw/tls/server.key"
    },
    "cors": {
      "enabled": false  // Disable unless needed
    },
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 60,
      "burstSize": 10
    }
  }
}
```

### Legacy Bridge (Deprecated)

**Note:** The TCP bridge (port 18790) is deprecated. Use the WebSocket gateway instead.

If you must use the bridge:

```json
{
  "bridge": {
    "enabled": false,  // Keep disabled if not needed
    "port": 18790,
    "bind": "127.0.0.1",
    "tls": {
      "enabled": true
    }
  }
}
```

## Authentication & Authorization

### Token-Based Authentication

**Create scoped tokens for different use cases:**

```json
{
  "gateway": {
    "auth": {
      "tokens": [
        {
          "name": "admin",
          "token": "admin-token-here",
          "permissions": ["*"],
          "expiresAt": "2026-06-01T00:00:00Z"
        },
        {
          "name": "read-only-monitoring",
          "token": "monitoring-token-here",
          "permissions": ["sessions:read", "health:read"],
          "expiresAt": "2027-01-01T00:00:00Z"
        },
        {
          "name": "agent-executor",
          "token": "executor-token-here",
          "permissions": ["chat", "sessions:read", "sessions:write"],
          "expiresAt": "2026-12-31T23:59:59Z"
        }
      ]
    }
  }
}
```

### Permission Scopes

Available permission scopes:

| Scope | Grants Access To |
|-------|------------------|
| `chat` | Create and interact with agent sessions |
| `sessions:read` | Read session data and history |
| `sessions:write` | Modify or delete sessions |
| `config:read` | Read configuration |
| `config:write` | Modify configuration |
| `health:read` | Health check endpoints |
| `skills:*` | Execute skills |
| `*` | All permissions (admin) |

### Credential Rotation

**Rotate tokens regularly:**

```bash
#!/bin/bash
# rotate-tokens.sh

NEW_TOKEN=$(openssl rand -base64 32)
CONFIG=~/.openclaw/openclaw.json

# Update configuration
jq '.gateway.auth.tokens[0].token = "'$NEW_TOKEN'"' $CONFIG > $CONFIG.tmp
mv $CONFIG.tmp $CONFIG

# Update dependent services
echo "New token: $NEW_TOKEN"
echo "Update OPENCLAW_TOKEN in dependent services"
```

**Schedule rotation:**

```cron
# Rotate tokens monthly
0 0 1 * * /home/openclaw/scripts/rotate-tokens.sh
```

## Network Security

### Firewall Rules

**Only expose necessary ports:**

```bash
# UFW example
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change default port!)
sudo ufw allow 22022/tcp

# OpenClaw gateway - only from specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 18789

sudo ufw enable
```

### Reverse Proxy

**Use nginx or Caddy for TLS termination:**

```nginx
# /etc/nginx/sites-available/openclaw
upstream openclaw {
    server 127.0.0.1:18789;
}

server {
    listen 443 ssl http2;
    server_name openclaw.internal.example.com;

    ssl_certificate /etc/letsencrypt/live/openclaw.internal.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openclaw.internal.example.com/privkey.pem;

    # Strong TLS configuration
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=openclaw:10m rate=10r/s;
    limit_req zone=openclaw burst=20 nodelay;

    location / {
        proxy_pass http://openclaw;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Authentication
        auth_basic "OpenClaw Gateway";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

### VPN or Tailscale

**Recommended: Use private networking**

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Bind OpenClaw to Tailscale interface
# In openclaw.json:
{
  "gateway": {
    "bind": "100.x.x.x"  # Your Tailscale IP
  }
}
```

## Production Deployment

### systemd Service

**Run OpenClaw as a system service:**

```ini
# /etc/systemd/system/openclaw.service
[Unit]
Description=OpenClaw AI Agent Gateway
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=openclaw
Group=openclaw
WorkingDirectory=/home/openclaw
Environment="NODE_ENV=production"
ExecStart=/usr/local/bin/openclaw gateway start
Restart=on-failure
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/openclaw/workspace /var/log/openclaw

# Resource limits
LimitNOFILE=4096
LimitNPROC=512

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Monitor logs
journalctl -u openclaw -f
```

### Health Monitoring

**Set up health check endpoint:**

```bash
#!/bin/bash
# /usr/local/bin/openclaw-health-check.sh

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18789/health)

if [ "$RESPONSE" != "200" ]; then
    echo "OpenClaw health check failed: HTTP $RESPONSE"
    # Send alert
    exit 1
fi

echo "OpenClaw healthy"
exit 0
```

**Monitoring with Prometheus:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'openclaw'
    static_configs:
      - targets: ['localhost:18789']
    metrics_path: '/metrics'
```

### Backup and Recovery

**Backup critical data:**

```bash
#!/bin/bash
# backup-openclaw.sh

BACKUP_DIR="/backups/openclaw/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Configuration
cp -r ~/.openclaw $BACKUP_DIR/config

# Session history
cp -r ~/.claude/projects $BACKUP_DIR/sessions

# Workspace
tar czf $BACKUP_DIR/workspace.tar.gz /home/openclaw/workspace

# Encrypt backup
gpg --encrypt --recipient backup@example.com $BACKUP_DIR/*

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://openclaw-backups/$(date +%Y%m%d)
```

### Log Rotation

```
# /etc/logrotate.d/openclaw
/var/log/openclaw/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 openclaw openclaw
    sharedscripts
    postrotate
        systemctl reload openclaw > /dev/null 2>&1 || true
    endscript
}
```

## Configuration Validation

**Test configuration before applying:**

```bash
# Dry-run validation
openclaw config validate ~/.openclaw/openclaw.json

# Test in sandbox mode
openclaw --debug gateway start --test-mode

# Verify security settings
openclaw config audit --report security-audit.json
```

## Summary Checklist

- [ ] OpenClaw runs as non-root user
- [ ] Gateway binds to 127.0.0.1 or private network only
- [ ] Authentication enabled with strong tokens
- [ ] TLS configured for encrypted communication
- [ ] Docker sandbox enabled with resource limits
- [ ] Workspace isolation configured
- [ ] Budget caps set (per-session and daily)
- [ ] Tool allowlist configured
- [ ] Firewall rules in place
- [ ] systemd service configured with hardening
- [ ] Health monitoring set up
- [ ] Logs configured with rotation
- [ ] Backup system in place
- [ ] Token rotation schedule established

## Next Steps

- Review [Responsible Agent Design](02-agent-design.md)
- Implement [Security Mechanisms](03-security-mechanisms.md)
- Set up [Monitoring](04-monitoring.md)
