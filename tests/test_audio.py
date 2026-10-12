import unittest

from audio import split_story_for_tts


class TestAudio(unittest.TestCase):

    def test_short_text_stays_in_one_chunk(self):
        text = "This is a short horror story."

        chunks = split_story_for_tts(text, max_chars=9000)

        self.assertEqual(chunks, [text])

    def test_long_text_splits_into_multiple_chunks(self):
        text = (
            "First paragraph is fairly long.\n\n"
            "Second paragraph is also fairly long."
        )

        chunks = split_story_for_tts(text, max_chars=40)

        self.assertGreater(len(chunks), 1)

    def test_chunks_respect_max_length(self):
        text = (
            "Paragraph one is short enough.\n\n"
            "Paragraph two is short enough.\n\n"
            "Paragraph three is short enough."
        )

        max_chars = 40
        chunks = split_story_for_tts(text, max_chars=max_chars)

        for chunk in chunks:
            self.assertLessEqual(len(chunk), max_chars)
    
    
if __name__ == "__main__":
    unittest.main()