# Claude Code Utility Scripts

This directory contains utility scripts extracted from `ai_docs/cc_hooks_v0_repomix.xml` for easier access and use. These scripts provide comprehensive logging, monitoring, and automation capabilities for Claude Code.

## Available Scripts

### 🔔 custom_notifier.py
**Purpose**: Custom notification handler for Claude Code  
**Features**:
- Logs notifications to `logs/notifications-detailed.log`
- Platform-specific voice notifications (macOS say, Linux notify-send, Windows toast)
- Configurable voice and speech rate for macOS
- Runs with `uv` for dependency isolation

**Usage**: Automatically called by Claude Code's notification hooks

### 🎨 format_code.sh
**Purpose**: Auto-formats code after file modifications  
**Supported Languages**:
- Python: Uses `black` or `autopep8`
- JavaScript/TypeScript: Uses `prettier`
- Go: Uses `gofmt`
- Rust: Uses `rustfmt`
- Shell scripts: Uses `shfmt`

**Usage**: Runs automatically after Write/Edit/MultiEdit operations

### 📊 log_full_data.py
**Purpose**: Comprehensive logging of all hook data structures  
**Features**:
- Logs complete hook input/output data
- Useful for debugging and understanding hook behavior
- Creates detailed JSON logs in `logs/tool-data-structures.jsonl`
- Tracks raw input length and parsed data

**Usage**: Can be used with any hook type (pre/post/notification/stop)

### 📝 log_tool_use.py
**Purpose**: Structured logging of tool usage  
**Features**:
- Creates concise JSON logs of all tool calls
- Logs to `logs/tool-usage.jsonl`
- Includes timestamps, session IDs, and tool details
- Lightweight alternative to full data logging

**Usage**: Typically used with PreToolUse and PostToolUse hooks

### 📈 session_summary.py
**Purpose**: Generates session summaries when Claude Code exits  
**Features**:
- Counts total tool calls by type
- Tracks files read/modified
- Lists bash commands executed
- Creates both human-readable and JSON summaries
- Saves to `logs/session-summaries.txt` and `.jsonl`

**Usage**: Run with Stop hook to summarize sessions

### 🔍 track_file_changes.py
**Purpose**: Audit trail for file modifications  
**Features**:
- Logs all file changes with timestamps
- Tracks operation type (Write/Edit/MultiEdit)
- Records file paths and session context
- Saves to `logs/file-changes-audit.jsonl`

**Usage**: Attach to Write/Edit/MultiEdit PreToolUse hooks

### 🛡️ validate_bash_command.py
**Purpose**: Security validation for bash commands  
**Features**:
- Blocks dangerous commands (rm -rf, sudo, etc.)
- Prevents modification of system files
- Customizable blocked patterns
- Returns clear error messages to Claude

**Usage**: Attach to Bash PreToolUse hook for security

## Installation

All Python scripts use `uv` for dependency management. Ensure `uv` is installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For shell script formatting, install the formatters you need:
```bash
# macOS
brew install black prettier shfmt

# Python formatter
pip install black autopep8

# Node.js formatter
npm install -g prettier
```

## Example Hook Configuration

Add these to your `.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/log_tool_use.py pre"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/validate_bash_command.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/format_code.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/session_summary.py"
          }
        ]
      }
    ]
  }
}
```

## Notes

- All scripts are designed to fail silently to avoid disrupting Claude Code
- Logs are created in a `logs/` directory relative to your current working directory
- Scripts use proper error handling and timeouts
- Python scripts include inline `uv` script metadata for dependency management