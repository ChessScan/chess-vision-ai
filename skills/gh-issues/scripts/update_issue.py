#!/usr/bin/env python3
"""Update a GitHub issue (title, body, labels, assignees, state, milestone)."""

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
    parser = argparse.ArgumentParser(description="Update a GitHub issue")
    parser.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    parser.add_argument("--issue", required=True, type=int, help="Issue number")
    parser.add_argument("--title", help="New title")
    parser.add_argument("--body", help="New body (markdown supported)")
    parser.add_argument("--labels", help="Comma-separated list of labels (replaces existing)")
    parser.add_argument("--add-labels", help="Comma-separated list of labels to add")
    parser.add_argument("--remove-labels", help="Comma-separated list of labels to remove")
    parser.add_argument("--assignees", help="Comma-separated list of assignee usernames (replaces existing)")
    parser.add_argument("--add-assignees", help="Comma-separated list of assignees to add")
    parser.add_argument("--remove-assignees", help="Comma-separated list of assignees to remove")
    parser.add_argument("--milestone", type=int, help="Milestone number (0 to remove)")
    parser.add_argument("--state", choices=["open", "closed"], help="New state")
    
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}), file=sys.stderr)
        sys.exit(1)
    
    # Build request body - only include changed fields
    body = {}
    
    if args.title is not None:
        body["title"] = args.title
    if args.body is not None:
        body["body"] = args.body
    if args.state is not None:
        body["state"] = args.state
    if args.milestone is not None:
        body["milestone"] = args.milestone if args.milestone > 0 else None
    if args.labels is not None:
        body["labels"] = [l.strip() for l in args.labels.split(",")] if args.labels else []
    if args.assignees is not None:
        body["assignees"] = [a.strip() for a in args.assignees.split(",")] if args.assignees else []
    
    if not body:
        print(json.dumps({"error": "No fields to update"}), file=sys.stderr)
        sys.exit(1)
    
    result = github_api_request(f"/repos/{args.repo}/issues/{args.issue}", method="PATCH", data=body, token=token)
    
    if result.get("error"):
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    
    # Handle label modifications separately if using add/remove
    if args.add_labels:
        for label in args.add_labels.split(","):
            github_api_request(
                f"/repos/{args.repo}/issues/{args.issue}/labels",
                method="POST",
                data={"labels": [label.strip()]},
                token=token
            )
    
    if args.remove_labels:
        for label in args.remove_labels.split(","):
            github_api_request(
                f"/repos/{args.repo}/issues/{args.issue}/labels/{label.strip()}",
                method="DELETE",
                token=token
            )
    
    # Handle assignee modifications separately
    if args.add_assignees:
        github_api_request(
            f"/repos/{args.repo}/issues/{args.issue}/assignees",
            method="POST",
            data={"assignees": [a.strip() for a in args.add_assignees.split(",")]},
            token=token
        )
    
    if args.remove_assignees:
        github_api_request(
            f"/repos/{args.repo}/issues/{args.issue}/assignees",
            method="DELETE",
            data={"assignees": [a.strip() for a in args.remove_assignees.split(",")]},
            token=token
        )
    
    # Refresh to get final state
    result = github_api_request(f"/repos/{args.repo}/issues/{args.issue}", token=token)
    
    output = {
        "number": result.get("number"),
        "title": result.get("title"),
        "url": result.get("html_url"),
        "state": result.get("state"),
        "updated_at": result.get("updated_at"),
        "labels": [l["name"] for l in result.get("labels", [])],
        "assignees": [a["login"] for a in result.get("assignees", [])]
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
