import unittest
from chunking import split_text


class TestChunkingComprehensive(unittest.TestCase):

    def test_empty_and_whitespace(self):
        self.assertEqual(split_text(""), [])
        self.assertEqual(split_text("   "), [])
        self.assertEqual(split_text("\n\n\t  \n"), [])
        self.assertEqual(split_text(None), [])

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            split_text("Sample text", chunk_size=0)
        with self.assertRaises(ValueError):
            split_text("Sample text", chunk_size=-5)

        # Negative overlap should clamp to 0
        chunks = split_text("Hello world. This is a test.", chunk_size=50, chunk_overlap=-10)
        self.assertGreater(len(chunks), 0)

        # Overlap >= chunk_size should clamp to chunk_size - 1
        chunks2 = split_text("Hello world. This is a test.", chunk_size=30, chunk_overlap=50)
        self.assertGreater(len(chunks2), 0)

    def test_short_text_single_chunk(self):
        short = "This is a short sentence that easily fits in default chunk size."
        chunks = split_text(short, chunk_size=500, chunk_overlap=50)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short)

    def test_no_empty_chunks(self):
        text = "First sentence.   \n\n   \n\nSecond sentence. Third sentence."
        chunks = split_text(text, chunk_size=100, chunk_overlap=20)
        for c in chunks:
            self.assertTrue(len(c.strip()) > 0)

    def test_sentence_punctuation_boundaries(self):
        text = "Is this query one? Yes, it is! And here is statement three. Done."
        chunks = split_text(text, chunk_size=40, chunk_overlap=10)
        self.assertGreater(len(chunks), 1)
        # Check no chunk is empty and sentences are reasonably respected
        for c in chunks:
            self.assertTrue(len(c) <= 60)

    def test_long_sentence_without_punctuation(self):
        long_sentence = " ".join(["word" + str(i) for i in range(150)])
        chunks = split_text(long_sentence, chunk_size=200, chunk_overlap=30)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertTrue(len(c) <= 220)
            self.assertFalse(c.endswith("word") and not c.startswith("word"))

    def test_text_without_whitespace(self):
        # Extremely long single word: should slice safely without infinite loop
        unbroken = "A" * 600
        chunks = split_text(unbroken, chunk_size=200, chunk_overlap=20)
        self.assertGreater(len(chunks), 1)
        # Check no infinite loop and all characters covered
        joined = "".join(chunks)
        self.assertIn("A" * 200, joined)

    def test_word_boundary_preservation(self):
        words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]
        text = " ".join(words * 10)
        chunks = split_text(text, chunk_size=60, chunk_overlap=15)
        for c in chunks:
            chunk_words = c.split()
            for w in chunk_words:
                self.assertIn(w, words)

    def test_structured_paragraphs(self):
        p1 = "Artificial Intelligence is broad."
        p2 = "Machine Learning is a subset of AI."
        p3 = "Deep Learning is a subset of ML."
        doc = f"{p1}\n\n{p2}\n\n{p3}"
        chunks = split_text(doc, chunk_size=500, chunk_overlap=50)
        self.assertEqual(len(chunks), 1)
        self.assertIn(p1, chunks[0])
        self.assertIn(p2, chunks[0])
        self.assertIn(p3, chunks[0])


if __name__ == "__main__":
    unittest.main()
