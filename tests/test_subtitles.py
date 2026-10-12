import unittest

from subtitles import (
    normalize_subtitle_word,
    align_story_words
)


class TestSubtitles(unittest.TestCase):

    def test_normalize_lowercase(self):
        self.assertEqual(normalize_subtitle_word("HELLO"), "hello")

    def test_normalize_removes_punctuation(self):
        self.assertEqual(normalize_subtitle_word("hello!"), "hello")

    def test_normalize_removes_apostrophe(self):
        self.assertEqual(normalize_subtitle_word("don't"), "dont")

    def test_align_story_words_exact_match(self):
        story_words = [
            {"word": "the", "normalized": "the"},
            {"word": "door", "normalized": "door"},
            {"word": "opened", "normalized": "opened"},
        ]

        whisper_words = [
            {"word": "the", "normalized": "the", "start": 0.0, "end": 0.2},
            {"word": "door", "normalized": "door", "start": 0.2, "end": 0.5},
            {"word": "opened", "normalized": "opened", "start": 0.5, "end": 0.9},
        ]

        matches = align_story_words(
            story_words,
            whisper_words
        )

        self.assertEqual(len(matches), 3)

    
    
if __name__ == "__main__":
    unittest.main()