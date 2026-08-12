import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parents[1]
TTS_SCRIPT = PROJECT_ROOT / ".claude" / "hooks" / "utils" / "tts" / "minimax_tts.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


minimax_tts = load_module(TTS_SCRIPT, "minimax_tts")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class MiniMaxTTSTest(unittest.TestCase):
    def test_cn_endpoint_payload_and_hex_audio_decoding(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "data": {"audio": "494433", "status": 2},
                    "base_resp": {"status_code": 0},
                }
            )

        environment = {
            "MINIMAX_REGION": "cn_zh",
            "MINIMAX_TTS_MODEL": "speech-2.8-turbo",
            "MINIMAX_AUDIO_FORMAT": "wav",
            "MINIMAX_LANGUAGE_BOOST": "English",
            "MINIMAX_VOICE_ID": "test-voice",
        }
        with patch.dict(os.environ, environment, clear=True):
            audio, audio_format = minimax_tts.synthesize_speech(
                "Ready for review", "test-key", opener=opener
            )

        request = captured["request"]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.minimaxi.com/v1/t2a_v2")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(payload["model"], "speech-2.8-turbo")
        self.assertEqual(payload["text"], "Ready for review")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["output_format"], "hex")
        self.assertEqual(payload["voice_setting"], {"voice_id": "test-voice"})
        self.assertEqual(payload["language_boost"], "English")
        self.assertEqual(audio, b"ID3")
        self.assertEqual(audio_format, "wav")
        self.assertEqual(captured["timeout"], 8)

    def test_global_defaults_and_custom_endpoint(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                minimax_tts.get_endpoint(),
                "https://api.minimax.io/v1/t2a_v2",
            )
            payload = minimax_tts.build_payload("Hello")

        self.assertEqual(payload["model"], "speech-2.8-hd")
        self.assertEqual(payload["text"], "Hello")
        self.assertEqual(payload["audio_setting"], {"format": "mp3"})
        self.assertNotIn("voice_setting", payload)

        with patch.dict(
            os.environ,
            {"MINIMAX_TTS_ENDPOINT": "https://gateway.example/v1/t2a_v2"},
            clear=True,
        ):
            self.assertEqual(
                minimax_tts.get_endpoint(), "https://gateway.example/v1/t2a_v2"
            )

    def test_api_error_and_invalid_audio_are_rejected(self):
        def api_error(request, timeout):
            return FakeResponse(
                {"base_resp": {"status_code": 1004, "status_msg": "invalid request"}}
            )

        def invalid_audio(request, timeout):
            return FakeResponse(
                {
                    "data": {"audio": "not-hex", "status": 2},
                    "base_resp": {"status_code": 0},
                }
            )

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(minimax_tts.MiniMaxTTSError, "status 1004"):
                minimax_tts.synthesize_speech("Hello", "test-key", opener=api_error)
            with self.assertRaisesRegex(minimax_tts.MiniMaxTTSError, "hexadecimal"):
                minimax_tts.synthesize_speech("Hello", "test-key", opener=invalid_audio)


class TTSSelectorTest(unittest.TestCase):
    def test_hooks_select_minimax_before_offline_tts(self):
        hooks = ["stop.py", "notification.py", "subagent_start.py", "subagent_stop.py"]
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}, clear=True):
            for index, hook in enumerate(hooks):
                module = load_module(
                    PROJECT_ROOT / ".claude" / "hooks" / hook,
                    f"tts_selector_{index}",
                )
                with self.subTest(hook=hook):
                    self.assertTrue(module.get_tts_script_path().endswith("minimax_tts.py"))


if __name__ == "__main__":
    unittest.main()
