import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from audio import generate_story_audio


class TestAudioForce(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        self.story = os.path.join(
            self.folder, "story_01.txt"
        )
        self.audio = os.path.join(
            self.folder, "story_01.mp3"
        )

        with open(self.story, "w", encoding="utf-8") as f:
            f.write("This is a test story.")

        with open(self.audio, "wb") as f:
            f.write(b"ORIGINAL_AUDIO")

        self.client = Mock()
        self.client.text_to_speech.convert.return_value = [
            b"FAKE_NARRATION"
        ]

    def test_force_rebuilds_existing_audio(self):

        def fake_ffmpeg(command, **kwargs):
            with open(command[-1], "wb") as f:
                f.write(b"REBUILT_AUDIO")

        with (
            patch("audio.audio_file_is_valid", return_value=True),
            patch("audio.record_cost_event"),
            patch("audio.subprocess.run", side_effect=fake_ffmpeg)
        ):

            generate_story_audio(
                self.client, self.folder,
                self.story, self.audio,
                force=False
            )

            self.client.text_to_speech.convert.assert_not_called()

            generate_story_audio(
                self.client, self.folder,
                self.story, self.audio,
                force=True
            )

        self.client.text_to_speech.convert.assert_called_once()

        with open(self.audio, "rb") as f:
            self.assertEqual(f.read(), b"REBUILT_AUDIO")

    def test_failed_rebuild_preserves_original(self):

        with (
            patch("audio.audio_file_is_valid", return_value=True),
            patch("audio.record_cost_event"),
            patch(
                "audio.subprocess.run",
                side_effect=RuntimeError("Simulated FFmpeg failure")
            )
        ):

            with self.assertRaises(RuntimeError):
                generate_story_audio(
                    self.client, self.folder,
                    self.story, self.audio,
                    force=True
                )

        with open(self.audio, "rb") as f:
            self.assertEqual(f.read(), b"ORIGINAL_AUDIO")


if __name__ == "__main__":
    unittest.main()
