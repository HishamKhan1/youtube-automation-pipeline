import os
import tempfile
import unittest

from project import completed_story_files_are_valid


class TestLegacyStoryCompletion(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = self.temp.name
        self.stories = [{}, {}]

        final_video = os.path.join(
            self.folder, "final_video_complete.mp4"
        )

        with open(final_video, "wb") as file:
            file.write(b"0" * 2000)

    def add_story(self, number):
        path = os.path.join(
            self.folder,
            f"story_{number:02d}.txt"
        )

        with open(path, "w") as file:
            file.write("Completed story.")

    def test_legacy_video_missing_story_rejected(self):
        self.add_story(1)

        self.assertFalse(
            completed_story_files_are_valid(
                self.folder,
                self.stories
            )
        )

    def test_legacy_video_all_stories_accepted(self):
        self.add_story(1)
        self.add_story(2)

        self.assertTrue(
            completed_story_files_are_valid(
                self.folder,
                self.stories
            )
        )


if __name__ == "__main__":
    unittest.main()
