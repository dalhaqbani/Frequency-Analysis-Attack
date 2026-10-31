"""
test_frequency_analysis.py
--------------------------
Unit tests for cipher.py, frequency_analysis.py and english_model.py.

Run with:  python -m unittest -v test_frequency_analysis.py
"""

import unittest

import cipher
import english_model as em
import frequency_analysis as fa
from sample_texts import SAMPLES


def letter_accuracy(guess, truth):
    """Percentage of letters in truth that guess got right (case ignored)."""
    pairs = [(g, t) for g, t in zip(guess.upper(), truth.upper()) if t.isalpha()]
    return 100 * sum(g == t for g, t in pairs) / len(pairs)


class TestCipher(unittest.TestCase):

    def test_key_is_a_permutation(self):
        key = cipher.generate_key(seed=1)

        self.assertEqual(sorted(key), list(cipher.ALPHABET))

    def test_same_seed_same_key(self):
        self.assertEqual(cipher.generate_key(seed=7), cipher.generate_key(seed=7))

    def test_encrypt_then_decrypt(self):
        key = cipher.generate_key(seed=3)
        text = "Meet me at noon, 12 sharp!"

        self.assertEqual(cipher.decrypt(cipher.encrypt(text, key), key), text.upper())

    def test_non_letters_unchanged(self):
        key = cipher.generate_key(seed=3)
        ciphertext = cipher.encrypt("Hi, 2026!", key)

        self.assertEqual(ciphertext[2:], ", 2026!")

    def test_invalid_key_rejected(self):
        with self.assertRaises(ValueError):
            cipher.encrypt("abc", "ABC")


class TestFrequencies(unittest.TestCase):

    def test_counts_ignore_case(self):
        counts = fa.letter_counts("AaB c!")

        self.assertEqual(counts["A"], 2)
        self.assertEqual(counts["B"], 1)
        self.assertEqual(counts["Z"], 0)
        self.assertEqual(len(counts), 26)

    def test_percentages(self):
        freqs = fa.letter_frequencies("AAB")

        self.assertAlmostEqual(freqs["A"], 200 / 3)
        self.assertAlmostEqual(sum(freqs.values()), 100)
        self.assertEqual(fa.letter_frequencies("123")["A"], 0.0)

    def test_sorted_by_frequency(self):
        # X appears 4 times, Q 3, Z 2; letters that never appear are dropped
        self.assertEqual(fa.sorted_by_frequency("XXXX QQQ ZZ"), ["X", "Q", "Z"])

    def test_ties_sorted_alphabetically(self):
        self.assertEqual(fa.sorted_by_frequency("ZZ AA MM"), ["A", "M", "Z"])


class TestMappingAndDecryption(unittest.TestCase):

    def test_rank_matching(self):
        mapping = fa.build_mapping("XXXX QQQ ZZ")

        self.assertEqual(
            (mapping["X"], mapping["Q"], mapping["Z"]),
            ("E", "T", "A")
        )

    def test_mapping_is_complete_permutation(self):
        mapping = fa.build_mapping("XXXX QQQ ZZ")

        self.assertEqual(sorted(mapping), list(cipher.ALPHABET))
        self.assertEqual(sorted(mapping.values()), list(cipher.ALPHABET))

    def test_decrypt_keeps_non_letters(self):
        mapping = fa.build_mapping("XXXX QQQ ZZ")

        self.assertEqual(fa.decrypt_with_mapping("XQ, Z! 42", mapping), "et, a! 42")

    def test_true_key_recovers_plaintext(self):
        key = cipher.generate_key(seed=9)
        text = SAMPLES["Cybersecurity note"]
        ciphertext = cipher.encrypt(text, key)
        true_mapping = {c: p for p, c in zip(cipher.ALPHABET, key)}

        self.assertEqual(
            fa.decrypt_with_mapping(ciphertext, true_mapping),
            text.lower()
        )

    def test_analyze_output(self):
        result = fa.analyze(cipher.encrypt(SAMPLES["Cybersecurity note"],
                                           cipher.generate_key(seed=2)))

        self.assertEqual(
            set(result),
            {"mapping", "plaintext", "cipher_frequencies",
             "cipher_order", "english_order", "score"}
        )


class TestManualOverrides(unittest.TestCase):

    def setUp(self):
        self.mapping = fa.build_mapping("XXXX QQQ ZZ")

    def test_override_swaps_letters(self):
        updated = fa.apply_overrides(self.mapping, {"Z": "E"})

        self.assertEqual(updated["Z"], "E")
        self.assertEqual(updated["X"], "A")   # X takes Z's old letter
        self.assertEqual(sorted(updated.values()), list(cipher.ALPHABET))

    def test_original_unchanged(self):
        fa.apply_overrides(self.mapping, {"Z": "E"})

        self.assertEqual(self.mapping["Z"], "A")

    def test_invalid_override_ignored(self):
        self.assertEqual(fa.apply_overrides(self.mapping, {"Z": "1"}), self.mapping)


class TestScoring(unittest.TestCase):

    english = SAMPLES["Cybersecurity note"]
    nonsense = "xqz jkv wmq zpl bfg vqm zzx qjx"

    def test_chi_squared(self):
        self.assertLess(fa.chi_squared_score(self.english),
                        fa.chi_squared_score(self.nonsense))
        self.assertEqual(fa.chi_squared_score("123"), float("inf"))

    def test_bigram_fitness(self):
        self.assertGreater(em.fitness(self.english), em.fitness(self.nonsense))
        self.assertEqual(em.fitness("a"), float("-inf"))

    def test_word_coverage(self):
        self.assertEqual(em.word_coverage("the cipher text"), 1.0)
        self.assertEqual(em.word_coverage(self.nonsense), 0.0)
        self.assertEqual(em.word_coverage(""), 0.0)


class TestSmartSolve(unittest.TestCase):

    def test_breaks_normal_length_text(self):
        text = SAMPLES["Cybersecurity note"]
        ciphertext = cipher.encrypt(text, cipher.generate_key(seed=5))
        mapping, plaintext, _ = fa.smart_solve(ciphertext, restarts=4, seed=1)

        self.assertGreaterEqual(letter_accuracy(plaintext, text), 95)
        self.assertEqual(sorted(mapping.values()), list(cipher.ALPHABET))

    def test_beats_single_letter_attack(self):
        text = SAMPLES["Frequency analysis (meta)"]
        ciphertext = cipher.encrypt(text, cipher.generate_key(seed=42))
        single = fa.analyze(ciphertext)["plaintext"]
        _, smart, _ = fa.smart_solve(ciphertext, restarts=4, seed=1)

        self.assertGreater(letter_accuracy(smart, text),
                           letter_accuracy(single, text))


if __name__ == "__main__":
    unittest.main()
