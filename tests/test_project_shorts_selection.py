import tempfile
import unittest
from pathlib import Path

from shorts import select_project_shorts


class TestProjectShortsSelection(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = Path(self.temp.name)
        (self.folder / "subtitles").mkdir()

    def add_story(self, number):
        path = (
            self.folder
            / "subtitles"
            / f"story_{number:02d}.srt"
        )

        blocks = []

        for i in range(24):
            start = i * 2
            end = (i + 1) * 2

            text = (
                "I heard something behind the door."
                if i == 10
                else "The room was completely quiet."
            )

            blocks.append(
                f"{i + 1}\n"
                f"00:00:{start:02d},000 --> "
                f"00:00:{end:02d},000\n"
                f"{text}"
            )

        path.write_text(
            "\n\n".join(blocks),
            encoding="utf-8"
        )

    def test_selects_five_different_stories(self):
        for number in range(1, 7):
            self.add_story(number)

        clips = select_project_shorts(
            self.folder, 6
        )

        self.assertEqual(len(clips), 5)

        story_numbers = [
            clip["story_number"]
            for clip in clips
        ]

        self.assertEqual(
            len(set(story_numbers)), 5
        )

        for clip in clips:
            self.assertGreaterEqual(
                clip["duration"], 25
            )
            self.assertLessEqual(
                clip["duration"], 55
            )

    def test_respects_maximum_count(self):
        for number in range(1, 6):
            self.add_story(number)

        clips = select_project_shorts(
            self.folder, 5,
            max_shorts=3
        )

        self.assertEqual(len(clips), 3)

    def test_rejects_too_few_clips(self):
        for number in range(1, 3):
            self.add_story(number)

        with self.assertRaises(RuntimeError):
            select_project_shorts(
                self.folder, 2
            )


if __name__ == "__main__":
    unittest.main()
