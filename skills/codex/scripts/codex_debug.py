#!/usr/bin/env python3
"""Have Codex debug errors with context."""

import argparse
import json
import os
import subprocess
import sys

CODEX_PATH = os.path.expanduser("~/.local/bin/codex")


def get_codex_binary():
    """Get the path to the codex binary."""
    return CODEX_PATH if os.path.isfile(CODEX_PATH) else "codex"


def run_codex_debug(error, stacktrace=None, files=None, logs=None, workdir="."):
    """Run Codex in debug mode with error context."""
    
    prompt = f"""Debug this error:

**Error:** {error}

"""
    
    if stacktrace:
        prompt += f"**Stack trace:**\n```\n{stacktrace}\n```\n\n"
    
    if files:
        prompt += f"**Relevant files:** {files}\n\n"
    
    if logs:
        prompt += f"**Logs:**\n```\n{logs}\n```\n\n"
    
    prompt += """Analyze the error, identify the root cause, and provide a fix. Output your response as:

1. **Root Cause**: Brief explanation
2. **Suggested Fix**: Code changes needed
3. **Files to Modify**: List of files
4. **Apply Fix**: If yes, I will apply it with --approval full

```json
{
  "root_cause": "...",
  "suggested_fix": "...",
  "files_to_modify": ["..."],
  "confidence": "high|medium|low"
}
```"""
    
    cmd = [
        get_codex_binary(),
        "exec",
        "-m", "gpt-5.4",
        prompt
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=workdir
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Have Codex debug errors with context"
    )
    
    parser.add_argument("--error", "-e", required=True,
                        help="Error message to debug")
    parser.add_argument("--stacktrace", "-s",
                        help="Stack trace or traceback")
    parser.add_argument("--files", "-f",
                        help="Relevant files (comma-separated)")
    parser.add_argument("--logs",
                        help="Log output or additional context")
    parser.add_argument("--workdir", "-w", default=".",
                        help="Working directory")
    parser.add_argument("--apply", "-a", action="store_true",
                        help="Apply the suggested fix automatically")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output as JSON")
    
    args = parser.parse_args()
    
    # Run debug analysis
    result = run_codex_debug(
        error=args.error,
        stacktrace=args.stacktrace,
        files=args.files,
        logs=args.logs,
        workdir=args.workdir
    )
    
    output = {
        "success": result.returncode == 0,
        "error_analyzed": args.error,
        "analysis": result.stdout,
        "stderr": result.stderr if result.stderr else None
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Codex Debug Analysis")
        print("=" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("\nStderr:")
            print(result.stderr)
    
    sys.exit(0 if result.returncode == 0 else 1)


if __name__ == "__main__":
    main()
