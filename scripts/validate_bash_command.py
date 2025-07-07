#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Validate bash commands and provide feedback to Claude Code.
Can block dangerous commands and suggest improvements.
"""

import json
import re
import sys

# Define validation rules as (regex pattern, message, is_dangerous) tuples
VALIDATION_RULES = [
    # Performance suggestions
    (r"\bgrep\b(?!.*\|)", "Use 'rg' (ripgrep) instead of 'grep' for better performance and features", False),
    (r"\bfind\s+\S+\s+-name\b", "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance", False),
    (r"\bcat\s+.*\|\s*grep\b", "Use 'rg pattern file' instead of 'cat file | grep pattern'", False),
    
    # Security warnings
    (r"\brm\s+-rf\s+/(?:\s|$)", "DANGER: Attempting to remove root directory!", True),
    (r"\brm\s+-rf\s+~(?:/|$|\s)", "DANGER: Attempting to remove home directory!", True),
    (r"\bdd\s+.*of=/dev/[sh]d[a-z](?:\d|$)", "DANGER: Direct disk write operation detected!", True),
    (r">\s*/dev/[sh]d[a-z]", "DANGER: Attempting to write directly to disk device!", True),
    
    # Insecure practices
    (r"\bcurl\s+.*\s+-k\b", "Security Warning: -k flag disables SSL certificate verification", False),
    (r"\bwget\s+.*--no-check-certificate\b", "Security Warning: --no-check-certificate disables SSL verification", False),
    (r"\bchmod\s+777\b", "Security Warning: chmod 777 gives full permissions to everyone", False),
    (r"\bsudo\s+chmod\s+-R\s+777\b", "DANGER: Recursive chmod 777 is extremely insecure!", True),
    
    # Best practices
    (r"cd\s+&&\s+ls", "Consider using 'ls <directory>' instead of 'cd && ls'", False),
    (r"\|\s*wc\s+-l\b", "Consider using 'rg -c' for counting matches in files", False),
]

def validate_command(command: str) -> tuple[list[str], bool]:
    """
    Validate a command and return (issues, should_block).
    """
    issues = []
    should_block = False
    
    for pattern, message, is_dangerous in VALIDATION_RULES:
        if re.search(pattern, command, re.IGNORECASE):
            issues.append(message)
            if is_dangerous:
                should_block = True
    
    return issues, should_block

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If JSON parsing fails, exit silently
        sys.exit(0)
    
    # Check if this is a Bash tool call
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)
    
    # Get the command
    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)
    
    # Validate the command
    issues, should_block = validate_command(command)
    
    if issues:
        # Output issues to stderr (will be shown to Claude)
        for message in issues:
            print(f"• {message}", file=sys.stderr)
        
        # Exit code 2 blocks the command
        if should_block:
            sys.exit(2)
    
    # Exit code 0 allows the command to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()