#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

"""Generate and play speech with the MiniMax Text-to-Audio API."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


REGION_ENDPOINTS = {
    "global_en": "https://api.minimax.io/v1/t2a_v2",
    "cn_zh": "https://api.minimaxi.com/v1/t2a_v2",
}


class MiniMaxTTSError(RuntimeError):
    """Raised when MiniMax cannot generate playable audio."""


def get_endpoint() -> str:
    """Return the configured MiniMax regional endpoint."""
    custom_endpoint = os.getenv("MINIMAX_TTS_ENDPOINT", "").strip()
    if custom_endpoint:
        return custom_endpoint

    region = os.getenv("MINIMAX_REGION", "global_en").strip().lower()
    aliases = {"global": "global_en", "cn": "cn_zh"}
    region = aliases.get(region, region)
    try:
        return REGION_ENDPOINTS[region]
    except KeyError as exc:
        supported = ", ".join(REGION_ENDPOINTS)
        raise MiniMaxTTSError(
            f"Unsupported MINIMAX_REGION '{region}'. Use one of: {supported}."
        ) from exc


def build_payload(text: str) -> dict[str, Any]:
    """Build a non-streaming MiniMax speech request."""
    payload: dict[str, Any] = {
        "model": os.getenv("MINIMAX_TTS_MODEL", "speech-2.8-hd"),
        "text": text,
        "stream": False,
        "output_format": "hex",
    }

    voice_id = os.getenv("MINIMAX_VOICE_ID", "").strip()
    if voice_id:
        payload["voice_setting"] = {"voice_id": voice_id}

    language = os.getenv("MINIMAX_LANGUAGE_BOOST", "").strip()
    if language:
        payload["language_boost"] = language

    audio_format = os.getenv("MINIMAX_AUDIO_FORMAT", "mp3").strip().lower()
    if audio_format not in {"mp3", "wav", "flac", "pcm"}:
        raise MiniMaxTTSError(
            "Unsupported MINIMAX_AUDIO_FORMAT. Use mp3, wav, flac, or pcm."
        )
    payload["audio_setting"] = {"format": audio_format}
    return payload


def synthesize_speech(
    text: str,
    api_key: str,
    opener: Callable[..., Any] | None = None,
) -> tuple[bytes, str]:
    """Request speech and decode the hexadecimal audio response."""
    payload = build_payload(text)
    request = Request(
        get_endpoint(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with (opener or urlopen)(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise MiniMaxTTSError(f"MiniMax request failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        detail = getattr(exc, "reason", exc)
        raise MiniMaxTTSError(f"MiniMax request failed: {detail}.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MiniMaxTTSError("MiniMax returned an invalid JSON response.") from exc

    base_response = result.get("base_resp") or {}
    status_code = base_response.get("status_code", 0)
    if status_code != 0:
        status_message = base_response.get("status_msg", "unknown error")
        raise MiniMaxTTSError(
            f"MiniMax returned status {status_code}: {status_message}."
        )

    audio_hex = (result.get("data") or {}).get("audio")
    if not isinstance(audio_hex, str) or not audio_hex:
        raise MiniMaxTTSError("MiniMax returned no audio data.")

    try:
        audio = bytes.fromhex(audio_hex)
    except ValueError as exc:
        raise MiniMaxTTSError("MiniMax returned invalid hexadecimal audio data.") from exc

    return audio, payload["audio_setting"]["format"]


def play_audio(audio: bytes, audio_format: str) -> None:
    """Play audio with an available operating-system player."""
    player = None
    command: list[str] = []
    if sys.platform == "darwin":
        player = shutil.which("afplay")
    elif sys.platform.startswith("linux"):
        player = shutil.which("ffplay") or shutil.which("mpg123")

    if not player:
        raise MiniMaxTTSError("No supported audio player was found.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as file:
            file.write(audio)
            temp_path = Path(file.name)

        if Path(player).name == "ffplay":
            command = [player, "-nodisp", "-autoexit", "-loglevel", "quiet", str(temp_path)]
        else:
            command = [player, str(temp_path)]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise MiniMaxTTSError("Audio playback failed.") from exc
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


def main() -> None:
    """Generate and play speech for the command-line text."""
    if load_dotenv:
        load_dotenv()

    api_key = os.getenv("MINIMAX_API_KEY", "").strip()
    if not api_key:
        print("Error: MINIMAX_API_KEY is not configured.", file=sys.stderr)
        sys.exit(1)

    text = " ".join(sys.argv[1:]).strip()
    if not text:
        text = "The first move is what sets everything in motion."

    try:
        audio, audio_format = synthesize_speech(text, api_key)
        play_audio(audio, audio_format)
    except MiniMaxTTSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
