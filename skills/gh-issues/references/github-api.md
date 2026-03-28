# GitHub Issues API Reference

## Authentication

All requests require a GitHub Personal Access Token (PAT) with appropriate scopes.

**Required scopes:**
- `public_repo` - for public repositories
- `repo` - for private repositories

**Token Header:**
```
Authorization: Bearer ghp_xxxxxxxxxxxx
```

## Rate Limits

| Type | Limit | Window |
|------|-------|--------|
| Authenticated | 5,000 | per hour |
| Unauthenticated | 60 | per hour |

**Check rate limit:**
```bash
curl -H "Authorization: Bearer TOKEN" https://api.github.com/rate_limit
```

## Endpoints

### Issues

**List repository issues**
```
GET /repos/{owner}/{repo}/issues
```

Query parameters:
- `state`: open, closed, all
- `labels`: comma-separated list
- `assignee`: username, `*`, `none`
- `creator`: username
- `milestone`: number, `*`, `none`
- `sort`: created, updated, comments
- `direction`: asc, desc
- `per_page`: 1-100
- `page`: page number

**Get single issue**
```
GET /repos/{owner}/{repo}/issues/{issue_number}
```

**Create issue**
```
POST /repos/{owner}/{repo}/issues
```

Request body:
```json
{
  "title": "string (required)",
  "body": "string (markdown supported)",
  "assignees": ["username1", "username2"],
  "labels": ["label1", "label2"],
  "milestone": 1
}
```

**Update issue**
```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

Same body as create, plus `state`: "open" or "closed"

### Comments

**List issue comments**
```
GET /repos/{owner}/{repo}/issues/{issue_number}/comments
```

**Create comment**
```
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
```

```json
{
  "body": "Comment text (markdown supported)"
}
```

**Update comment**
```
PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}
```

**Delete comment**
```
DELETE /repos/{owner}/{repo}/issues/comments/{comment_id}
```

### Labels

**List labels**
```
GET /repos/{owner}/{repo}/labels
```

**Add labels to issue**
```
POST /repos/{owner}/{repo}/issues/{issue_number}/labels
```

```json
{
  "labels": ["label1", "label2"]
}
```

**Remove label**
```
DELETE /repos/{owner}/{repo}/issues/{issue_number}/labels/{name}
```

### Assignees

**Add assignees**
```
POST /repos/{owner}/{repo}/issues/{issue_number}/assignees
```

```json
{
  "assignees": ["username1", "username2"]
}
```

**Remove assignees**
```
DELETE /repos/{owner}/{repo}/issues/{issue_number}/assignees
```

## Search

**Search issues**
```
GET /search/issues
```

Query parameters:
- `q`: search query (required)
- `sort`: comments, reactions, created, updated, interactions
- `order`: asc, desc
- `per_page`: 1-100

**Search query syntax:**
- `is:issue is:open` - open issues
- `repo:owner/name` - in specific repo
- `label:bug` - with label
- `no:assignee` - unassigned
- `milestone:"v1.0"` - in milestone
- `created:>2024-01-01` - created after date
- `updated:2024-01-01..2024-03-01` - updated in range
- `"exact phrase"` - exact match

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No content (success on delete) |
| 401 | Unauthorized (bad token) |
| 403 | Forbidden (rate limit, permissions) |
| 404 | Not found (repo/issue doesn't exist) |
| 410 | Gone (issue permanently deleted) |
| 422 | Validation failed |
| 422 | Validation failed |
| 500 | Server error |

## Error Response Format

```json
{
  "message": "Validation Failed",
  "errors": [
    {
      "resource": "Issue",
      "field": "title",
      "code": "missing_field"
    }
  ]
}
```

## Common Patterns

### Batch Operations

For batch label/assignee operations, use separate calls - the API doesn't support batching in a single request.

### Pagination

Link header contains pagination info:
```
Link: <https://api.github.com/repos/...?page=2>; rel="next",
      <https://api.github.com/repos/...?page=5>; rel="last"
```

`rel` values: `next`, `prev`, `first`, `last`

### Filtering Pull Requests

The issues API includes PRs. Check for `pull_request` key to filter them out when needed.
