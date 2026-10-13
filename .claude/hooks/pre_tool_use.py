#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import shlex
from pathlib import Path

# Operands that make a recursive rm dangerous no matter the flags. Compared
# lowercased, like the matcher below.
DANGEROUS_RM_TARGETS = frozenset({
    "/", "/*", "~", "~/", "$home", "..", "*", ".",
})

# Tokens that join simple commands (`rm a; rm -rf /` must still catch the
# second half without blaming the first).
_SHELL_SEPARATORS = frozenset({";", "&&", "||", "|", "&"})

# `sudo` wrappers around the real command (`sudo rm -rf /`, `sudo -u root rm
# -rf /`). Anything else leading means this segment is not an rm invocation.
_SUDO_VALUE_OPTIONS = frozenset({"-u", "--user", "-g", "--group"})


def _split_segments(tokens):
    """Split shell tokens at command separators (issue #28).

    shlex keeps `;`/`&` glued when they touch a word (`done;`), so a
    trailing one is peeled into its own separator. A quoted trailing `;`
    peels the same way (quotes are already gone) — only a segment boundary
    moves, and only an rm invocation spanning it could misread.
    """
    segments, current = [], []
    for token in tokens:
        words = [token]
        while (
            len(words[-1]) > 1
            and words[-1][-1] in ";&"
            and words[-1][-2:] not in ("&&", "||")
        ):
            words[-1:] = [words[-1][:-1], words[-1][-1:]]
        for word in words:
            if word in _SHELL_SEPARATORS:
                segments.append(current)
                current = []
            elif word:
                current.append(word)
    segments.append(current)
    return segments


def _rm_argv(segment):
    """The rm argv of one segment, or None when it is not an rm invocation.

    Skips one leading `sudo` (plus its `-u/-g` value options). Returns the
    tokens after the `rm` word itself: options, `--`, then operands.
    """
    words = list(segment)
    if words and words[0].lower() == "sudo":
        words = words[1:]
        while len(words) >= 2 and words[0].lower() in _SUDO_VALUE_OPTIONS:
            words = words[2:]
    if not words:
        return None
    head = words[0].lower()
    if head != "rm" and not head.endswith("/rm"):
        return None
    return words[1:]


def _parse_rm_flags(argv):
    """Split an rm argv into (recursive, force, operands).

    Only option tokens count as flags: `-` clusters, `--recursive` and
    `--force`, anywhere before a `--` terminator — GNU rm accepts options
    after operands too, so `rm -r dir -f` is still recursive+force. A
    pathname like `soft-hold-enrollment` never matches: it does not start
    with `-`, and that substring match was issue #28.
    """
    recursive = force = False
    operands = []
    options_done = False
    for token in argv:
        lowered = token.lower()
        if lowered == "--":
            options_done = True
        elif not options_done and lowered in ("--recursive", "--force"):
            if lowered == "--recursive":
                recursive = True
            else:
                force = True
        elif not options_done and re.fullmatch(r"-[a-z]+", lowered):
            flags = lowered[1:]
            recursive = recursive or "r" in flags
            force = force or "f" in flags
        else:
            operands.append(token)
    return recursive, force, operands


def _is_dangerous_target(operand):
    """Operands that are dangerous under a recursive rm, lowercased."""
    lowered = operand.lower()
    if lowered in DANGEROUS_RM_TARGETS:
        return True
    stripped = lowered.rstrip("/")
    if lowered and not lowered.strip("/"):
        return True  # /, //, /// are all root
    if lowered == "$home" or lowered.startswith("$home/"):
        return True  # the home dir itself or anything under it
    return bool(stripped) and (
        stripped.endswith("/..")
        or (lowered.startswith("~") and (len(lowered) == 1 or lowered[1] == "/"))
    )


def is_dangerous_rm_command(command):
    """
    True only for an rm invocation that is actually destructive: recursive
    plus force, or recursive into a dangerous target. Flags are read from
    option tokens (shlex), never matched as substrings of pathnames.
    Unparseable input is not blocked: it cannot run as written either.
    """
    try:
        tokens = shlex.split(command.lower(), posix=True)
    except ValueError:
        return False
    for segment in _split_segments(tokens):
        argv = _rm_argv(segment)
        if argv is None:
            continue
        recursive, force, operands = _parse_rm_flags(argv)
        if recursive and force:
            return True
        if recursive and any(_is_dangerous_target(o) for o in operands):
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