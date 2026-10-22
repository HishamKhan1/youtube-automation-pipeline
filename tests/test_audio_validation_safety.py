import os
import tempfile
import unittest
from unittest.mock import Mock, patch
from audio import generate_story_audio


class TestAudioValidationSafety(unittest.TestCase):

    def test_invalid_replacement_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            story = os.path.join(folder, "story_01.txt")
            audio_file = os.path.join(folder, "story_01.mp3")

            with open(story, "w", encoding="utf-8") as f:
                f.write("A test horror story.")

            with open(audio_file, "wb") as f:
                f.write(b"ORIGINAL_AUDIO")

            client = Mock()
            client.text_to_speech.convert.return_value = [
                b"FAKE_NARRATION"
            ]

            def fake_ffmpeg(command, **kwargs):
                with open(command[-1], "wb") as f:
                    f.write(b"CORRUPT_AUDIO")

            def fake_validation(path):
                return os.path.abspath(path) == os.path.abspath(audio_file)

            with (
                patch("audio.subprocess.run", side_effect=fake_ffmpeg),
                patch("audio.audio_file_is_valid", side_effect=fake_validation),
                patch("audio.record_cost_event")
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "failed validation"
                ):
                    generate_story_audio(
                        client, folder, story, audio_file,
                        force=True
                    )

            with open(audio_file, "rb") as f:
                self.assertEqual(f.read(), b"ORIGINAL_AUDIO")


if __name__ == "__main__":
    unittest.main()
