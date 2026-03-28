# Codex Configuration Guide

## Authentication Setup

### Method 1: ChatGPT Account (Recommended)

1. Run `codex` for the first time
2. Browser opens to ChatGPT login
3. Sign in with existing account (Plus/Pro/Team/Education/Enterprise)
4. Token saved locally for future use

**Benefits:**
- Uses your existing ChatGPT plan
- No API key management
- Full feature access

### Method 2: API Key

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo 'export OPENAI_API_KEY="sk-xxxxx"' >> ~/.bashrc
```

**Requirements:**
- Valid OpenAI API key
- Payment method on file
- Rate limits apply

## Configuration Files

### Global Config: `~/.codex/config.json`

```json
{
  "default_model": "gpt-5.4",
  "default_approval_mode": "auto",
  "exclude_patterns": [
    "node_modules",
    ".git",
    "dist",
    "build",
    "*.log"
  ],
  "include_patterns": [
    "src/**",
    "test/**"
  ],
  "log_level": "info",
  "backup": true,
  "backup_dir": ".codex-backups"
}
```

### Project Config: `.codex/config.json`

Project-specific settings override global:

```json
{
  "default_approval_mode": "manual",
  "exclude_patterns": [
    "generated/**",
    "vendor/**"
  ],
  "custom_instructions": "This is a TypeScript project using NestJS..."
}
```

## Model Selection

### gpt-5.4 (Default)

- **Best for:** General coding tasks
- **Context:** ~128K tokens
- **Speed:** Fast
- **Cost:** Standard

### gpt-5.3-codex

- **Best for:** Large codebases, complex refactoring
- **Context:** ~200K tokens
- **Speed:** Slower
- **Cost:** Higher
- **Use when:** Working with 50+ files or large files

## Custom System Instructions

Add context about your codebase to help Codex:

```json
{
  "custom_instructions": """
This is a Python FastAPI application.
- Use async/await for database operations
- Use Pydantic models for validation
- Tests use pytest with fixtures in conftest.py
- Database migrations use Alembic
"""
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Codex Review

on:
  pull_request:
    branches: [main]

jobs:
  codex-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Codex
        run: npm install -g @openai/codex
      
      - name: Run Codex Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CODEX_APPROVAL_MODE: manual
        run: |
          codex "Review this PR for bugs and security issues" --no-tty --approval manual
```

### GitLab CI

```yaml
codex-review:
  stage: test
  image: node:18
  before_script:
    - npm install -g @openai/codex
  script:
    - codex "Review changes" --no-tty
  variables:
    CODEX_APPROVAL_MODE: manual
```

## Advanced Features

### MCP (Model Context Protocol)

Give Codex access to external tools:

```json
{
  "mcp_servers": [
    {
      "name": "database",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/mysql"]
    }
  ]
}
```

### Subagents

Configure subagent behavior:

```json
{
  "subagents": {
    "max_parallel": 3,
    "timeout_seconds": 300,
    "approval_mode": "auto"
  }
}
```

## Environment-Specific Settings

### Development

```bash
export CODEX_APPROVAL_MODE=full
export CODEX_LOG_LEVEL=debug
```

### Staging

```bash
export CODEX_APPROVAL_MODE=auto
export CODEX_LOG_LEVEL=info
```

### Production

```bash
export CODEX_APPROVAL_MODE=manual
export CODEX_LOG_LEVEL=warn
export CODEX_BACKUP=true
```

## Tips

1. **Start restrictive** - Use `manual` approval initially, then relax
2. **Exclude generated files** - Add build outputs to exclude patterns
3. **Version control config** - Commit `.codex/config.json` to share team settings
4. **Use custom instructions** - Help Codex understand your codebase conventions
