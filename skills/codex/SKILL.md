---
name: codex
description: OpenAI Codex CLI coding agent integration. Use when the user wants to delegate complex coding tasks to Codex, perform code reviews, refactor large codebases, debug issues, run tests, or execute multi-step development workflows. Triggers on phrases like "use codex to...", "have codex...", "codex, ..." or any request to perform coding tasks that would benefit from Codex's autonomous capabilities. Supports both interactive prompts and structured task execution with safety controls.
---

# Codex Coding Agent

Delegate complex software engineering tasks to OpenAI Codex. Codex can read codebases, edit files, run commands, and execute multi-step workflows autonomously.

## Quick Start

**Simple task execution:**
```bash
codex "refactor the auth module to use async/await"
```

**With full control:**
```bash
python3 scripts/codex_exec.py --task "implement user authentication" --approval full --workdir ./project
```

## Modes of Operation

### 1. Direct CLI (Simple Tasks)

For straightforward tasks where you want Codex to run immediately:

```bash
codex "add error handling to all API endpoints"
```

**Flags:**
- `--approval full|auto|manual` - Control what Codex can do without asking
- `--model gpt-5.4|gpt-5.3-codex` - Choose the model
- `--no-tty` - Non-interactive mode (for scripts)

### 2. Structured Execution (Complex Tasks)

For complex tasks requiring setup, safety controls, or specific context:

```bash
python3 scripts/codex_exec.py \
  --task "Migrate from Express to Fastify" \
  --approval full \
  --workdir ./my-app \
  --exclude "node_modules,build,dist" \
  --model gpt-5.4
```

### 3. Code Review Mode

Have Codex review code before committing:

```bash
python3 scripts/codex_review.py \
  --workdir . \
  --files "src/**/*.ts" \
  --focus "security,performance" \
  --output review.json
```

### 4. Batch Processing

Process multiple tasks in parallel:

```bash
python3 scripts/codex_batch.py \
  --tasks tasks.json \
  --max-parallel 3 \
  --output results/
```

## Approval Modes

Control what Codex can do autonomously:

| Mode | Description | Use When |
|------|-------------|----------|
| `full` | Codex can edit files and run commands freely | Trusted codebase, well-tested |
| `auto` | Codex can make changes, asks before destructive operations | Normal development |
| `manual` | Every action requires approval | Critical/production code |

**Set via environment:**
```bash
export CODEX_APPROVAL_MODE=full
```

## Authentication

Codex requires authentication. Choose one method:

**1. ChatGPT Account (Recommended)**
- Run `codex` and sign in with ChatGPT
- Uses your Plus/Pro/Team/Education/Enterprise plan

**2. API Key**
```bash
export OPENAI_API_KEY="sk-..."
```

## Common Workflows

### Refactoring

```bash
python3 scripts/codex_exec.py \
  --task "Refactor all callback-based functions to use async/await" \
  --approval auto \
  --include "src/**/*.js" \
  --exclude "node_modules"
```

### Debugging

```bash
python3 scripts/codex_debug.py \
  --error "TypeError: Cannot read property 'map' of undefined" \
  --stacktrace "at parseUsers (src/utils.js:42:15)" \
  --files "src/utils.js,src/api.js"
```

### Test Generation

```bash
python3 scripts/codex_exec.py \
  --task "Write comprehensive unit tests for the UserService class" \
  --approval full \
  --workdir . \
  --output-tests test/
```

### Documentation

```bash
python3 scripts/codex_exec.py \
  --task "Generate API documentation from the Express routes" \
  --approval full \
  --output docs/API.md
```

## Subagents

For complex multi-part tasks, Codex can spawn subagents:

```bash
python3 scripts/codex_subagent.py \
  --task "Analyze the codebase and create a migration plan" \
  --subagents 3 \
  --mode parallel
```

See `references/subagents.md` for advanced patterns.

## Safety Controls

### Excluded Paths

Always exclude sensitive directories:
```bash
--exclude "node_modules,.git,secrets,*.key,*.pem"
```

### File Backups

Enable automatic backups before edits:
```bash
export CODEX_BACKUP=true
export CODEX_BACKUP_DIR=.codex-backups
```

### Audit Logging

Enable logging of all Codex actions:
```bash
export CODEX_LOG_LEVEL=debug
export CODEX_LOG_FILE=codex.log
```

## Error Handling

All scripts return structured JSON:

```json
{
  "success": true,
  "task": "refactor auth module",
  "files_modified": ["src/auth.js", "src/middleware.js"],
  "commands_run": ["npm test"],
  "duration_seconds": 45.2,
  "tokens_used": 1247
}
```

On failure:
```json
{
  "success": false,
  "error": "Test suite failed after changes",
  "details": "...",
  "files_modified": ["src/auth.js"]
}
```

## Advanced Configuration

See `references/configuration.md` for:
- Model selection (gpt-5.4, gpt-5.3-codex)
- Custom system prompts
- MCP (Model Context Protocol) tools
- CI/CD integration patterns

## Reference

- **API Details:** `references/codex-api.md`
- **Subagent Patterns:** `references/subagents.md`
- **Configuration:** `references/configuration.md`
- **Safety Guide:** `references/safety.md`
