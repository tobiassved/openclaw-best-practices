#!/usr/bin/env python3
"""
Secure Worker API Example

A production-ready HTTP wrapper for Claude Code with security controls.
"""
import http.server
import json
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional

# Security configuration
MAX_BUDGET_USD = 5.0
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes
RATE_LIMIT_PER_MINUTE = 10
ALLOWED_TOOLS = ['Read', 'Grep', 'Glob', 'Edit']  # Read + limited write
BLOCKED_PATHS = ['.env', '.aws', '.ssh', '/etc']

class RateLimiter:
    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()

    def is_allowed(self) -> bool:
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [t for t in self.requests if now - t < 60]

            if len(self.requests) >= self.max_requests:
                return False

            self.requests.append(now)
            return True

class SecureWorkerAPI:
    def __init__(self):
        self.rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE)
        self.active_sessions = {}
        self.session_lock = threading.Lock()

    def execute_agent(self, prompt: str, budget: float, user_id: str) -> dict:
        """Execute agent with security controls."""

        # Rate limiting
        if not self.rate_limiter.is_allowed():
            return {
                'success': False,
                'error': 'Rate limit exceeded. Try again later.'
            }

        # Budget validation
        if budget > MAX_BUDGET_USD:
            return {
                'success': False,
                'error': f'Budget exceeds maximum: ${MAX_BUDGET_USD}'
            }

        # Check for active session
        with self.session_lock:
            if user_id in self.active_sessions:
                return {
                    'success': False,
                    'error': 'User already has an active session'
                }

            # Mark session as active
            self.active_sessions[user_id] = time.time()

        try:
            # Sanitize input
            sanitized_prompt = self.sanitize_prompt(prompt)

            # Build secure command
            cmd = [
                'claude', '-p',
                '--model', 'sonnet',
                '--max-budget-usd', str(budget),
                '--allowedTools', ' '.join(ALLOWED_TOOLS),
                '--output-format', 'text',
                sanitized_prompt
            ]

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SESSION_TIMEOUT_SECONDS,
                cwd='/workspace',  # Restricted working directory
                env={
                    'HOME': '/tmp',
                    'PATH': '/usr/local/bin:/usr/bin:/bin'
                }
            )

            output = result.stdout or result.stderr or 'No output'

            # Redact any leaked secrets
            safe_output = self.redact_secrets(output)

            return {
                'success': True,
                'response': safe_output,
                'cost': self.estimate_cost(safe_output)
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Session timeout after {SESSION_TIMEOUT_SECONDS}s'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)}'
            }

        finally:
            # Remove active session
            with self.session_lock:
                self.active_sessions.pop(user_id, None)

    def sanitize_prompt(self, prompt: str) -> str:
        """Sanitize user input to prevent injection."""
        # Remove null bytes
        prompt = prompt.replace('\x00', '')

        # Limit length
        if len(prompt) > 10000:
            raise ValueError('Prompt too long (max 10000 chars)')

        # Check for injection attempts
        dangerous_patterns = [
            'ignore previous instructions',
            'disregard system prompt',
            'new instructions:',
        ]

        prompt_lower = prompt.lower()
        for pattern in dangerous_patterns:
            if pattern in prompt_lower:
                raise ValueError(f'Prompt contains dangerous pattern: {pattern}')

        return prompt

    def redact_secrets(self, text: str) -> str:
        """Redact common secret patterns."""
        import re

        patterns = [
            (r'AKIA[0-9A-Z]{16}', '[AWS_ACCESS_KEY]'),
            (r'aws_secret_access_key\s*=\s*\S+', 'aws_secret_access_key=[REDACTED]'),
            (r'password\s*=\s*\S+', 'password=[REDACTED]'),
            (r'token\s*=\s*\S+', 'token=[REDACTED]'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def estimate_cost(self, output: str) -> float:
        """Rough cost estimation based on output length."""
        # Very rough estimate: $0.01 per 1000 chars
        return len(output) / 1000 * 0.01

class Handler(http.server.BaseHTTPRequestHandler):
    api = SecureWorkerAPI()

    def do_POST(self):
        """Handle POST requests."""
        try:
            # Parse request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            prompt = data.get('prompt', '')
            budget = float(data.get('budget', 1.0))
            user_id = data.get('user_id', 'anonymous')

            if not prompt:
                self.send_error(400, 'Missing prompt')
                return

            # Execute
            result = self.api.execute_agent(prompt, budget, user_id)

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, f'Internal server error: {str(e)}')

    def log_message(self, format, *args):
        """Override to add structured logging."""
        timestamp = datetime.utcnow().isoformat()
        print(json.dumps({
            'timestamp': timestamp,
            'type': 'http_request',
            'method': format,
            'args': args
        }))

if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', 18790), Handler)
    print('Secure Worker API listening on http://127.0.0.1:18790')
    server.serve_forever()
