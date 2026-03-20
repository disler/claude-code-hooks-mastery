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
import subprocess
import random
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def build_notification_message(input_data):
    """Build a concise notification message, ending with project directory."""
    cwd = input_data.get('cwd', '')
    project_name = Path(cwd).name if cwd else 'unknown'
    notification_type = input_data.get('notification_type', '')
    message = input_data.get('message', '')

    # Build concise action description
    if notification_type == 'permission_prompt':
        # Extract tool name from messages like "Claude needs your permission to use Bash"
        tool = message.split('to use ')[-1] if 'to use ' in message else 'a tool'
        action = f"Claude needs permission for {tool}"
    elif notification_type == 'idle_prompt':
        action = "Claude is waiting for input"
    elif notification_type == 'elicitation_dialog':
        action = f"Claude has a question: {message}" if message else "Claude has a question"
    elif message:
        action = message
    else:
        action = "Claude needs your input"

    # Optionally prepend engineer name (30% chance)
    engineer_name = os.getenv('ENGINEER_NAME', '').strip()
    if engineer_name and random.random() < 0.3:
        action = f"{engineer_name}, {action[0].lower()}{action[1:]}"

    return f"{action} in {project_name}"


def send_desktop_notification(title, message):
    """Send a desktop push notification via notify-send (Linux)."""
    try:
        subprocess.run(
            ["notify-send", "--app-name=Claude Code", title, message],
            capture_output=True,
            timeout=5
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass


def announce_tts(input_data):
    """Announce via TTS."""
    notification_message = build_notification_message(input_data)

    try:
        tts_script = get_tts_script_path()
        if tts_script:
            subprocess.run([
                "uv", "run", tts_script, notification_message
            ],
            capture_output=True,
            timeout=10
            )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    except Exception:
        pass


def announce_desktop(input_data):
    """Send a desktop push notification."""
    notification_message = build_notification_message(input_data)
    cwd = input_data.get('cwd', '')
    title = f"Claude Code — {Path(cwd).name}" if cwd else "Claude Code"
    send_desktop_notification(title, notification_message)


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--notify',
            nargs='?',
            const='tts',
            default='off',
            choices=['tts', 'desktop', 'both', 'off'],
            help='Notification mode: tts (voice, default if no value given), desktop (notify-send), both, off (log only)'
        )
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Ensure log directory exists
        import os
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'notification.json')
        
        # Read existing log data or initialize empty list
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Send notification based on chosen mode
        # Skip for the generic "Claude is waiting for your input" message
        if args.notify != 'off' and input_data.get('message') != 'Claude is waiting for your input':
            if args.notify == 'tts':
                announce_tts(input_data)
            elif args.notify == 'desktop':
                announce_desktop(input_data)
            elif args.notify == 'both':
                announce_desktop(input_data)
                announce_tts(input_data)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()