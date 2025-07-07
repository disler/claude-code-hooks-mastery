#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///
"""
Custom notification handler for Claude Code.
Logs notifications and can be extended to send to various notification systems.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def main():
    try:
        # Read notification data from stdin
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    # Extract notification details
    message = hook_input.get("message", "")
    title = hook_input.get("title", "Claude Code")
    session_id = hook_input.get("session_id", "unknown")
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Log notification to file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{session_id}] {title}: {message}\n"
    
    with open(log_dir / "notifications-detailed.log", "a") as f:
        f.write(log_entry)
    
    # Platform-specific notification (optional)
    # You can uncomment and customize these based on your platform:
    
    # macOS notification using osascript and say
    if sys.platform == "darwin":
        # Escape quotes for shell
        safe_message = message.replace("'", "'\"'\"'")
        safe_title = title.replace("'", "'\"'\"'")
        
        # Voice notification using macOS 'say' command
        if os.path.exists("/usr/bin/say"):
            # Combine title and message for speech
            speech_text = f"{title}: {message}" if title != "Claude Code" else message
            safe_speech = speech_text.replace("'", "'\"'\"'")
            
            # Use say command with some nice options:
            # -v: voice (default system voice if not specified)
            # -r: rate (words per minute, default is ~200)
            os.system(f"say -r 180 '{safe_speech}' &")  # & runs it in background
        
        # Visual notification using osascript (optional)
        if os.path.exists("/usr/bin/osascript"):
            escaped_message = message.replace('"', '\\"')
            escaped_title = title.replace('"', '\\"')
            # Uncomment to also enable desktop notifications:
            # os.system(f'osascript -e \'display notification "{escaped_message}" with title "{escaped_title}"\'')
    
    # Linux notification using notify-send
    elif sys.platform.startswith("linux") and os.path.exists("/usr/bin/notify-send"):
        # Uncomment to enable desktop notifications:
        # os.system(f'notify-send "{title}" "{message}"')
        pass
    
    # Windows notification (requires win10toast)
    elif sys.platform == "win32":
        # Uncomment and install win10toast to enable:
        # try:
        #     from win10toast import ToastNotifier
        #     toaster = ToastNotifier()
        #     toaster.show_toast(title, message, duration=10)
        # except ImportError:
        #     pass
        pass
    
    sys.exit(0)

if __name__ == "__main__":
    main()