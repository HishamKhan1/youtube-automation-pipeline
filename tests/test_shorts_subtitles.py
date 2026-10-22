import tempfile
import unittest
from pathlib import Path

from shorts import (
    load_srt_cues,
    timestamp_to_seconds
)


class TestShortsSubtitles(unittest.TestCase):

    def test_timestamp_conversion(self):
        self.assertEqual(
            timestamp_to_seconds("00:01:35,500"),
            95.5
        )

    def test_subtitle_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "story_01.srt"

            path.write_text(
                "1\n"
                "00:00:01,000 --> 00:00:03,500\n"
                "I heard someone knocking.\n\n"
                "2\n"
                "00:00:04,000 --> 00:00:06,000\n"
                "But I lived alone.\n",
                encoding="utf-8"
            )

            cues = load_srt_cues(path)

            self.assertEqual(len(cues), 2)
            self.assertEqual(cues[0]["start"], 1.0)
            self.assertEqual(cues[0]["end"], 3.5)
            self.assertEqual(
                cues[1]["text"],
                "But I lived alone."
            )


if __name__ == "__main__":
    unittest.main()