import ast
import unittest
from pathlib import Path


class TestVideoAssemblyArguments(unittest.TestCase):

    def test_combined_video_argument_order(self):
        root = Path(__file__).resolve().parents[1]

        pipeline = ast.parse(
            (root / "pipeline.py").read_text(encoding="utf-8-sig")
        )

        calls = [
            node for node in ast.walk(pipeline)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_stage"
            and len(node.args) >= 6
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "combined_video"
        ]

        self.assertEqual(len(calls), 1)

        arguments = [
            getattr(arg, "id", None)
            for arg in calls[0].args[2:6]
        ]

        self.assertEqual(arguments, [
            "combine_story_videos",
            "video_files",
            "transition_video",
            "concat_file"
        ])

        video = ast.parse(
            (root / "video.py").read_text(encoding="utf-8-sig")
        )

        functions = [
            node for node in video.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "combine_story_videos"
        ]

        self.assertEqual(len(functions), 1)
        self.assertEqual(
            [arg.arg for arg in functions[0].args.args],
            ["video_files", "output_file", "concat_file"]
        )


if __name__ == "__main__":
    unittest.main()
