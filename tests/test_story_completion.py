import os
import tempfile
import unittest

from project import completed_story_files_are_valid


class TestStoryCompletion(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = self.temp.name
        self.stories = [{}, {}]

        self.marker = os.path.join(
            self.folder, "stories_complete.marker"
        )

        with open(self.marker, "w") as file:
            file.write("complete")

    def add_story(self, number, content):
        path = os.path.join(
            self.folder, f"story_{number:02d}.txt"
        )

        with open(path, "w") as file:
            file.write(content)

    def test_missing_story_rejected(self):
        self.add_story(1, "First story.")

        self.assertFalse(
            completed_story_files_are_valid(
                self.folder, self.stories
            )
        )

    def test_complete_stories_accepted(self):
        self.add_story(1, "First story.")
        self.add_story(2, "Second story.")

        self.assertTrue(
            completed_story_files_are_valid(
                self.folder, self.stories
            )
        )

    def test_empty_story_rejected(self):
        self.add_story(1, "First story.")
        self.add_story(2, "")

        self.assertFalse(
            completed_story_files_are_valid(
                self.folder, self.stories
            )
        )

    def test_missing_marker_rejected(self):
        self.add_story(1, "First story.")
        self.add_story(2, "Second story.")
        os.remove(self.marker)

        self.assertFalse(
            completed_story_files_are_valid(
                self.folder, self.stories
            )
        )


if __name__ == "__main__":
    unittest.main()
