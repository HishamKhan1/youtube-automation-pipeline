import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts import burn_short_captions


class TestAssCaptionRendering(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        folder = Path(self.temp.name)

        self.video = folder / "vertical.mp4"
        self.ass = folder / "captions.ass"
        self.output = folder / "finished.mp4"

        self.video.write_bytes(b"SOURCE_VIDEO")

        self.ass.write_text(
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            "[Events]\n"
            "Dialogue: 0,0:00:00.00,0:00:02.00,"
            "Horror,,0,0,0,,HELLO\n",
            encoding="utf-8"
        )

    def test_uses_ass_styles(self):
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)

            working_dir = Path(kwargs["cwd"])

            self.assertTrue(
                (working_dir / "captions.ass").exists()
            )

            Path(command[-1]).write_bytes(
                b"RENDERED_VIDEO" * 200
            )

        with patch(
            "shorts.subprocess.run",
            side_effect=fake_run
        ):
            burn_short_captions(
                self.video,
                self.ass,
                self.output
            )

        video_filter = commands[0][
            commands[0].index("-vf") + 1
        ]

        self.assertEqual(
            video_filter,
            "subtitles=filename=captions.ass"
        )

        self.assertTrue(self.output.exists())

    def test_invalid_ass_preserves_output(self):
        self.ass.write_text(
            "INVALID DATA",
            encoding="utf-8"
        )

        self.output.write_bytes(b"OLD_VIDEO")

        with self.assertRaises(ValueError):
            burn_short_captions(
                self.video,
                self.ass,
                self.output
            )

        self.assertEqual(
            self.output.read_bytes(),
            b"OLD_VIDEO"
        )


if __name__ == "__main__":
    unittest.main()
