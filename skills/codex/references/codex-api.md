# Codex API Reference

## Codex CLI Command Reference

### Basic Syntax

```bash
codex [OPTIONS] <PROMPT>
```

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--approval MODE` | Approval mode: `full`, `auto`, `manual` | `auto` |
| `--model MODEL` | Model to use | `gpt-5.4` |
| `--no-tty` | Non-interactive mode | - |
| `--quiet` | Suppress output | - |
| `--version` | Show version | - |
| `--help` | Show help | - |

### Approval Modes

**`full`**
- Codex edits files and runs commands without asking
- Use for: trusted codebases, repetitive tasks
- Risk: High - can make any change

**`auto`** (default)
- Codex asks before destructive operations
- Use for: normal development work
- Risk: Medium - asks before rm, git reset, etc.

**`manual`**
- Every action requires approval
- Use for: critical/production code, learning
- Risk: Low - you control everything

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for authentication | `sk-...` |
| `CODEX_APPROVAL_MODE` | Default approval mode | `auto` |
| `CODEX_MODEL` | Default model | `gpt-5.4` |
| `CODEX_EXCLUDE` | Patterns to exclude | `node_modules,.git` |
| `CODEX_INCLUDE` | Patterns to include | `src/**` |
| `CODEX_LOG_LEVEL` | Logging verbosity | `debug` |
| `CODEX_LOG_FILE` | Log file path | `codex.log` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication error |
| 4 | Rate limit exceeded |
| 5 | Cancelled by user |
| 130 | Interrupted (Ctrl+C) |

## Response Formats

### Interactive Mode

Full TUI with side-by-side diff viewer and conversation history.

### Non-Interactive Mode (--no-tty)

Stream-style output with markers:

```
[CODEX] Thinking...
[CODEX] Editing file: src/auth.js
[CODEX] Running: npm test
[CODEX] Test passed
[CODEX] Done
```

### JSON Mode (when stdin/stdout is redirected)

```json
{
  "action": "edit",
  "file": "src/auth.js",
  "changes": 3,
  "description": "Added error handling"
}
```

## Context Window

- **gpt-5.4**: ~128K tokens
- **gpt-5.3-codex**: ~200K tokens

Codex automatically manages context by:
1. Prioritizing recently modified files
2. Including relevant imports/dependencies
3. Excluding binary and generated files

## File Handling

### Included by Default
- Source code files (*.js, *.ts, *.py, etc.)
- Configuration files (*.json, *.yaml, etc.)
- Documentation (*.md)

### Excluded by Default
- `node_modules/`, `vendor/`
- `.git/`
- Build outputs: `dist/`, `build/`
- Binary files
- Secrets: `*.pem`, `*.key`

### Custom Exclusions

```bash
export CODEX_EXCLUDE="node_modules,.git,secrets,vendor"
```

## Supported Languages

Codex works best with:
- JavaScript/TypeScript
- Python
- Go
- Rust
- Java
- C/C++
- Ruby
- PHP
- Shell scripting

## Limitations

- **File size**: Individual files >1MB may be summarized
- **Binary files**: Cannot edit images, compiled binaries
- **Network**: Cannot make external network requests (unless in sandbox)
- **Shell access**: Can run commands but sandboxed

## Safety Features

### Automatic Backups

Before editing, Codex can create backups:

```bash
export CODEX_BACKUP=true
export CODEX_BACKUP_DIR=.codex-backups
```

### Git Integration

Codex respects `.gitignore` and can work with git:
- `git diff` to see changes
- `git checkout` to revert
- `git commit` to save progress

## Performance Tips

1. **Use `--approval full`** for batch operations
2. **Exclude large directories** to reduce token usage
3. **Be specific** in prompts for faster results
4. **Use `--model gpt-5.3-codex`** for larger contexts

## Troubleshooting

### "Rate limit exceeded"
- Wait a minute and retry
- Check `openai.com/billing` for usage
- Consider upgrading plan

### "Permission denied" on file edits
- Check file permissions
- Run with appropriate user/permissions
- Use `--approval full` if you trust the changes

### "No changes made"
- Be more specific in prompt
- Include file paths in prompt
- Check that files exist and are readable
