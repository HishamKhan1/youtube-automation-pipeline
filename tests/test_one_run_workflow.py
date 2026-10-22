import ast
import os
import unittest
from pathlib import Path
from unittest.mock import Mock


class TestOneRunWorkflow(unittest.TestCase):

    def simulate(self, fail_stage=None):
        path = Path(__file__).resolve().parents[1] / "main.py"
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))

        start = next(
            i for i, node in enumerate(tree.body)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "existing_final_video"
                for target in node.targets
            )
        )

        section = ast.Module(
            body=tree.body[start:],
            type_ignores=[]
        )

        names = {
            node.id for node in ast.walk(section)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
        }

        scope = {
            name: Mock(name=name)
            for name in names
        }

        events = []

        def fake_run_stage(folder, stage, action, *args, **kwargs):
            events.append(stage)
            if stage == fail_stage:
                raise RuntimeError("Simulated stage failure")

        def fake_finalize(client, folder, rain):
            events.append("finalize")

        scope.update({
            "os": os,
            "len": len,
            "print": Mock(),
            "output_folder": "dry_run_project",
            "selected_stories": [{}],
            "channel_config": {
                "voice_id": "test_voice",
                "background_file": "test.mp4",
                "ambience_file": "test.mp3"
            },
            "final_video_can_be_reused": lambda *a: False,
            "complete_stage_if_file_exists": Mock(),
            "run_stage": fake_run_stage,
            "finalize_video_project": fake_finalize
        })

        compiled = compile(section, str(path), "exec")

        try:
            exec(compiled, scope)
        except RuntimeError:
            if fail_stage is None:
                raise

        return events

    def test_successful_workflow_finalizes_once(self):
        events = self.simulate()

        self.assertEqual(events.count("finalize"), 1)
        self.assertLess(
            events.index("subtitled_videos"),
            events.index("finalize")
        )

    def test_failed_subtitles_prevent_finalization(self):
        events = self.simulate(fail_stage="subtitles")

        self.assertIn("subtitles", events)
        self.assertNotIn("finalize", events)


if __name__ == "__main__":
    unittest.main()
