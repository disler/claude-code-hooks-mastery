#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Universal tool use logger for Claude Code hooks.
Logs all tool usage to a structured JSON format.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Log error and exit gracefully
        with open(log_dir / "hook-errors.log", "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}Z] JSON decode error in log_tool_use.py: {e}\n")
        sys.exit(0)
    
    # Determine if this is pre or post hook
    hook_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "hook_type": hook_type,
        "session_id": hook_input.get("session_id"),
        "tool_name": hook_input.get("tool_name"),
        "transcript_path": hook_input.get("transcript_path")
    }
    
    # Add tool-specific information
    if hook_type == "pre":
        log_entry["tool_input"] = hook_input.get("tool_input", {})
    elif hook_type == "post":
        log_entry["tool_input"] = hook_input.get("tool_input", {})
        log_entry["tool_response"] = hook_input.get("tool_response", {})
    
    # Write to log file
    log_file = log_dir / "tool-usage.jsonl"
    with log_file.open("a") as f:
        json.dump(log_entry, f)
        f.write("\n")
    
    # Success - no output means continue
    sys.exit(0)

if __name__ == "__main__":
    main()