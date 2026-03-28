#!/usr/bin/env python3
"""Search GitHub issues across repositories."""

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
    parser = argparse.ArgumentParser(description="Search GitHub issues")
    parser.add_argument("--query", "-q", required=True, help="Search query (GitHub search syntax)")
    parser.add_argument("--repo", help="Limit to specific repo (adds 'repo:owner/name' to query)")
    parser.add_argument("--sort", choices=["comments", "reactions", "reactions-+1", "reactions--1", 
                                             "reactions-smile", "reactions-thinking_face", 
                                             "reactions-heart", "reactions-tada", "interactions", 
                                             "created", "updated"], default="updated", 
                                             help="Sort field")
    parser.add_argument("--order", choices=["asc", "desc"], default="desc", help="Sort order")
    parser.add_argument("--limit", type=int, default=30, help="Max results to return")
    
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}), file=sys.stderr)
        sys.exit(1)
    
    # Build search query
    query = args.query
    if args.repo:
        query = f"repo:{args.repo} {query}"
    
    # Ensure we're searching issues (not just any content)
    if "is:" not in query and "type:" not in query:
        query = f"is:issue {query}"
    
    # Build query parameters
    params = {
        "q": query,
        "sort": args.sort,
        "order": args.order,
        "per_page": min(args.limit, 100)
    }
    
    query_string = urllib.parse.urlencode(params)
    endpoint = f"/search/issues?{query_string}"
    
    result = github_api_request(endpoint, token=token)
    
    if result.get("error"):
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    
    items = result.get("items", [])[:args.limit]
    
    # Format output
    output = {
        "total_count": result.get("total_count"),
        "incomplete_results": result.get("incomplete_results"),
        "count": len(items),
        "issues": []
    }
    
    for issue in items:
        output["issues"].append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("html_url"),
            "state": issue.get("state"),
            "repository": issue.get("repository_url", "").split("/")[-2:] if issue.get("repository_url") else None,
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "user": issue.get("user", {}).get("login"),
            "labels": [l["name"] for l in issue.get("labels", [])],
            "comments_count": issue.get("comments"),
            "score": issue.get("score")
        })
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
