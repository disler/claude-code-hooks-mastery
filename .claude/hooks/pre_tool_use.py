#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import shlex
from pathlib import Path


def _parse_rm_tokens(tokens):
    """
    Given a list of tokens starting after 'rm', determine whether the
    combination of flags and operands constitutes a dangerous rm invocation.

    Returns True if the command is dangerous, False otherwise.

    Uses proper token-level parsing so that path components like
    '-enrollment' are never mistaken for flags (fixes #28).
    """
    has_recursive = False
    has_force = False
    operands = []
    end_of_options = False

    for tok in tokens:
        if end_of_options or not tok.startswith('-'):
            operands.append(tok)
            continue
        if tok == '--':
            end_of_options = True
            continue
        if tok in ('--recursive', '-R'):
            has_recursive = True
            continue
        if tok == '--force':
            has_force = True
            continue
        # Collapsed short flags like -rf, -fr, -Rf, -rfi, etc.
        if tok.startswith('-') and not tok.startswith('--'):
            flag_chars = tok[1:]
            if 'r' in flag_chars or 'R' in flag_chars:
                has_recursive = True
            if 'f' in flag_chars:
                has_force = True
            continue

    # rm -rf (or -r -f) is always dangerous
    if has_recursive and has_force:
        return True

    # rm -r targeting dangerous paths
    if has_recursive:
        dangerous_path_patterns = [
            r'^/$',             # Root
            r'^/\*$',           # Root wildcard
            r'^~/?',            # Home directory
            r'^\$HOME',         # $HOME
            r'\.\.',            # Parent directory traversal
            r'^\*$',            # Bare wildcard
            r'^\.$',            # Current directory
        ]
        for operand in operands:
            for pattern in dangerous_path_patterns:
                if re.search(pattern, operand):
                    return True

    return False


def is_dangerous_rm_command(command):
    """
    Detect dangerous rm commands using proper shell tokenization.

    Handles:
    - Direct rm invocations (rm -rf /)
    - Inline shell wrappers: bash -c "rm -rf /", sh -c "rm -rf /" (fixes #4)
    - Script execution: bash script.sh, source script.sh, . script.sh (fixes #4)

    Uses shlex.split instead of regex on the raw string so that path
    components like '-enrollment' are never misidentified as flags (fixes #28).
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Malformed quoting — fall back to simple whitespace split
        tokens = command.split()

    if not tokens:
        return False

    # --- Check 1: Direct rm invocation anywhere in a pipeline / chain -------
    # Split on shell operators so "echo hi && rm -rf /" is caught.
    # We re-tokenize each sub-command.
    sub_commands = _split_shell_commands(command)
    for sub in sub_commands:
        try:
            sub_tokens = shlex.split(sub)
        except ValueError:
            sub_tokens = sub.split()
        if not sub_tokens:
            continue

        cmd = _basename(sub_tokens[0])
        if cmd == 'rm':
            if _parse_rm_tokens(sub_tokens[1:]):
                return True

    # --- Check 2: Inline shell — bash/sh/zsh/dash -c "..." ----------------
    for sub in sub_commands:
        try:
            sub_tokens = shlex.split(sub)
        except ValueError:
            sub_tokens = sub.split()
        if not sub_tokens:
            continue

        cmd = _basename(sub_tokens[0])
        if cmd in ('bash', 'sh', 'zsh', 'dash'):
            # Look for -c flag and extract the inline script
            inline_script = _extract_inline_script(sub_tokens[1:])
            if inline_script and is_dangerous_rm_command(inline_script):
                return True

    # --- Check 3: Script file execution ------------------------------------
    # Patterns: bash script.sh, sh script.sh, source script.sh, . script.sh,
    #           ./script.sh, /path/to/script.sh
    for sub in sub_commands:
        try:
            sub_tokens = shlex.split(sub)
        except ValueError:
            sub_tokens = sub.split()
        if not sub_tokens:
            continue

        script_path = _detect_script_execution(sub_tokens)
        if script_path and _script_contains_dangerous_rm(script_path):
            return True

    return False


def _basename(path):
    """Return the basename of a command path, e.g. /usr/bin/rm -> rm."""
    return path.rsplit('/', 1)[-1] if '/' in path else path


def _split_shell_commands(command):
    """
    Naively split a shell command line on ;, &&, ||, and | boundaries.
    This is intentionally simple — full shell parsing is not the goal.
    """
    # Replace operators with a unique delimiter, then split
    result = re.split(r'\s*(?:&&|\|\||[;|])\s*', command)
    return [s.strip() for s in result if s.strip()]


def _extract_inline_script(tokens):
    """
    Given tokens after bash/sh (e.g. ['-c', 'rm -rf /']), return the
    inline script string if -c is present, else None.
    """
    for i, tok in enumerate(tokens):
        if tok == '-c' and i + 1 < len(tokens):
            # Everything after -c is the script (may be one quoted arg
            # or multiple args that the shell concatenates with spaces)
            return ' '.join(tokens[i + 1:])
    return None


def _detect_script_execution(tokens):
    """
    Detect if the command executes a script file.
    Returns the script file path or None.

    Patterns detected:
    - bash/sh/zsh/dash script.sh (without -c)
    - source script.sh
    - . script.sh
    - ./script.sh or /path/to/script.sh (if the file looks like a script)
    """
    if not tokens:
        return None

    cmd = _basename(tokens[0])

    # source / dot-command
    if cmd in ('source', '.') and len(tokens) > 1:
        return tokens[1]

    # bash/sh/zsh/dash script.sh (no -c flag)
    if cmd in ('bash', 'sh', 'zsh', 'dash'):
        # Skip option flags to find the script file argument
        for tok in tokens[1:]:
            if tok == '-c':
                return None  # Inline command, handled elsewhere
            if tok.startswith('-'):
                continue
            return tok  # First non-flag argument is the script file
        return None

    # Direct execution: ./script.sh or /abs/path/script.sh
    if '/' in tokens[0] or tokens[0].startswith('./'):
        return tokens[0]

    return None


def _script_contains_dangerous_rm(script_path):
    """
    Read a script file and check whether it contains a dangerous rm command.
    Returns False if the file doesn't exist or can't be read — fail open
    to avoid blocking legitimate commands against non-existent files.
    """
    try:
        path = Path(script_path).resolve()
        if not path.is_file():
            return False
        # Only inspect reasonably sized files (< 1 MB) to avoid stalls
        if path.stat().st_size > 1_000_000:
            return False
        content = path.read_text(errors='replace')
    except (OSError, PermissionError):
        return False

    # Check each non-comment line
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        # Recursively use the same detection for each line
        if is_dangerous_rm_command(stripped):
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