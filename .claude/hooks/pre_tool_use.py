#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import shlex
from pathlib import Path


def _looks_like_rm_invocation(tokens):
    """Return (is_rm, index_of_rm) for tokens.

    Supports common wrappers like: sudo rm ..., command rm ..., env VAR=... rm ...
    """
    if not tokens:
        return False, -1

    i = 0

    # Skip leading wrappers
    if tokens and tokens[0] == "sudo":
        i += 1

    if i < len(tokens) and tokens[i] == "env":
        i += 1
        # Skip env assignments (KEY=VALUE)
        while i < len(tokens) and "=" in tokens[i] and not tokens[i].startswith("-"):
            i += 1

    if i < len(tokens) and tokens[i] == "command":
        i += 1

    if i < len(tokens) and tokens[i] in ("rm", "\\rm"):
        return True, i

    return False, -1


def _parse_rm_options_and_operands(tokens_after_rm):
    """Parse rm flags and operands.

    We only treat -r/-R/--recursive and -f/--force as options when they are option
    *tokens*, not substrings inside operands (e.g. a path containing "-enrollment").
    """
    recursive = False
    force = False
    operands = []

    it = iter(tokens_after_rm)
    for tok in it:
        if tok == "--":
            operands.extend(list(it))
            break

        # Option token
        if tok.startswith("-") and tok != "-":
            if tok in ("-r", "-R", "--recursive"):
                recursive = True
                continue
            if tok in ("-f", "--force"):
                force = True
                continue

            # Combined short options like -rf, -fr, -Rfv
            if not tok.startswith("--"):
                for ch in tok[1:]:
                    if ch in ("r", "R"):
                        recursive = True
                    if ch == "f":
                        force = True
                continue

            # Unknown long option: ignore
            continue

        operands.append(tok)

    return recursive, force, operands


def _is_dangerous_rm_target(operand: str) -> bool:
    """Heuristic checks for dangerous rm targets.

    Note: absolute paths like /Users/... are NOT automatically dangerous.
    """
    op = operand.strip()

    # Common foot-guns
    if op in ("/", "/*", "*", ".", "./"):
        return True

    # Home directory nukes
    if op in ("~", "~/", "$HOME"):
        return True

    # Parent directory references (rm -r ..)
    if op in ("..", "../"):
        return True

    return False


def is_dangerous_rm_command(command):
    """Detect dangerous rm commands.

    - Avoid false positives from substrings inside paths.
    - Prefer parsing over regex heuristics.

    Current policy (conservative):
    - Any rm with BOTH recursive and force flags is considered dangerous.
    - rm with recursive flag is considered dangerous only when targeting clearly
      dangerous paths (/, ., .., ~, wildcards).
    """
    # Fast path: normalize whitespace only (do NOT lower-case blindly; keep operands)
    cmd = " ".join(command.split())

    try:
        tokens = shlex.split(cmd)
    except ValueError:
        # If parsing fails, fall back to a very conservative regex check
        normalized = " ".join(cmd.lower().split())
        return bool(re.search(r"\brm\s+.*\s-\w*[rR]\w*f", normalized))

    is_rm, rm_i = _looks_like_rm_invocation(tokens)
    if not is_rm:
        return False

    recursive, force, operands = _parse_rm_options_and_operands(tokens[rm_i + 1 :])

    if recursive and force:
        return True

    if recursive:
        return any(_is_dangerous_rm_target(op) for op in operands)

    return False


def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ["Read", "Edit", "MultiEdit", "Write", "Bash"]:
        # Check file paths for file-based tools
        if tool_name in ["Read", "Edit", "MultiEdit", "Write"]:
            file_path = tool_input.get("file_path", "")
            if ".env" in file_path and not file_path.endswith(".env.sample"):
                return True

        # Check bash commands for .env file access
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            # Pattern to detect .env file access (but allow .env.sample)
            env_patterns = [
                r"\b\.env\b(?!\.sample)",  # .env but not .env.sample
                r"cat\s+.*\.env\b(?!\.sample)",  # cat .env
                r"echo\s+.*>\s*\.env\b(?!\.sample)",  # echo > .env
                r"touch\s+.*\.env\b(?!\.sample)",  # touch .env
                r"cp\s+.*\.env\b(?!\.sample)",  # cp .env
                r"mv\s+.*\.env\b(?!\.sample)",  # mv .env
            ]

            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True

    return False


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Check for .env file access (blocks access to sensitive environment files)
        if is_env_file_access(tool_name, tool_input):
            print(
                "BLOCKED: Access to .env files containing sensitive data is prohibited",
                file=sys.stderr,
            )
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Check for dangerous rm -rf commands
        if tool_name == "Bash":
            command = tool_input.get("command", "")

            # Block rm commands with robust parsing (avoid pathname false positives)
            if is_dangerous_rm_command(command):
                print("BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Ensure log directory exists
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pre_tool_use.json"

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, "r") as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        sys.exit(0)

    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
