import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from audio import generate_all_story_audio
from state import (
    create_project_state,
    load_project_state,
    mark_downstream_stale,
    run_stage,
    set_stage_status
)


class TestAudioStageRecovery(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        create_project_state(self.folder)

        story = os.path.join(
            self.folder,
            "story_01.txt"
        )

        with open(story, "w", encoding="utf-8") as file:
            file.write("A test horror story.")

    def test_failed_audio_stage_forces_regeneration(self):

        mark_downstream_stale(
            self.folder, "stories"
        )

        set_stage_status(
            self.folder, "audio", "running"
        )
        set_stage_status(
            self.folder, "audio", "failed"
        )

        with (
            patch("audio.generate_story_audio") as narration,
            patch("audio.get_usage_totals", return_value={})
        ):
            run_stage(
                self.folder,
                "audio",
                generate_all_story_audio,
                Mock(),
                self.folder,
                1
            )

        self.assertTrue(
            narration.call_args.kwargs["force"]
        )

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["audio"]["status"],
            "complete"
        )

        self.assertFalse(
            state["stages"]["audio"]["rebuild_required"]
        )

    def test_new_project_uses_normal_caching(self):

        with (
            patch("audio.generate_story_audio") as narration,
            patch("audio.get_usage_totals", return_value={})
        ):
            run_stage(
                self.folder,
                "audio",
                generate_all_story_audio,
                Mock(),
                self.folder,
                1
            )

        self.assertFalse(
            narration.call_args.kwargs["force"]
        )


if __name__ == "__main__":
    unittest.main()
