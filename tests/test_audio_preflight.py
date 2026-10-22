import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from audio import generate_all_story_audio
from state import create_project_state


class TestAudioPreflight(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        create_project_state(self.folder)

    def test_missing_story_blocks_all_narration(self):
        story = os.path.join(self.folder, "story_01.txt")

        with open(story, "w", encoding="utf-8") as f:
            f.write("A complete story.")

        with patch("audio.generate_story_audio") as narration:
            with self.assertRaises(RuntimeError):
                generate_all_story_audio(
                    Mock(), self.folder, 2
                )

            narration.assert_not_called()

    def test_empty_story_blocks_all_narration(self):
        for number in [1, 2]:
            path = os.path.join(
                self.folder, f"story_{number:02d}.txt"
            )
            with open(path, "w", encoding="utf-8") as f:
                if number == 1:
                    f.write("A complete story.")

        with patch("audio.generate_story_audio") as narration:
            with self.assertRaises(RuntimeError):
                generate_all_story_audio(
                    Mock(), self.folder, 2
                )

            narration.assert_not_called()


if __name__ == "__main__":
    unittest.main()
