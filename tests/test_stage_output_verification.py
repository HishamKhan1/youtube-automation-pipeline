import tempfile
import unittest

from state import (
    create_project_state,
    load_project_state,
    mark_downstream_stale,
    run_stage
)


class TestStageOutputVerification(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.folder = self.temp.name
        create_project_state(self.folder)

        mark_downstream_stale(
            self.folder, "stories"
        )

    def test_missing_output_fails_stage(self):

        with self.assertRaises(RuntimeError):
            run_stage(
                self.folder,
                "audio",
                lambda: None,
                completion_check=lambda: False
            )

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["audio"]["status"],
            "failed"
        )

        self.assertTrue(
            state["stages"]["audio"]["rebuild_required"]
        )

    def test_valid_output_completes_stage(self):

        run_stage(
            self.folder,
            "audio",
            lambda: None,
            completion_check=lambda: True
        )

        state = load_project_state(self.folder)

        self.assertEqual(
            state["stages"]["audio"]["status"],
            "complete"
        )

        self.assertFalse(
            state["stages"]["audio"]["rebuild_required"]
        )


if __name__ == "__main__":
    unittest.main()
