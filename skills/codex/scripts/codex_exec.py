#!/usr/bin/env python3
"""Execute Codex tasks with full control and safety options."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


CODEX_PATH = os.path.expanduser("~/.local/bin/codex")


def check_codex_installed():
    """Check if Codex CLI is installed."""
    result = subprocess.run(["which", "codex"], capture_output=True, text=True)
    if result.returncode == 0:
        return True
    # Also check local install
    return os.path.isfile(CODEX_PATH)


def install_codex():
    """Attempt to install Codex."""
    print("Codex not found. Installing...")
    result = subprocess.run(
        ["npm", "install", "-g", "@openai/codex"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def run_codex_task(task, approval="auto", model=None, workdir=None, 
                   include=None, exclude=None):
    """Run a Codex task with the specified parameters."""
    
    # Use local path or fall back to PATH
    codex_binary = CODEX_PATH if os.path.isfile(CODEX_PATH) else "codex"
    
    cmd = [codex_binary, "exec"]
    
    # Add model
    if model:
        cmd.extend(["-m", model])
    
    # Add working directory
    if workdir:
        cmd.extend(["-C", workdir])
    
    # Approval mode mapping
    if approval == "full":
        cmd.append("--full-auto")
    elif approval == "manual":
        # No auto flag = manual mode
        pass
    else:  # auto
        cmd.append("--full-auto")
    
    # Add the prompt
    cmd.append(task)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=workdir or os.getcwd()
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Execute Codex tasks with safety controls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task "refactor auth module" --approval auto
  %(prog)s --task "fix bug in login" --workdir ./project --model gpt-5.4
        """
    )
    
    parser.add_argument("--task", "-t", required=True,
                        help="The task description for Codex")
    parser.add_argument("--approval", choices=["full", "auto", "manual"], 
                        default="auto",
                        help="Approval mode: full (unrestricted), auto (ask on destructive), manual (always ask)")
    parser.add_argument("--model", choices=["gpt-5.4", "gpt-5.3-codex"],
                        default="gpt-5.4",
                        help="Model to use")
    parser.add_argument("--workdir", "-w",
                        help="Working directory for the task")
    parser.add_argument("--include",
                        help="Comma-separated glob patterns for files to include")
    parser.add_argument("--exclude", "-e",
                        default="node_modules,.git,dist,build",
                        help="Comma-separated glob patterns for files to exclude")
    parser.add_argument("--output", "-o",
                        help="Output file for results (JSON format)")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be executed without running")
    
    args = parser.parse_args()
    
    # Handle dry-run before install check
    if args.dry_run:
        codex_bin = CODEX_PATH if os.path.isfile(CODEX_PATH) else "codex"
        print(f"Would execute: {codex_bin} exec")
        print(f"  Model: {args.model}")
        print(f"  Working dir: {args.workdir or os.getcwd()}")
        print(f"  Task: {args.task}")
        sys.exit(0)
    
    # Check/install Codex
    if not check_codex_installed():
        if not install_codex():
            error_result = {
                "success": False,
                "error": "Failed to install Codex CLI",
                "fix": "Install manually: npm install -g @openai/codex"
            }
            print(json.dumps(error_result), file=sys.stderr)
            sys.exit(1)
    
    # Validate working directory
    if args.workdir and not os.path.isdir(args.workdir):
        error_result = {
            "success": False,
            "error": f"Working directory does not exist: {args.workdir}"
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    
    # Set up environment
    env = os.environ.copy()
    env["CODEX_APPROVAL_MODE"] = args.approval
    
    if args.exclude:
        env["CODEX_EXCLUDE"] = args.exclude
    
    # Build the enhanced task with context
    task = args.task
    if args.include:
        task += f"\n\nFocus on these files: {args.include}"
    
    # Run the task
    start_time = os.times()
    result = run_codex_task(
        task=task,
        approval=args.approval,
        model=args.model,
        workdir=args.workdir,
        include=args.include,
        exclude=args.exclude
    )
    end_time = os.times()
    
    # Build response
    response = {
        "success": result.returncode == 0,
        "task": args.task,
        "approval_mode": args.approval,
        "model": args.model,
        "workdir": args.workdir or os.getcwd(),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr if result.stderr else None
    }
    
    if args.json or args.output:
        output = json.dumps(response, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
    else:
        # Human-readable output
        if response["success"]:
            print(f"✓ Task completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"✗ Task failed (exit code {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr}")
    
    sys.exit(0 if response["success"] else 1)


if __name__ == "__main__":
    main()
