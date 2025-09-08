#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import json
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


def log_status_line(input_data, status_line_output, error_message=None):
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
        "version": "v2",
        "input_data": input_data,
        "status_line_output": status_line_output,
    }

    if error_message:
        log_entry["error"] = error_message

    # Append the log entry
    log_data.append(log_entry)

    # Write back to file with formatting
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def get_last_prompt(session_id):
    """Get the last prompt for the current session."""
    # Use the JSON structure
    session_file = Path(f".claude/data/sessions/{session_id}.json")

    if not session_file.exists():
        return None, f"Session file {session_file} does not exist"

    try:
        with open(session_file, "r") as f:
            session_data = json.load(f)
            prompts = session_data.get("prompts", [])
            if prompts:
                return prompts[-1], None
            return None, "No prompts in session"
    except Exception as e:
        return None, f"Error reading session file: {str(e)}"


def generate_status_line(input_data):
    """Generate the status line showing the last prompt."""
    # Extract session ID from input data
    session_id = input_data.get("session_id", "unknown")

    # Get model name for prefix
    model_info = input_data.get("model", {})
    model_name = model_info.get("display_name", "Claude")

    # Get the last prompt
    prompt, error = get_last_prompt(session_id)

    if error:
        # Log the error but show a default message
        log_status_line(input_data, f"[{model_name}] 💭 No recent prompt", error)
        return f"\033[36m[{model_name}]\033[0m \033[90m💭 No recent prompt\033[0m"

    # Format the prompt for status line
    # Remove newlines and excessive whitespace
    prompt = " ".join(prompt.split())

    # Color coding based on prompt type
    if prompt.startswith("/"):
        # Command prompt - yellow
        prompt_color = "\033[33m"
        icon = "⚡"
    elif "?" in prompt:
        # Question - blue
        prompt_color = "\033[34m"
        icon = "❓"
    elif any(
        word in prompt.lower()
        for word in ["create", "write", "add", "implement", "build"]
    ):
        # Creation task - green
        prompt_color = "\033[32m"
        icon = "💡"
    elif any(word in prompt.lower() for word in ["fix", "debug", "error", "issue"]):
        # Fix/debug task - red
        prompt_color = "\033[31m"
        icon = "🐛"
    elif any(word in prompt.lower() for word in ["refactor", "improve", "optimize"]):
        # Refactor task - magenta
        prompt_color = "\033[35m"
        icon = "♻️"
    else:
        # Default - white
        prompt_color = "\033[37m"
        icon = "💬"

    # Construct the status line
    status_line = f"\033[36m[{model_name}]\033[0m {icon} {prompt_color}{prompt}\033[0m"

    return status_line


def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        # Generate status line
        status_line = generate_status_line(input_data)

        # Log the status line event (without error since it's successful)
        log_status_line(input_data, status_line)

        # Output the status line (first line of stdout becomes the status line)
        print(status_line)

        # Success
        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully - output basic status
        print("\033[31m[Claude] 💭 JSON Error\033[0m")
        sys.exit(0)
    except Exception as e:
        # Handle any other errors gracefully - output basic status
        print(f"\033[31m[Claude] 💭 Error: {str(e)}\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
