import tempfile
import unittest
from pathlib import Path

from shorts import (
    create_styled_short_ass,
    seconds_to_ass_timestamp
)


class TestStyledShortCaptions(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        folder = Path(self.temp.name)

        self.source = folder / "story.srt"
        self.output = folder / "short.ass"

        self.source.write_text(
            "1\n"
            "00:00:00,000 --> 00:00:09,000\n"
            "I heard footsteps behind me "
            "inside the bedroom door.\n",
            encoding="utf-8"
        )

    def test_ass_timestamps(self):
        self.assertEqual(
            seconds_to_ass_timestamp(95.5),
            "0:01:35.50"
        )

    def test_creates_styled_caption_groups(self):
        create_styled_short_ass(
            self.source, self.output
        )

        content = self.output.read_text(
            encoding="utf-8"
        )

        self.assertIn("PlayResX: 1080", content)
        self.assertIn("PlayResY: 1920", content)
        self.assertIn("Style: Horror,Arial,72", content)

        dialogue = [
            line for line in content.splitlines()
            if line.startswith("Dialogue:")
        ]

        self.assertEqual(len(dialogue), 3)

    def test_highlighting_and_animation(self):
        create_styled_short_ass(
            self.source, self.output
        )

        content = self.output.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            r"{\1c&H00D7FF&}FOOTSTEPS",
            content
        )
        self.assertIn(r"\fad(80,80)", content)
        self.assertIn(r"\t(0,120,", content)


if __name__ == "__main__":
    unittest.main()
