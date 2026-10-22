import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts import render_selected_project_short


class TestShortAssembly(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = Path(self.temp.name)

        (self.folder / "videos").mkdir()
        (self.folder / "subtitles").mkdir()

        self.video = (
            self.folder / "videos"
            / "story_02_video.mp4"
        )

        self.srt = (
            self.folder / "subtitles"
            / "story_02.srt"
        )

        self.srt.write_text(
            "1\n"
            "00:00:20,000 --> 00:00:30,000\n"
            "I heard footsteps behind the door.\n",
            encoding="utf-8"
        )

        self.clip = {
            "story_number": 2,
            "start": 22.0,
            "end": 27.0
        }

    def test_assembles_complete_short(self):
        self.video.write_bytes(b"SOURCE_VIDEO")

        def fake_render(source, output, start, end):
            Path(output).write_bytes(
                b"VERTICAL" * 300
            )

        def fake_captions(video, subtitles, output):
            Path(output).write_bytes(
                b"FINISHED" * 300
            )

        with (
            patch(
                "shorts.render_vertical_short",
                side_effect=fake_render
            ) as render,
            patch(
                "shorts.burn_short_captions",
                side_effect=fake_captions
            ) as captions
        ):
            result = render_selected_project_short(
                self.folder,
                self.clip,
                1
            )

        final = Path(result)

        self.assertTrue(final.is_file())
        self.assertEqual(
            final.name,
            "short_01_story_02.mp4"
        )

        assets = self.folder / "shorts" / "assets"

        self.assertTrue(
            (assets / "short_01_story_02.srt").is_file()
        )

        self.assertTrue(
            (assets / "short_01_story_02.ass").is_file()
        )

        self.assertEqual(render.call_count, 1)
        self.assertEqual(captions.call_count, 1)

    def test_missing_video_stops_assembly(self):
        with patch(
            "shorts.render_vertical_short"
        ) as render:
            with self.assertRaises(FileNotFoundError):
                render_selected_project_short(
                    self.folder,
                    self.clip,
                    1
                )

            render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
