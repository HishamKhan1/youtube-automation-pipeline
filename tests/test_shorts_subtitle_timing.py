import tempfile
import unittest
from pathlib import Path

from shorts import (
    create_short_subtitles,
    load_srt_cues,
    seconds_to_srt_timestamp
)


class TestShortsSubtitleTiming(unittest.TestCase):

    def test_timestamp_formatting(self):
        self.assertEqual(
            seconds_to_srt_timestamp(95.5),
            "00:01:35,500"
        )

    def test_subtitles_shift_to_short_timeline(self):

        with tempfile.TemporaryDirectory() as folder:

            source = Path(folder) / "original.srt"
            output = Path(folder) / "short.srt"

            source.write_text(
                "1\n"
                "00:00:01,000 --> 00:00:04,000\n"
                "I heard footsteps.\n\n"
                "2\n"
                "00:00:04,000 --> 00:00:08,000\n"
                "Someone was behind me.\n",
                encoding="utf-8"
            )

            create_short_subtitles(
                source, output,
                clip_start=3,
                clip_end=7
            )

            cues = load_srt_cues(output)

            self.assertEqual(len(cues), 2)

            self.assertEqual(cues[0]["start"], 0)
            self.assertEqual(cues[0]["end"], 1)

            self.assertEqual(cues[1]["start"], 1)
            self.assertEqual(cues[1]["end"], 4)

    def test_no_overlap_preserves_existing_output(self):

        with tempfile.TemporaryDirectory() as folder:

            source = Path(folder) / "original.srt"
            output = Path(folder) / "short.srt"

            source.write_text(
                "1\n"
                "00:00:10,000 --> 00:00:12,000\n"
                "The door opened.\n",
                encoding="utf-8"
            )

            output.write_text(
                "PREVIOUS OUTPUT",
                encoding="utf-8"
            )

            with self.assertRaises(RuntimeError):
                create_short_subtitles(
                    source, output, 0, 5
                )

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "PREVIOUS OUTPUT"
            )


if __name__ == "__main__":
    unittest.main()
