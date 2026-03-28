#!/usr/bin/env python3
"""Have Codex review code for bugs, security, performance issues."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CODEX_PATH = os.path.expanduser("~/.local/bin/codex")


def get_codex_binary():
    """Get the path to the codex binary."""
    return CODEX_PATH if os.path.isfile(CODEX_PATH) else "codex"


def run_codex_review(workdir, files=None, focus=None):
    """Run Codex in code review mode."""
    
    # Build review prompt
    prompt = "Review this codebase for issues"
    
    if focus:
        prompt += f". Focus on: {focus}"
    
    if files:
        prompt += f"\n\nFocus on these files: {files}"
    
    prompt += """

Provide a structured review covering:
1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style and maintainability
5. Suggested fixes for critical issues

Output format:
```json
{
  "summary": "Overall assessment",
  "critical": [{"file": "...", "line": N, "issue": "...", "fix": "..."}],
  "warnings": [{"file": "...", "line": N, "issue": "...", "suggestion": "..."}],
  "suggestions": [{"file": "...", "suggestion": "..."}]
}
```"""
    
    cmd = [
        get_codex_binary(),
        "exec",
        "--full-auto",
        "-m", "gpt-5.4",
        "review"
    ]
    
    if files:
        cmd.append(f"Review these files: {files}")
    else:
        cmd.append(prompt)
    
    env = os.environ.copy()
    env["CODEX_APPROVAL_MODE"] = "manual"
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=workdir,
        env=env
    )
    
    return result


def parse_review_output(stdout):
    """Try to extract JSON review from Codex output."""
    # Look for JSON block in the output
    import re
    
    # Try to find JSON block
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', stdout, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to parse entire output as JSON
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        pass
    
    # Return raw output wrapped
    return {
        "raw_output": stdout,
        "parsed": False
    }


def main():
    parser = argparse.ArgumentParser(
        description="Have Codex review code for issues",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--workdir", "-w", default=".",
                        help="Directory containing the code to review")
    parser.add_argument("--files", "-f",
                        help="Files or patterns to review (comma-separated globs)")
    parser.add_argument("--focus",
                        help="Areas to focus on (security,performance,bugs,style)")
    parser.add_argument("--output", "-o",
                        help="Output file for review results")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output as JSON")
    
    args = parser.parse_args()
    
    # Validate workdir
    if not os.path.isdir(args.workdir):
        print(json.dumps({"error": f"Directory not found: {args.workdir}"}), file=sys.stderr)
        sys.exit(1)
    
    # Check Codex is installed
    if not os.path.isfile(CODEX_PATH):
        result = subprocess.run(["which", "codex"], capture_output=True)
        if result.returncode != 0:
            print(json.dumps({"error": "Codex not found. Install: npm i -g @openai/codex"}), file=sys.stderr)
            sys.exit(1)
    
    # Run review
    result = run_codex_review(args.workdir, args.files, args.focus)
    
    # Parse and format output
    review_data = parse_review_output(result.stdout)
    
    output = {
        "success": result.returncode == 0,
        "workdir": os.path.abspath(args.workdir),
        "files_reviewed": args.files,
        "focus_areas": args.focus,
        "review": review_data,
        "raw_stdout": result.stdout if not review_data.get("parsed", True) else None,
        "stderr": result.stderr if result.stderr else None
    }
    
    if args.json or args.output:
        json_output = json.dumps(output, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Review saved to {args.output}")
        else:
            print(json_output)
    else:
        # Human-readable output
        print(f"Code Review for: {args.workdir}")
        print("=" * 50)
        
        if isinstance(review_data, dict):
            if "summary" in review_data:
                print(f"\nSummary: {review_data['summary']}\n")
            
            if "critical" in review_data and review_data["critical"]:
                print(f"\n🚨 Critical Issues: {len(review_data['critical'])}")
                for issue in review_data["critical"]:
                    print(f"  - {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}: {issue.get('issue', '')}")
            
            if "warnings" in review_data and review_data["warnings"]:
                print(f"\n⚠️  Warnings: {len(review_data['warnings'])}")
                for warning in review_data["warnings"]:
                    print(f"  - {warning.get('file', 'N/A')}:{warning.get('line', 'N/A')}: {warning.get('issue', '')}")
        else:
            print(result.stdout)
    
    sys.exit(0 if result.returncode == 0 else 1)


if __name__ == "__main__":
    main()
