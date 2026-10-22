import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts import render_vertical_short


class TestShortsRendering(unittest.TestCase):

    def test_vertical_render_command(self):

        with tempfile.TemporaryDirectory() as folder:

            source = Path(folder) / "source.mp4"
            output = Path(folder) / "short.mp4"

            source.write_bytes(b"ORIGINAL")

            commands = []

            def fake_run(command, **kwargs):
                commands.append(command)
                Path(command[-1]).write_bytes(
                    b"RENDERED" * 500
                )

            with patch(
                "shorts.subprocess.run",
                side_effect=fake_run
            ):
                render_vertical_short(
                    source, output,
                    10, 45
                )

            self.assertTrue(output.exists())
            self.assertIn("1080", " ".join(commands[0]))
            self.assertIn("1920", " ".join(commands[0]))
            self.assertIn("35.000", commands[0])

    def test_failed_render_preserves_original(self):

        with tempfile.TemporaryDirectory() as folder:

            source = Path(folder) / "source.mp4"
            output = Path(folder) / "short.mp4"

            source.write_bytes(b"SOURCE")
            output.write_bytes(b"OLD_SHORT")

            with patch(
                "shorts.subprocess.run",
                side_effect=subprocess.CalledProcessError(
                    1, ["ffmpeg"]
                )
            ):
                with self.assertRaises(
                    subprocess.CalledProcessError
                ):
                    render_vertical_short(
                        source, output,
                        10, 45
                    )

            self.assertEqual(
                output.read_bytes(),
                b"OLD_SHORT"
            )


if __name__ == "__main__":
    unittest.main()
