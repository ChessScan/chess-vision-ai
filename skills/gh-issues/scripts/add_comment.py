#!/usr/bin/env python3
"""Add a comment to a GitHub issue."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


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
    parser = argparse.ArgumentParser(description="Add a comment to a GitHub issue")
    parser.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    parser.add_argument("--issue", required=True, type=int, help="Issue number")
    parser.add_argument("--body", required=True, help="Comment body (markdown supported)")
    
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}), file=sys.stderr)
        sys.exit(1)
    
    if not args.body.strip():
        print(json.dumps({"error": "Comment body cannot be empty"}), file=sys.stderr)
        sys.exit(1)
    
    body = {"body": args.body}
    
    result = github_api_request(
        f"/repos/{args.repo}/issues/{args.issue}/comments",
        method="POST",
        data=body,
        token=token
    )
    
    if result.get("error"):
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    
    output = {
        "id": result.get("id"),
        "url": result.get("html_url"),
        "issue_url": result.get("issue_url"),
        "created_at": result.get("created_at"),
        "user": result.get("user", {}).get("login")
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
