# Codex Safety Guide

## Approval Mode Selection

### Choose Appropriately

| Scenario | Recommended Mode | Reason |
|----------|-----------------|--------|
| New/unfamiliar codebase | `manual` | Learn what Codex does |
| Well-tested codebase | `auto` | Balance efficiency and safety |
| Trusted, repetitive tasks | `full` | Maximum automation |
| Production hotfix | `manual` | Every action visible |
| CI/CD pipeline | `auto` | With review gates |

## Pre-Execution Checklist

Before running Codex with `--approval full`:

- [ ] Working directory is correct
- [ ] `.gitignore` includes sensitive files
- [ ] Tests exist and pass
- [ ] Backup/rollback plan ready
- [ ] No uncommitted critical changes
- [ ] Someone available to review (for production)

## Protected Operations

Codex in `auto` mode will ask before:

- Deleting files (`rm`)
- Modifying `.git` directory
- Changing file permissions (`chmod`)
- Running `git reset` or `git checkout`
- Executing shell commands with `sudo`
- Network operations outside sandbox

## Best Practices

### 1. Start with Manual Mode

```bash
# First time - see everything
codex "refactor auth" --approval manual

# After trust established
codex "refactor auth" --approval auto
```

### 2. Review Changes Before Commit

```bash
# Run Codex
codex "implement feature" --approval auto

# Review
git diff

# Test
npm test

# Commit if satisfied
git add -A && git commit -m "feat: implement ..."
```

### 3. Use Feature Branches

```bash
git checkout -b codex/feature-name

# Run Codex
codex "implement complex feature" --approval full

# Review, test, then merge
git checkout main && git merge codex/feature-name
```

### 4. Exclude Sensitive Files

Always exclude:
```
.env
.secrets
*.key
*.pem
credentials/
config/secrets.json
```

### 5. Enable Backups

```bash
export CODEX_BACKUP=true
export CODEX_BACKUP_DIR=.codex-backups
```

Creates timestamped backups before each edit.

## Dangerous Prompts

These patterns warrant extra caution:

**Risk: Data Loss**
- "Delete all test files"
- "Clean up unused code"
- "Remove old migrations"

**Risk: Security**
- "Add admin bypass"
- "Disable authentication"
- "Log all passwords"

**Risk: Breaking Changes**
- "Change database schema"
- "Update all dependencies"
- "Refactor core modules"

## Recovery

### Undo All Changes

```bash
# Git - revert all changes
git checkout -- .
git clean -fd

# If backups enabled
cp -r .codex-backups/latest/* .
```

### Review What Changed

```bash
# See all modified files
git status

# See diff
git diff

# Specific file
git diff path/to/file.js
```

### Emergency Stop

If Codex is doing something wrong:

- **Ctrl+C** - Immediate stop (current operation)
- **Ctrl+\** - Force kill (last resort)
- Close terminal - Nuclear option

## Auditing

### Enable Logging

```bash
export CODEX_LOG_LEVEL=debug
export CODEX_LOG_FILE=/var/log/codex.log
```

### Log Contents

- Timestamps
- Prompts sent
- Files modified
- Commands executed
- Tokens used
- Errors encountered

### Compliance

For regulated environments:

1. Always use `--approval manual`
2. Log everything
3. Require second review for changes
4. Document Codex usage in commit messages

## Security Considerations

### Secrets Management

❌ **Don't:** Include secrets in prompts
```bash
# BAD
codex "Use API key sk-12345 to call the service"
```

✅ **Do:** Reference environment variables
```bash
# GOOD
codex "Call the service using process.env.API_KEY"
```

### Code Review

Critical code should still get human review:

```bash
# Generate with Codex
codex "implement payment processing" --approval auto

# Review before commit
gh pr create --reviewer @security-team
```

### Network Access

Codex runs in a sandbox and cannot make arbitrary network requests.

## Team Guidelines

### Code Style

Add team conventions to `.codex/config.json`:

```json
{
  "custom_instructions": "Follow our style guide: use single quotes, 2-space indent, descriptive variable names"
}
```

### Required Reviews

For shared repositories:

```bash
# Require review for Codex changes
export CODEX_APPROVAL_MODE=manual
```

### Documentation

When Codex makes significant changes:

```bash
# In commit message
git commit -m "refactor(auth): migrate to JWT

Codex-assisted refactoring:
- Extracted auth logic to middleware
- Added token refresh
- Updated tests

Reviewed-by: @teammate"
```
