#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def main():
    try:
        parser = argparse.ArgumentParser(
            description="ConfigChange hook - logs and optionally audits configuration changes during a session"
        )
        parser.add_argument('--log-only', action='store_true',
                            help='Only log the event without any side effects')
        parser.add_argument('--audit', action='store_true',
                            help='Enable audit logging with extra detail')
        args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract fields
        source = input_data.get("source", "unknown")
        file_path = input_data.get("file_path", "")

        # Add timestamp to input data for logging
        input_data["logged_at"] = datetime.now().isoformat()

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "config_change.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
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

        # If audit mode, log additional context
        if args.audit:
            audit_path = os.path.join(log_dir, "config_change_audit.log")
            with open(audit_path, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] ConfigChange: source={source}, file_path={file_path}\n")

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
