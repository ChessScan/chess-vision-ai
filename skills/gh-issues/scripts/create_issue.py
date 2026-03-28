#!/usr/bin/env python3
"""Create a GitHub issue in a repository."""

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
    parser = argparse.ArgumentParser(description="Create a GitHub issue")
    parser.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", help="Issue body (markdown supported)")
    parser.add_argument("--labels", help="Comma-separated list of labels")
    parser.add_argument("--assignees", help="Comma-separated list of assignee usernames")
    parser.add_argument("--milestone", type=int, help="Milestone number")
    
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}), file=sys.stderr)
        sys.exit(1)
    
    # Build request body
    body = {
        "title": args.title
    }
    
    if args.body:
        body["body"] = args.body
    if args.labels:
        body["labels"] = [l.strip() for l in args.labels.split(",")]
    if args.assignees:
        body["assignees"] = [a.strip() for a in args.assignees.split(",")]
    if args.milestone:
        body["milestone"] = args.milestone
    
    result = github_api_request(f"/repos/{args.repo}/issues", method="POST", data=body, token=token)
    
    if result.get("error"):
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    
    # Output key info
    output = {
        "number": result.get("number"),
        "title": result.get("title"),
        "url": result.get("html_url"),
        "state": result.get("state"),
        "created_at": result.get("created_at"),
        "labels": [l["name"] for l in result.get("labels", [])],
        "assignees": [a["login"] for a in result.get("assignees", [])]
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
