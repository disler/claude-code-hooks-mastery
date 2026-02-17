#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def log_status_line(input_data, status_line_output):
    """Log status line event to logs directory."""
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "status_line.json"

    # Read existing log data or initialize empty list
    if log_file.exists():
        with open(log_file, "r") as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    # Create log entry with input data and generated output
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "input_data": input_data,
        "status_line_output": status_line_output,
    }

    # Append the log entry
    log_data.append(log_entry)

    # Write back to file with formatting
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def get_git_branch():
    """Get current git branch if in a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_status():
    """Get git status indicators."""
    try:
        # Check if there are uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            changes = result.stdout.strip()
            if changes:
                lines = changes.split("\n")
                return f"±{len(lines)}"
    except Exception:
        pass
    return ""


def generate_status_line(input_data):
    """Generate the status line based on input data."""
    parts = []

    # Model display name
    model_info = input_data.get("model", {})
    model_name = model_info.get("display_name", "Claude")
    parts.append(f"\033[36m[{model_name}]\033[0m")  # Cyan color

    # Current directory
    workspace = input_data.get("workspace", {})
    current_dir = workspace.get("current_dir", "")
    if current_dir:
        dir_name = os.path.basename(current_dir)
        parts.append(f"\033[34m📁 {dir_name}\033[0m")  # Blue color

    # Git branch and status
    git_branch = get_git_branch()
    if git_branch:
        git_status = get_git_status()
        git_info = f"🌿 {git_branch}"
        if git_status:
            git_info += f" {git_status}"
        parts.append(f"\033[32m{git_info}\033[0m")  # Green color

    # Version info (optional, smaller)
    version = input_data.get("version", "")
    if version:
        parts.append(f"\033[90mv{version}\033[0m")  # Gray color

    return " | ".join(parts)


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Generate status line
        status_line = generate_status_line(input_data)

        # Log the status line event
        log_status_line(input_data, status_line)

        # Output the status line (first line of stdout becomes the status line)
        print(status_line)

        # Success
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully - output basic status
        print("\033[31m[Claude] 📁 Unknown\033[0m")
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully - output basic status
        print("\033[31m[Claude] 📁 Error\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
