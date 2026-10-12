import os
import tempfile
import unittest

from project import save_video_info, load_video_info


class TestProject(unittest.TestCase):

    def test_save_and_load_video_info(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_idea = "Test horror video"

            selected_stories = [
                {
                    "id": 1,
                    "title": "The Door",
                    "premise": "A door opens by itself every night."
                }
            ]

            all_story_ideas = selected_stories.copy()
            attempted_story_ids = [1]
            narrator_profiles = {"1": {"style": "calm"}}

            save_video_info(
                temp_dir,
                video_idea,
                selected_stories,
                all_story_ideas,
                attempted_story_ids,
                narrator_profiles
            )

            loaded = load_video_info(temp_dir)

            self.assertEqual(loaded["video_idea"], video_idea)
            self.assertEqual(loaded["selected_stories"], selected_stories)
            self.assertEqual(loaded["attempted_story_ids"], attempted_story_ids)
            self.assertEqual(loaded["narrator_profiles"], narrator_profiles)


if __name__ == "__main__":
    unittest.main()