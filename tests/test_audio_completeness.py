import os
import tempfile
import unittest
from unittest.mock import patch

from audio import all_story_audio_is_valid


class TestAudioCompleteness(unittest.TestCase):

    def test_missing_story_rejected(self):

        with tempfile.TemporaryDirectory() as folder:

            story = os.path.join(
                folder,
                "story_01.txt"
            )

            with open(story, "w", encoding="utf-8") as f:
                f.write("Test story")

            with patch(
                "audio.audio_file_is_valid",
                return_value=True
            ):
                result = all_story_audio_is_valid(
                    folder, 2
                )

            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
