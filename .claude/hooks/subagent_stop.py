#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "anthropic",
# ]
# ///

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
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
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass

# Add hooks directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.tts.tts_queue import acquire_tts_lock, release_tts_lock, cleanup_stale_locks
except ImportError:
    # Fallback if imports fail - provide no-op functions
    def acquire_tts_lock(agent_id: str, timeout: int = 30) -> bool:
        return True
    def release_tts_lock(agent_id: str) -> None:
        pass
    def cleanup_stale_locks(max_age_seconds: int = 60) -> None:
        pass

try:
    from utils.llm.task_summarizer import summarize_subagent_task
except ImportError:
    # Fallback if imports fail
    def summarize_subagent_task(task_description: str, agent_name: Optional[str] = None) -> str:
        return "Subagent Complete"


def get_tts_script_path() -> Optional[str]:
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


def extract_task_context(input_data: dict) -> str:
    """
    Extract task context from the subagent input data.

    Looks for the agent transcript path and reads the initial task/prompt
    from the JSONL transcript file.

    Args:
        input_data: The input data dictionary from stdin

    Returns:
        A brief description of what the subagent was doing
    """
    # Try to get agent transcript path
    transcript_path = input_data.get("agent_transcript_path")
    if not transcript_path:
        # Fallback to regular transcript_path
        transcript_path = input_data.get("transcript_path")

    if not transcript_path or not os.path.exists(transcript_path):
        return "completed a task"

    try:
        # Read the JSONL transcript file
        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)

                    # Look for user messages or initial prompts
                    entry_type = entry.get("type", "")

                    if entry_type == "user":
                        # The content is nested in message.content
                        message = entry.get("message", {})
                        content = message.get("content", "") if isinstance(message, dict) else ""

                        # Fallback to direct content field
                        if not content:
                            content = entry.get("content", "")

                        if isinstance(content, str) and content:
                            # Truncate if too long
                            if len(content) > 200:
                                return content[:200] + "..."
                            return content
                        elif isinstance(content, list):
                            # Handle content blocks
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text = block.get("text", "")
                                    if text:
                                        if len(text) > 200:
                                            return text[:200] + "..."
                                        return text

                    # Also check for prompt field
                    prompt = entry.get("prompt", "")
                    if prompt:
                        if len(prompt) > 200:
                            return prompt[:200] + "..."
                        return prompt

                except json.JSONDecodeError:
                    continue

    except (OSError, IOError):
        pass

    return "completed a task"


def announce_subagent_completion(message: str = "Subagent Complete") -> None:
    """Announce subagent completion using the best available TTS service.

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
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        parser.add_argument('--notify', action='store_true', help='Enable TTS completion announcement')
        parser.add_argument('--summarize', action='store_true', default=True,
                            help='Generate AI summary of subagent task (default: on when --notify is used)')
        parser.add_argument('--no-summarize', dest='summarize', action='store_false',
                            help='Disable AI summary, use generic message')
        args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields (used for logging context)
        _ = input_data.get("session_id", "")
        _ = input_data.get("stop_hook_active", False)

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "subagent_stop.json")

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

        # Handle --chat switch (same as stop.py)
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines

                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Announce subagent completion via TTS (only if --notify flag is set)
        if args.notify:
            agent_id = input_data.get("agent_id", "unknown")
            debug_log(f"=== SubagentStop for agent: {agent_id} ===")
            debug_log(f"agent_transcript_path: {input_data.get('agent_transcript_path', 'NOT FOUND')}")
            debug_log(f"ANTHROPIC_API_KEY present: {bool(os.getenv('ANTHROPIC_API_KEY'))}")

            # Clean up any stale locks first
            cleanup_stale_locks(max_age_seconds=60)

            # Generate summary message
            if args.summarize:
                task_context = extract_task_context(input_data)
                debug_log(f"Extracted task_context: {task_context[:100]}...")
                summary_message = summarize_subagent_task(task_context, agent_name=agent_id)
                debug_log(f"Generated summary_message: {summary_message}")
            else:
                summary_message = "Subagent Complete"
                debug_log("Summarize disabled, using default message")

            # Acquire lock before speaking (blocks until available or timeout)
            if acquire_tts_lock(agent_id, timeout=30):
                try:
                    debug_log(f"Lock acquired, announcing: {summary_message}")
                    announce_subagent_completion(summary_message)
                finally:
                    release_tts_lock(agent_id)
                    debug_log("Lock released")
            else:
                # Timeout - still announce but log warning
                debug_log(f"Lock timeout, announcing anyway: {summary_message}")
                announce_subagent_completion(summary_message)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
