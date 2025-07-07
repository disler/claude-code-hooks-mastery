#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Log complete tool data structures for debugging and exploration.
Shows all available fields in hook inputs.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Read raw input
    raw_input = sys.stdin.read()
    
    try:
        # Parse JSON
        hook_input = json.loads(raw_input)
        
        # Determine hook type from command line args
        hook_type = "unknown"
        if len(sys.argv) > 1:
            hook_type = sys.argv[1]
        
        # Create detailed log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hook_type": hook_type,
            "raw_input_length": len(raw_input),
            "parsed_data": hook_input
        }
        
        # Write to detailed log file
        log_file = log_dir / "tool-data-structures.jsonl"
        with log_file.open("a") as f:
            json.dump(log_entry, f, indent=2)
            f.write("\n")
        
        # Also write a pretty-printed version for easier reading
        pretty_file = log_dir / f"tool-data-{hook_type}.json"
        with pretty_file.open("w") as f:
            json.dump(hook_input, f, indent=2)
        
        # Create a human-readable summary
        summary_file = log_dir / "tool-data-summary.log"
        with summary_file.open("a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Hook Type: {hook_type}\n")
            f.write(f"Tool Name: {hook_input.get('tool_name', 'N/A')}\n")
            f.write(f"Session ID: {hook_input.get('session_id', 'N/A')}\n")
            f.write(f"Available Keys: {', '.join(hook_input.keys())}\n")
            
            # Show tool_input structure
            if 'tool_input' in hook_input:
                f.write(f"Tool Input Keys: {', '.join(hook_input['tool_input'].keys())}\n")
            
            # Show tool_response structure (for post hooks)
            if 'tool_response' in hook_input:
                f.write(f"Tool Response Keys: {', '.join(hook_input['tool_response'].keys())}\n")
            
            f.write(f"{'='*60}\n")
        
    except json.JSONDecodeError as e:
        # Log error
        error_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "raw_input": raw_input[:1000]  # First 1000 chars
        }
        
        error_file = log_dir / "tool-data-errors.jsonl"
        with error_file.open("a") as f:
            json.dump(error_entry, f)
            f.write("\n")
    
    # Always exit successfully
    sys.exit(0)

if __name__ == "__main__":
    main()