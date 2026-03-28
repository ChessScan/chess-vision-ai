#!/usr/bin/env python3
"""List issues in a GitHub repository."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse


def github_api_request(endpoint, method="GET", data=None, token=None):
    """Make a GitHub API request."""
    url = f"https://api.github.com{endpoint}"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "gh-issues-skill/1.0"
    }
    
    if data:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode("utf-8"))
        return {"error": True, "status": e.code, "message": error_body.get("message", str(e))}
    except urllib.error.URLError as e:
        return {"error": True, "status": 0, "message": str(e.reason)}


def main():
    parser = argparse.ArgumentParser(description="List GitHub issues")
    parser.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    parser.add_argument("--state", choices=["open", "closed", "all"], default="open", help="Issue state filter")
    parser.add_argument("--labels", help="Comma-separated list of labels to filter by")
    parser.add_argument("--assignee", help="Filter by assignee username (use '*' for any, 'none' for unassigned)")
    parser.add_argument("--creator", help="Filter by creator username")
    parser.add_argument("--milestone", help="Filter by milestone number or '*' for any, 'none' for no milestone")
    parser.add_argument("--sort", choices=["created", "updated", "comments"], default="created", help="Sort field")
    parser.add_argument("--direction", choices=["asc", "desc"], default="desc", help="Sort direction")
    parser.add_argument("--limit", type=int, default=30, help="Max number of issues to return")
    
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}), file=sys.stderr)
        sys.exit(1)
    
    # Build query parameters
    params = {
        "state": args.state,
        "sort": args.sort,
        "direction": args.direction,
        "per_page": min(args.limit, 100)
    }
    
    if args.labels:
        params["labels"] = args.labels
    if args.assignee:
        params["assignee"] = args.assignee
    if args.creator:
        params["creator"] = args.creator
    if args.milestone:
        params["milestone"] = args.milestone
    
    query_string = urllib.parse.urlencode(params)
    endpoint = f"/repos/{args.repo}/issues?{query_string}"
    
    results = []
    
    while endpoint and len(results) < args.limit:
        result = github_api_request(endpoint, token=token)
        
        if result.get("error"):
            print(json.dumps(result), file=sys.stderr)
            sys.exit(1)
        
        if isinstance(result, list):
            results.extend(result[:args.limit - len(results)])
        
        # Check for Link header pagination (simplified - just one page for now)
        break
    
    # Format output
    output = []
    for issue in results:
        # Skip pull requests (they show up in issues API)
        if "pull_request" in issue:
            continue
        
        output.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("html_url"),
            "state": issue.get("state"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "user": issue.get("user", {}).get("login"),
            "labels": [l["name"] for l in issue.get("labels", [])],
            "assignees": [a["login"] for a in issue.get("assignees", [])],
            "comments": issue.get("comments"),
            "body_preview": issue.get("body", "")[:200] if issue.get("body") else None
        })
    
    print(json.dumps({"count": len(output), "issues": output}, indent=2))


if __name__ == "__main__":
    main()
