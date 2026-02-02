#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import shlex
from pathlib import Path

def is_dangerous_rm_command(command):
    """
    Comprehensive detection of dangerous rm commands.
    Matches various forms of rm -rf and similar destructive patterns.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        # If parsing fails, don't block (fail open rather than break tooling)
        return False

    if not tokens:
        return False

    # Split into simple command segments on common separators.
    separators = {";", "&&", "||", "|"}
    segments = []
    current = []
    for t in tokens:
        if t in separators:
            if current:
                segments.append(current)
            current = []
            continue
        current.append(t)
    if current:
        segments.append(current)

    def _rm_invocation_is_dangerous(segment_tokens):
        if not segment_tokens:
            return False

        # Handle common prefix: sudo [opts] rm ...
        i = 0
        if segment_tokens[0] == "sudo":
            i = 1
            while i < len(segment_tokens):
                t = segment_tokens[i]
                if t == "--":
                    i += 1
                    break
                if t.startswith("-"):
                    # sudo -u <user> ...
                    if t in {"-u"} and i + 1 < len(segment_tokens):
                        i += 2
                        continue
                    i += 1
                    continue
                break

        if i >= len(segment_tokens):
            return False

        # Only treat this segment as rm if the executable token is rm (or /bin/rm, etc).
        exe = segment_tokens[i]
        if Path(exe).name != "rm":
            return False

        has_recursive = False
        has_force = False
        operands = []

        k = i + 1
        parsing_options = True
        while k < len(segment_tokens):
            t = segment_tokens[k]

            if parsing_options and t == "--":
                parsing_options = False
                k += 1
                continue

            if parsing_options and t.startswith("--"):
                if t == "--recursive":
                    has_recursive = True
                    k += 1
                    continue
                if t == "--force":
                    has_force = True
                    k += 1
                    continue
                # Unknown long option: treat as option, not operand
                k += 1
                continue

            if parsing_options and t.startswith("-") and t != "-":
                # Short options may be combined: -rf, -fr, -R, etc.
                for ch in t[1:]:
                    if ch in {"r", "R"}:
                        has_recursive = True
                    elif ch == "f":
                        has_force = True
                k += 1
                continue

            operands.append(t)
            k += 1

        # Preserve prior intent: rm with both recursive + force is always blocked.
        if has_recursive and has_force:
            return True

        # For recursive deletes, block obviously dangerous targets.
        if not has_recursive:
            return False

        dangerous_exact = {"/", "/*", ".", ".."}
        for op in operands:
            if op in dangerous_exact or op.lower() in dangerous_exact:
                return True

            # Home directory (raw "~" tokens)
            if op == "~" or op.startswith("~/"):
                return True

            # Home env var usage (raw "$HOME" tokens)
            if op == "$HOME" or op.startswith("$HOME/"):
                return True

            # Globs are too risky with recursion
            if any(ch in op for ch in ["*", "?", "["]):
                return True

            # Parent directory traversal components (e.g. foo/../bar)
            try:
                if ".." in Path(op).parts:
                    return True
            except Exception:
                # If Path can't parse, ignore and continue
                pass

        return False

    for seg in segments:
        if _rm_invocation_is_dangerous(seg):
            return True

    return False

def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write', 'Bash']:
        # Check file paths for file-based tools
        if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
            file_path = tool_input.get('file_path', '')
            if '.env' in file_path and not file_path.endswith('.env.sample'):
                return True

        # Check bash commands for .env file access
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')
            # Pattern to detect .env file access (but allow .env.sample)
            env_patterns = [
                r'\b\.env\b(?!\.sample)',  # .env but not .env.sample
                r'cat\s+.*\.env\b(?!\.sample)',  # cat .env
                r'echo\s+.*>\s*\.env\b(?!\.sample)',  # echo > .env
                r'touch\s+.*\.env\b(?!\.sample)',  # touch .env
                r'cp\s+.*\.env\b(?!\.sample)',  # cp .env
                r'mv\s+.*\.env\b(?!\.sample)',  # mv .env
            ]

            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True

    return False

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        # Check for .env file access (blocks access to sensitive environment files)
        if is_env_file_access(tool_name, tool_input):
            print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Check for dangerous rm -rf commands
        if tool_name == 'Bash':
            command = tool_input.get('command', '')

            # Block rm -rf commands with comprehensive pattern matching
            if is_dangerous_rm_command(command):
                print("BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'pre_tool_use.json'

        # Read existing log data or initialize empty list
        if log_path.exists():
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

        sys.exit(0)

    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()
