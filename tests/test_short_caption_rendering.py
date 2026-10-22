import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts import burn_short_captions


class TestShortCaptionRendering(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = Path(self.temp.name)
        self.source = self.folder / "vertical.mp4"
        self.subtitles = self.folder / "short.srt"
        self.output = self.folder / "captioned.mp4"

        self.source.write_bytes(b"SOURCE_VIDEO")

        self.subtitles.write_text(
            "1\n"
            "00:00:00,000 --> 00:00:02,000\n"
            "Someone was behind the door.\n",
            encoding="utf-8"
        )

    def test_caption_render_command(self):
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)

            working_dir = Path(kwargs["cwd"])

            self.assertTrue(
                (working_dir / "captions.srt").is_file()
            )

            Path(command[-1]).write_bytes(
                b"CAPTIONED_VIDEO" * 200
            )

        with patch(
            "shorts.subprocess.run",
            side_effect=fake_run
        ):
            burn_short_captions(
                self.source,
                self.subtitles,
                self.output
            )

        self.assertTrue(self.output.is_file())

        video_filter = commands[0][
            commands[0].index("-vf") + 1
        ]

        self.assertIn(
            "subtitles=filename=captions.srt",
            video_filter
        )

        self.assertIn("FontSize=14", video_filter)
        self.assertIn("MarginV=60", video_filter)
        self.assertIn("Outline=1.5", video_filter)

    def test_render_failure_preserves_old_output(self):
        self.output.write_bytes(b"OLD_VIDEO")

        with patch(
            "shorts.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1, ["ffmpeg"]
            )
        ):
            with self.assertRaises(
                subprocess.CalledProcessError
            ):
                burn_short_captions(
                    self.source,
                    self.subtitles,
                    self.output
                )

        self.assertEqual(
            self.output.read_bytes(),
            b"OLD_VIDEO"
        )


if __name__ == "__main__":
    unittest.main()
