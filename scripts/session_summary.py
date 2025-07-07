#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Generate session summary when Claude Code stops.
Can optionally block stop if tasks are incomplete.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

def analyze_session(session_id: str) -> dict:
    """Analyze the session's tool usage."""
    stats = {
        "total_tools": 0,
        "tool_counts": Counter(),
        "file_reads": [],
        "file_writes": [],
        "bash_commands": [],
        "errors": 0
    }
    
    # Read tool usage log if it exists
    tool_log = Path("logs/tool-usage.jsonl")
    if tool_log.exists():
        with open(tool_log) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("session_id") == session_id:
                        stats["total_tools"] += 1
                        tool_name = entry.get("tool_name", "unknown")
                        stats["tool_counts"][tool_name] += 1
                        
                        # Track specific operations
                        if tool_name == "Read":
                            file_path = entry.get("tool_input", {}).get("file_path")
                            if file_path:
                                stats["file_reads"].append(file_path)
                        elif tool_name in ["Write", "Edit", "MultiEdit"]:
                            file_path = entry.get("tool_input", {}).get("file_path")
                            if file_path:
                                stats["file_writes"].append(file_path)
                        elif tool_name == "Bash":
                            command = entry.get("tool_input", {}).get("command")
                            if command:
                                stats["bash_commands"].append(command)
                        
                        # Check for errors in post hooks
                        if entry.get("hook_type") == "post":
                            response = entry.get("tool_response", {})
                            if not response.get("success", True) or response.get("exit_code", 0) != 0:
                                stats["errors"] += 1
                except:
                    pass
    
    return stats

def check_incomplete_todos(session_id: str) -> list:
    """Check for incomplete todos in the current session."""
    # This is a placeholder - in a real implementation, you might
    # read the TodoRead output from the transcript
    return []

def main():
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    stop_hook_active = hook_input.get("stop_hook_active", False)
    
    # Don't create infinite loops
    if stop_hook_active:
        sys.exit(0)
    
    # Analyze the session
    stats = analyze_session(session_id)
    
    # Generate summary
    summary = f"""
=== Session Summary ===
Session ID: {session_id}
End Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Tool Calls: {stats['total_tools']}
Tool Usage:
"""
    
    for tool, count in stats['tool_counts'].most_common():
        summary += f"  - {tool}: {count}\n"
    
    summary += f"""
Files Read: {len(stats['file_reads'])}
Files Modified: {len(stats['file_writes'])}
Bash Commands: {len(stats['bash_commands'])}
Errors Encountered: {stats['errors']}
Transcript: {transcript_path}
=====================
"""
    
    # Write summary to log
    with open("logs/session-summaries.txt", "a") as f:
        f.write(summary)
    
    # Also create a JSON summary for programmatic access
    json_summary = {
        "session_id": session_id,
        "end_time": datetime.now().isoformat(),
        "stats": {
            "total_tools": stats["total_tools"],
            "tool_counts": dict(stats["tool_counts"]),
            "files_read": len(stats["file_reads"]),
            "files_modified": len(stats["file_writes"]),
            "bash_commands": len(stats["bash_commands"]),
            "errors": stats["errors"]
        },
        "transcript_path": transcript_path
    }
    
    with open("logs/session-summaries.jsonl", "a") as f:
        json.dump(json_summary, f)
        f.write("\n")
    
    # Example: Block stop if there are errors (commented out)
    # if stats['errors'] > 0:
    #     output = {
    #         "decision": "block",
    #         "reason": f"Session had {stats['errors']} errors. Please review before ending."
    #     }
    #     print(json.dumps(output))
    #     sys.exit(0)
    
    # Example: Check for incomplete todos (commented out)
    # incomplete = check_incomplete_todos(session_id)
    # if incomplete:
    #     output = {
    #         "decision": "block",
    #         "reason": f"You have {len(incomplete)} incomplete todos. Complete them?"
    #     }
    #     print(json.dumps(output))
    #     sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    main()