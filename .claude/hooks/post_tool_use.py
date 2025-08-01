#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import sys
from pathlib import Path

from _log_common import append_log_data


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Append new data
        append_log_data('post_tool_use.json', input_data)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()