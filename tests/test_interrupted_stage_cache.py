import os
import tempfile
import unittest

from state import (
    create_project_state,
    set_stage_status,
    load_project_state,
    complete_stage_if_file_exists
)


class TestInterruptedStageCache(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        create_project_state(self.folder)

        self.cached_file = os.path.join(
            self.folder, "old_audio.mp3"
        )

        with open(self.cached_file, "wb") as f:
            f.write(b"OLD_AUDIO" * 500)

    def test_running_stage_cannot_reuse_old_output(self):
        set_stage_status(self.folder, "audio", "running")

        result = complete_stage_if_file_exists(
            self.folder, "audio", self.cached_file
        )

        self.assertFalse(result)

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["audio"]["status"],
            "running"
        )

    def test_failed_stage_cannot_reuse_old_output(self):
        set_stage_status(self.folder, "audio", "failed")

        result = complete_stage_if_file_exists(
            self.folder, "audio", self.cached_file
        )

        self.assertFalse(result)

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["audio"]["status"],
            "failed"
        )


if __name__ == "__main__":
    unittest.main()
