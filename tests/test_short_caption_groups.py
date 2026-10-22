import unittest
from shorts import split_cues_for_shorts


class TestShortCaptionGroups(unittest.TestCase):

    def test_splits_long_sentence(self):

        cues = [{
            "start": 2.0,
            "end": 8.0,
            "text": (
                "I heard someone whisper my name "
                "from behind the locked bedroom door."
            )
        }]

        groups = split_cues_for_shorts(cues)

        self.assertGreater(len(groups), 1)

        self.assertTrue(
            all(
                2 <= len(g["text"].split()) <= 4
                for g in groups
            )
        )

        self.assertEqual(
            " ".join(g["text"] for g in groups),
            cues[0]["text"]
        )

        self.assertAlmostEqual(groups[0]["start"], 2.0)
        self.assertAlmostEqual(groups[-1]["end"], 8.0)

        for previous, current in zip(
            groups, groups[1:]
        ):
            self.assertAlmostEqual(
                previous["end"],
                current["start"]
            )

    def test_balances_five_words(self):

        cues = [{
            "start": 0.0,
            "end": 5.0,
            "text": "I heard footsteps behind me."
        }]

        groups = split_cues_for_shorts(cues)

        self.assertEqual(
            [len(g["text"].split()) for g in groups],
            [3, 2]
        )

    def test_preserves_gaps_between_cues(self):

        cues = [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "Someone knocked."
            },
            {
                "start": 3.0,
                "end": 4.0,
                "text": "I froze."
            }
        ]

        groups = split_cues_for_shorts(cues)

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["end"], 1.0)
        self.assertEqual(groups[1]["start"], 3.0)


if __name__ == "__main__":
    unittest.main()
