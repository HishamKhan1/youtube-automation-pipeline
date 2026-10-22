import unittest

from state import get_downstream_stages


class TestStageDependencies(unittest.TestCase):

    def test_audio_dependencies(self):
        stages = get_downstream_stages("audio")

        for name in [
            "subtitles",
            "story_videos",
            "combined_video",
            "ambience",
            "shorts"
        ]:
            self.assertIn(name, stages)

    def test_audio_does_not_affect_metadata(self):
        stages = get_downstream_stages("audio")

        self.assertNotIn("metadata", stages)
        self.assertNotIn("thumbnail_final", stages)
        self.assertNotIn("audio", stages)

    def test_story_changes_affect_metadata(self):
        stages = get_downstream_stages("stories")

        self.assertIn("audio", stages)
        self.assertIn("metadata", stages)
        self.assertIn("thumbnail_final", stages)
        self.assertIn("shorts", stages)

    def test_invalid_stage_rejected(self):
        with self.assertRaises(ValueError):
            get_downstream_stages("not_a_real_stage")


if __name__ == "__main__":
    unittest.main()
