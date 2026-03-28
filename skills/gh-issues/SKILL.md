---
name: gh-issues
description: GitHub Issues automation and coding agent. Use when working with GitHub repositories to create, update, comment on, search, and manage issues programmatically. Also use for automated issue triage, generating issue reports, linking issues to commits/PRs, or integrating GitHub issues into development workflows. Triggers on phrases like "create a GitHub issue", "update issue", "add comment to issue", "list open issues", "search issues", or any GitHub issue-related tasks requiring API interaction.
---

# GitHub Issues Coding Agent

Automate GitHub issue workflows via the GitHub API. Create, update, search, and manage issues programmatically.

## Quick Start

All operations use scripts in `scripts/` directory. Run with proper authentication via `GITHUB_TOKEN` environment variable.

### Authentication

Set `GITHUB_TOKEN` with a personal access token (requires `repo` or `public_repo` scope):

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### Common Operations

**Create an issue:**
```bash
python3 scripts/create_issue.py --repo owner/repo --title "Bug: ..." --body "..."
```

**Update an issue:**
```bash
python3 scripts/update_issue.py --repo owner/repo --issue 123 --body "New description"
```

**Add a comment:**
```bash
python3 scripts/add_comment.py --repo owner/repo --issue 123 --body "Comment text"
```

**List open issues:**
```bash
python3 scripts/list_issues.py --repo owner/repo --state open
```

**Search issues:**
```bash
python3 scripts/search_issues.py --repo owner/repo --query "label:bug is:open"
```

## Workflow Patterns

### Creating Multiple Related Issues

When a feature needs multiple issues, batch them:

1. Create parent/tracking issue first
2. Create child issues with reference to parent
3. Add cross-reference comments linking them

### Issue Triage Workflow

1. List open issues: `list_issues.py --state open --labels needs-triage`
2. For each issue, read contents and determine action
3. Update labels/assignee: `update_issue.py --issue N --labels "bug,critical" --assignee "user"`
4. Add triage comment explaining decision

### Automated Issue Reports

Generate summaries of issue activity:
```bash
python3 scripts/issue_report.py --repo owner/repo --since 7d --format markdown
```

## API Reference

See `references/github-api.md` for complete GitHub Issues API documentation, rate limits, and error handling.

## Error Handling

All scripts exit non-zero on failure and print JSON error details to stderr. Common error codes:
- 401: Invalid or missing GITHUB_TOKEN
- 403: Rate limited or insufficient permissions
- 404: Repository or issue not found
- 422: Validation failed (bad input)

## Rate Limits

- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour

Scripts automatically check remaining rate limit and warn when < 10% remaining.
