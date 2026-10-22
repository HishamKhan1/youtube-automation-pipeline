import ast
import unittest
from pathlib import Path


class TestAutomaticFinalization(unittest.TestCase):

    def test_finalization_follows_video_generation(self):

        main_file = (
            Path(__file__).resolve().parents[1] / "main.py"
        )

        tree = ast.parse(
            main_file.read_text(encoding="utf-8-sig")
        )

        calls = []

        for index, node in enumerate(tree.body):

            if not isinstance(node, ast.Expr):
                continue

            if not isinstance(node.value, ast.Call):
                continue

            call = node.value

            if isinstance(call.func, ast.Name):
                calls.append(
                    (index, call.func.id, call)
                )

        finalization = [
            (index, call)
            for index, name, call in calls
            if name == "finalize_video_project"
        ]

        self.assertEqual(
            len(finalization),
            1,
            "Expected exactly one automatic finalization call"
        )

        subtitle_stage = [
            index
            for index, name, call in calls
            if (
                name == "run_stage"
                and len(call.args) >= 2
                and isinstance(call.args[1], ast.Constant)
                and call.args[1].value == "subtitled_videos"
            )
        ]

        self.assertEqual(len(subtitle_stage), 1)

        self.assertLess(
            subtitle_stage[0],
            finalization[0][0]
        )

        arguments = [
            arg.id if isinstance(arg, ast.Name) else None
            for arg in finalization[0][1].args
        ]

        self.assertEqual(
            arguments,
            ["client", "output_folder", "rain_file"]
        )


if __name__ == "__main__":
    unittest.main()
