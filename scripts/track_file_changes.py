#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Track file changes for audit purposes.
Creates a detailed log of all file modifications.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_file_info(file_path: str) -> dict:
    """Get file information if it exists."""
    try:
        path = Path(file_path)
        if path.exists():
            stat = path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "mode": oct(stat.st_mode),
                "is_dir": path.is_dir(),
                "is_file": path.is_file(),
            }
    except:
        pass
    return {"exists": False}

def main():
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit", "NotebookEdit"]:
        sys.exit(0)
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Extract file path
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path", "unknown")
    
    # Create detailed log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "file": file_path,
        "session_id": hook_input.get("session_id"),
        "file_info": get_file_info(file_path),
        "user": os.environ.get("USER", "unknown"),
        "cwd": os.getcwd(),
    }
    
    # Add operation-specific details
    if tool_name == "Write":
        log_entry["operation"] = "create_or_overwrite"
        log_entry["content_length"] = len(tool_input.get("content", ""))
    elif tool_name == "Edit":
        log_entry["operation"] = "edit"
        log_entry["old_string_length"] = len(tool_input.get("old_string", ""))
        log_entry["new_string_length"] = len(tool_input.get("new_string", ""))
        log_entry["replace_all"] = tool_input.get("replace_all", False)
    elif tool_name == "MultiEdit":
        log_entry["operation"] = "multi_edit"
        log_entry["edit_count"] = len(tool_input.get("edits", []))
    
    # Write to audit log
    with open(log_dir / "file-changes-audit.jsonl", "a") as f:
        json.dump(log_entry, f)
        f.write("\n")
    
    # Also write a simple summary to a human-readable log
    summary = f"[{log_entry['timestamp']}] {tool_name}: {file_path} by {log_entry['user']}"
    with open(log_dir / "file-changes-summary.log", "a") as f:
        f.write(summary + "\n")
    
    sys.exit(0)

if __name__ == "__main__":
    main()