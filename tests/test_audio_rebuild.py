import os
import tempfile
import unittest
from unittest.mock import patch

from pipeline import rebuild_ambience_only
from state import create_project_state, load_project_state


class TestAudioRebuild(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        create_project_state(self.folder)

        self.input_video = os.path.join(
            self.folder, "final_video_with_transitions.mp4"
        )
        self.final_video = os.path.join(
            self.folder, "final_video_complete.mp4"
        )
        self.rain = os.path.join(
            self.folder, "rain.mp3"
        )

        with open(self.input_video, "wb") as f:
            f.write(b"input" * 500)

        with open(self.final_video, "wb") as f:
            f.write(b"original" * 500)

        with open(self.rain, "wb") as f:
            f.write(b"rain")

    def test_successful_rebuild_invalidates_shorts(self):

        def fake_render(video, rain, output):
            with open(output, "wb") as f:
                f.write(b"rebuilt" * 500)

        with patch(
            "pipeline.add_background_ambience",
            side_effect=fake_render
        ):
            rebuild_ambience_only(
                self.folder, self.rain
            )

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["ambience"]["status"],
            "complete"
        )
        self.assertEqual(
            state["stages"]["shorts"]["status"],
            "stale"
        )
        self.assertEqual(
            state["stages"]["cleanup"]["status"],
            "stale"
        )

        with open(self.final_video, "rb") as f:
            self.assertEqual(
                f.read(), b"rebuilt" * 500
            )

    def test_failed_rebuild_preserves_original(self):

        with patch(
            "pipeline.add_background_ambience",
            side_effect=RuntimeError("Simulated failure")
        ):
            with self.assertRaises(RuntimeError):
                rebuild_ambience_only(
                    self.folder, self.rain
                )

        with open(self.final_video, "rb") as f:
            self.assertEqual(
                f.read(), b"original" * 500
            )

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["ambience"]["status"],
            "failed"
        )

        self.assertFalse(
            os.path.exists(
                os.path.join(
                    self.folder,
                    "final_video_rebuilding.mp4"
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
