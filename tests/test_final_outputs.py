import os
import json
import tempfile
import unittest

from pipeline import validate_final_outputs


class TestFinalOutputs(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = self.temp.name

        self.video = os.path.join(
            self.folder, "final_video_complete.mp4"
        )

        self.thumbnail = os.path.join(
            self.folder, "thumbnail_final.png"
        )

        self.metadata = os.path.join(
            self.folder, "youtube_metadata.json"
        )

        # Dummy files to test the current size checks
        for path in [self.video, self.thumbnail]:
            with open(path, "wb") as file:
                file.write(b"0" * 2000)

        with open(self.metadata, "w") as file:
            json.dump({
                "title": "Test Video",
                "description": "Test description"
            }, file)

    def test_missing_video_rejected(self):
        os.remove(self.video)

        with self.assertRaises(RuntimeError):
            validate_final_outputs(self.folder)

    def test_missing_thumbnail_rejected(self):
        os.remove(self.thumbnail)

        with self.assertRaises(RuntimeError):
            validate_final_outputs(self.folder)

    def test_invalid_metadata_rejected(self):
        with open(self.metadata, "w") as file:
            file.write("invalid json")

        with self.assertRaises(RuntimeError):
            validate_final_outputs(self.folder)

    def test_complete_outputs_accepted(self):
        self.assertTrue(
            validate_final_outputs(self.folder)
        )


if __name__ == "__main__":
    unittest.main()
