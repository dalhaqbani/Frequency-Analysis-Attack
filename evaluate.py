"""
evaluate.py
-----------
Accuracy experiments for the report's Results section.

Each experiment encrypts known English text with a random substitution key,
attacks the ciphertext, and compares the result with the original text.

Run with:  python evaluate.py      (takes a few minutes: the smart solver is slow)
"""

import cipher
import frequency_analysis as fa
from sample_texts import SAMPLES

KEY_SEEDS = range(1, 11)          # 10 random keys per sample

# A short message (94 letters) to show how the attacks behave on short text.
# It is kept here because the interface now rejects texts under 150 letters.
SHORT_TEXT = (
    "Meet me at the old library tomorrow at noon and bring the documents "
    "we discussed. Do not tell anyone about this plan."
)

# The texts used in Experiment 1: the built-in samples plus the short message.
TEST_TEXTS = dict(SAMPLES)
TEST_TEXTS["Short message"] = SHORT_TEXT

# An independent test text, not used anywhere else in the project, so results
# do not depend on the built-in samples or on the solver's common-word list.
INDEPENDENT_TEXT = (
    "Long before computers existed, people relied on secret writing to "
    "protect letters, military orders and trade secrets. Kings, merchants "
    "and spies all needed a way to send information that would remain "
    "private even if the messenger was captured. The simplest solution was "
    "to swap each letter of the message for another letter, using a key that "
    "only the sender and the receiver knew. This kind of system is called a "
    "monoalphabetic substitution cipher, and for many centuries it was "
    "considered almost impossible to break. In the ninth century, the scholar "
    "Al-Kindi, who worked in Baghdad, wrote a book that changed the history of "
    "secret writing. He noticed that in any long piece of text some letters "
    "are used much more often than others. If a cipher only replaces each "
    "letter with a different symbol, those patterns do not disappear. They "
    "simply move to new symbols. By counting the symbols in a secret message "
    "and comparing the counts with the normal pattern of the language, a "
    "careful reader could start to guess which symbol stood for which letter. "
    "The method became famous in Europe many years later. In the sixteenth "
    "century, letters written in cipher by Mary, Queen of Scots, were "
    "intercepted and handed to an expert code breaker. By studying how often "
    "each symbol appeared, he was able to recover the hidden messages, which "
    "revealed a plot against Queen Elizabeth. The decrypted letters were used "
    "as evidence at her trial, and the result showed how dangerous it can be "
    "to trust a weak cipher. Today, the lesson of frequency analysis is still "
    "important for anyone who designs or uses security systems. A good cipher "
    "must hide every statistical pattern of the original data, not only the "
    "shape of the letters."
)


def letter_accuracy(guess, truth):
    """Percentage of the letters in truth that guess decrypted correctly."""
    pairs = [(g, t) for g, t in zip(guess.upper(), truth.upper()) if t.isalpha()]
    if not pairs:
        return 0.0
    return 100 * sum(g == t for g, t in pairs) / len(pairs)


def count_letters(text):
    return sum(ch.isalpha() for ch in text)


def letter_window(text, start, n):
    """The part of text holding n letters, starting at letter number start."""
    positions = [i for i, ch in enumerate(text) if ch.isalpha()]
    end = min(start + n, len(positions)) - 1
    return text[positions[start]:positions[end] + 1]


def attack(text, key_seed, solver_seed=1):
    """Encrypt text, run both attacks, and return their letter accuracies."""
    ciphertext = cipher.encrypt(text, cipher.generate_key(key_seed))
    single = fa.analyze(ciphertext)["plaintext"]
    _, smart, _ = fa.smart_solve(ciphertext, seed=solver_seed)
    return letter_accuracy(single, text), letter_accuracy(smart, text)


def average(values):
    return sum(values) / len(values)


def experiment_samples():
    print("Experiment 1: single-letter attack vs smart solve on the test texts")
    print(f"({len(KEY_SEEDS)} random keys per sample, key seeds "
          f"{KEY_SEEDS.start}-{KEY_SEEDS.stop - 1})\n")
    print(f"{'Sample':<28}{'Letters':>8}{'Single':>9}{'Smart avg':>11}"
          f"{'Smart min':>11}{'Runs >=95%':>12}")
    print("-" * 79)

    for name, text in TEST_TEXTS.items():
        results = [attack(text, seed, solver_seed=seed) for seed in KEY_SEEDS]
        single = [r[0] for r in results]
        smart = [r[1] for r in results]
        good = sum(s >= 95 for s in smart)
        print(f"{name:<28}{count_letters(text):>8}{average(single):>8.1f}%"
              f"{average(smart):>10.1f}%{min(smart):>10.1f}%"
              f"{good:>7}/{len(smart)}")


def experiment_length(windows=3):
    total = count_letters(INDEPENDENT_TEXT)
    lengths = [50, 100, 200, 400, 800, total]

    print("\nExperiment 2: accuracy vs ciphertext length (independent text, key seed 1)")
    print(f"(average over {windows} evenly spaced parts of the text; "
          f"the full {total}-letter text is one part)\n")
    print(f"{'Letters':>8}{'Single':>9}{'Smart':>9}")
    print("-" * 26)

    for n in lengths:
        if n == total:
            starts = [0]
        else:
            starts = [round(k * (total - n) / (windows - 1)) for k in range(windows)]
        results = [attack(letter_window(INDEPENDENT_TEXT, s, n), key_seed=1)
                   for s in starts]
        print(f"{n:>8}{average([r[0] for r in results]):>8.1f}%"
              f"{average([r[1] for r in results]):>8.1f}%")


def experiment_chi_squared(sample="Frequency analysis (meta)", key_seed=42):
    """Fix one wrong letter at a time (most frequent first, using the known
    key, as an analyst would after recognising a word) and track how the
    letter accuracy and the chi-squared score change."""
    text = SAMPLES[sample]
    key = cipher.generate_key(key_seed)
    ciphertext = cipher.encrypt(text, key)
    true_mapping = {c: p for p, c in zip(cipher.ALPHABET, key)}
    mapping = fa.build_mapping(ciphertext)

    print(f"\nExperiment 3: chi-squared score during manual correction "
          f"({sample}, key seed {key_seed})\n")
    print(f"{'Corrections':>12}{'Accuracy':>10}{'Chi-squared':>13}")
    print("-" * 35)

    step = 0
    while True:
        plaintext = fa.decrypt_with_mapping(ciphertext, mapping)
        print(f"{step:>12}{letter_accuracy(plaintext, text):>9.1f}%"
              f"{fa.chi_squared_score(plaintext):>13.1f}")
        wrong = [c for c in fa.sorted_by_frequency(ciphertext)
                 if mapping[c] != true_mapping[c]]
        if not wrong:
            break
        mapping = fa.apply_overrides(mapping, {wrong[0]: true_mapping[wrong[0]]})
        step += 1

    print(f"\nChi-squared of the true plaintext: {fa.chi_squared_score(text):.1f}")


if __name__ == "__main__":
    experiment_samples()
    experiment_length()
    experiment_chi_squared()
