import json
import os
import pathlib


def get_log_path():
    # Ensure log directory exists
    project_dir = os.getenv('CLAUDE_PROJECT_DIR', '.')
    project_dir = pathlib.Path(project_dir)
    log_dir = project_dir / 'logs'
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def append_log_data(log_file, data):
    log_file = get_log_path() / log_file

    # Read existing log data if there is any
    log_data = []
    if os.path.exists(log_file):
        with open(log_file, 'rt') as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                pass

    # Append new data
    log_data.append(data)

    # Write back to file with formatting
    with open(log_file, 'wt') as f:
        json.dump(log_data, f, indent=2)
