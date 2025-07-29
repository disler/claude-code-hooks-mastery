#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "openai[voice_helpers]",
#     "python-dotenv",
# ]
# ///

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv


async def main():
    """
    OpenAI TTS Script

    Uses OpenAI's latest TTS model for high-quality text-to-speech.
    Accepts optional text prompt as command-line argument.

    Usage:
    - ./openai_tts.py                    # Uses default text
    - ./openai_tts.py "Your custom text" # Uses provided text

    Features:
    - OpenAI tts-1-hd model (high quality)
    - Nova voice (engaging and warm)
    - Streaming audio playback
    - Live audio playback via LocalAudioPlayer
    """

    # Load environment variables
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        from openai import AsyncOpenAI
        from openai.helpers import LocalAudioPlayer

        # Initialize OpenAI client
        openai = AsyncOpenAI(api_key=api_key)

        print("🎙️  OpenAI TTS")
        print("=" * 20)

        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            text = "Today is a wonderful day to build something people love!"

        print(f"🎯 Text: {text}")
        print("🔊 Generating and streaming...")

        try:
            # Generate audio using OpenAI TTS (non-streaming first)
            response = await openai.audio.speech.create(
                model="tts-1-hd",
                voice="nova",
                input=text,
                response_format="mp3",
            )
            
            # Save to temporary file and play
            temp_file = Path("/tmp/tts_output.mp3")
            with open(temp_file, "wb") as f:
                f.write(response.content)
            
            print(f"🎵 Audio saved to: {temp_file}")
            
            # Play audio using system command (macOS)
            try:
                import subprocess
                result = subprocess.run(
                    ["afplay", str(temp_file)], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    print("✅ Playback complete!")
                else:
                    print(f"⚠️  afplay failed: {result.stderr}")
                    # Fallback to open command
                    subprocess.run(["open", str(temp_file)])
                    print("📂 Opened with system default player")
            except Exception as player_error:
                print(f"⚠️  System playback failed: {player_error}")
                print(f"📁 Audio file saved at: {temp_file}")
                print("You can play it manually with: open /tmp/tts_output.mp3")

        except Exception as e:
            print(f"❌ Error: {e}")

    except ImportError as e:
        print("❌ Error: Required package not installed")
        print("This script uses UV to auto-install dependencies.")
        print("Make sure UV is installed: https://docs.astral.sh/uv/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
