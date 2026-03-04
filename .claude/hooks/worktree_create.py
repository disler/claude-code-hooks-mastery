#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract fields
        name = input_data.get("name", "worktree")

        # Add timestamp to input data for logging
        input_data["logged_at"] = datetime.now().isoformat()

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "worktree_create.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        # Create the worktree using git
        worktree_base = os.path.join(os.getcwd(), ".claude", "worktrees")
        os.makedirs(worktree_base, exist_ok=True)
        worktree_path = os.path.join(worktree_base, name)

        # Create a new branch and worktree
        branch_name = f"worktree-{name}"
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, worktree_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Failed to create worktree: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Print the worktree path to stdout (required by WorktreeCreate contract)
        print(worktree_path)
        sys.exit(0)

    except json.JSONDecodeError:
        print("Invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating worktree: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
