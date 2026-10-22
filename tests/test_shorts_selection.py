import unittest
from shorts import select_story_short


class TestShortsSelection(unittest.TestCase):

    def test_selects_valid_duration(self):

        cues = [
            {
                "start": i * 2,
                "end": (i + 1) * 2,
                "text": "The room was quiet."
            }
            for i in range(50)
        ]

        clip = select_story_short(cues)

        self.assertIsNotNone(clip)
        self.assertGreaterEqual(clip["duration"], 25)
        self.assertLessEqual(clip["duration"], 55)

    def test_prefers_suspenseful_moments(self):

        cues = [
            {
                "start": i * 2,
                "end": (i + 1) * 2,
                "text": (
                    "I heard a scream behind the locked door."
                    if i == 40
                    else "The room was quiet."
                )
            }
            for i in range(80)
        ]

        clip = select_story_short(cues)

        self.assertIn(
            "scream",
            clip["text"].lower()
        )


if __name__ == "__main__":
    unittest.main()
