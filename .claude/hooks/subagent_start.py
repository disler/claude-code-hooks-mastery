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
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def debug_log(message: str) -> None:
    """Write debug message to logs/subagent_debug.log"""
    try:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        debug_path = os.path.join(log_dir, "subagent_debug.log")
        timestamp = datetime.now().isoformat()
        with open(debug_path, 'a') as f:
            f.write(f"[{timestamp}] [START] {message}\n")
    except Exception:
        pass


def get_tts_script_path() -> str | None:
    """
    Determine which TTS script to use based on available API keys.
    MiniMax is selected before the offline fallback.
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

    # Check for MiniMax API key (third priority)
    if os.getenv('MINIMAX_API_KEY'):
        minimax_script = tts_dir / "minimax_tts.py"
        if minimax_script.exists():
            return str(minimax_script)

    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)

    return None


def announce_subagent_start(message: str = "Subagent Started") -> None:
    """Announce subagent start using the best available TTS service.

    Args:
        message: The message to announce via TTS
    """
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available

        # Call the TTS script with the provided message
        subprocess.run([
            "uv", "run", tts_script, message
        ],
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def main() -> None:
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="SubagentStart hook - logs and optionally announces subagent spawn events"
        )
        parser.add_argument('--notify', action='store_true',
                            help='Enable TTS announcement when subagent starts')
        args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract fields for logging/announcement (only extract what we use)
        agent_id = input_data.get("agent_id", "unknown")
        agent_type = input_data.get("agent_type", "unknown")

        # Add timestamp to input data for logging
        input_data["logged_at"] = datetime.now().isoformat()

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "subagent_start.json")

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

        debug_log(f"Logged SubagentStart: agent_id={agent_id}, agent_type={agent_type}")

        # Announce subagent start via TTS (only if --notify flag is set)
        if args.notify:
            debug_log(f"=== SubagentStart for agent: {agent_id} ===")
            debug_log(f"agent_type: {agent_type}")

            # Create announcement message
            if agent_type and agent_type != "unknown":
                announcement = f"{agent_type} agent started"
            else:
                announcement = "Subagent started"

            debug_log(f"Announcing: {announcement}")
            announce_subagent_start(announcement)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
