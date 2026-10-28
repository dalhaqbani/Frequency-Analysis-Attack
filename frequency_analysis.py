"""
frequency_analysis.py
---------------------
The core of the project: breaking a monoalphabetic substitution cipher using
frequency analysis, following the four steps in the project brief:

    1. Create a list of plaintext (English) letter frequencies, sorted.
    2. Create a list of ciphertext letter frequencies, sorted.
    3. Merge the two lists to build an estimated letter mapping.
    4. Use that mapping to produce an approximate decryption.

It also adds the pieces a real analyst needs: a scoring function to measure
how "English-like" a guess is, and manual mapping overrides so the user can
fix the letters the raw frequency guess gets wrong.
"""

import random
import string
from collections import Counter

import english_model  # English digram statistics, used to score candidates

ALPHABET = string.ascii_uppercase

# Standard English letter frequencies (%), most common first.
# Source: relative frequencies of letters in typical English text.
ENGLISH_FREQ = {
    "E": 12.70, "T": 9.06, "A": 8.17, "O": 7.51, "I": 6.97, "N": 6.75,
    "S": 6.33, "H": 6.09, "R": 5.99, "D": 4.25, "L": 4.03, "C": 2.78,
    "U": 2.76, "M": 2.41, "W": 2.36, "F": 2.23, "G": 2.02, "Y": 1.97,
    "P": 1.93, "B": 1.49, "V": 0.98, "K": 0.77, "J": 0.15, "X": 0.15,
    "Q": 0.10, "Z": 0.07,
}

# English letters ordered from most to least frequent: "ETAOINSHRDLU..."
ENGLISH_ORDER = [letter for letter, _ in
                 sorted(ENGLISH_FREQ.items(), key=lambda kv: kv[1], reverse=True)]


def letter_counts(text):
    """Count occurrences of each letter A-Z in the text (case-insensitive)."""
    text = text.upper()
    counts = Counter(ch for ch in text if ch in ALPHABET)
    # Ensure every letter is present, even with a zero count.
    return {letter: counts.get(letter, 0) for letter in ALPHABET}


def letter_frequencies(text):
    """Return each letter's frequency as a percentage of total letters."""
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return {letter: 0.0 for letter in ALPHABET}
    return {letter: (count / total) * 100 for letter, count in counts.items()}


def sorted_by_frequency(text):
    """Step 2: list of the ciphertext's letters, most frequent first.

    Letters that do not appear at all are dropped, since they give the
    attack no information.
    """
    counts = letter_counts(text)
    present = [(letter, c) for letter, c in counts.items() if c > 0]
    present.sort(key=lambda kv: kv[1], reverse=True)
    return [letter for letter, _ in present]


def build_mapping(ciphertext):
    """Steps 1-3: build an estimated cipher->plaintext letter mapping.

    Pair the most frequent ciphertext letter with 'E', the next with 'T',
    and so on down the English frequency order. Ciphertext letters that
    never appear are mapped to whatever English letters are left over, so
    the mapping is always a complete permutation.
    """
    cipher_order = sorted_by_frequency(ciphertext)

    mapping = {}
    used_plain = set()

    # Pair ranked ciphertext letters with ranked English letters.
    for cipher_letter, plain_letter in zip(cipher_order, ENGLISH_ORDER):
        mapping[cipher_letter] = plain_letter
        used_plain.add(plain_letter)

    # Fill in any ciphertext letters that didn't appear in the text.
    leftover_plain = [p for p in ENGLISH_ORDER if p not in used_plain]
    leftover_cipher = [c for c in ALPHABET if c not in mapping]
    for cipher_letter, plain_letter in zip(leftover_cipher, leftover_plain):
        mapping[cipher_letter] = plain_letter

    return mapping


def apply_overrides(mapping, overrides):
    """Apply manual user corrections while keeping the mapping a valid
    permutation.

    `overrides` is a dict of {cipher_letter: plain_letter}. When the user
    forces a cipher letter to a plaintext letter, whichever cipher letter
    currently holds that plaintext letter is swapped with it, so no two
    cipher letters ever map to the same plaintext letter.
    """
    mapping = dict(mapping)
    for cipher_letter, new_plain in overrides.items():
        cipher_letter = cipher_letter.upper()
        new_plain = new_plain.upper()
        if cipher_letter not in ALPHABET or new_plain not in ALPHABET:
            continue

        # Find which cipher letter currently maps to new_plain and swap.
        for other_cipher, plain in mapping.items():
            if plain == new_plain and other_cipher != cipher_letter:
                mapping[other_cipher] = mapping[cipher_letter]
                break
        mapping[cipher_letter] = new_plain
    return mapping


def decrypt_with_mapping(ciphertext, mapping):
    """Step 4: produce the approximate plaintext using the mapping.

    Decrypted letters are shown in lowercase so it is easy to see, at a
    glance, which letters have been guessed vs. any that are still raw.
    """
    result = []
    for ch in ciphertext.upper():
        if ch in mapping:
            result.append(mapping[ch].lower())
        else:
            result.append(ch)
    return "".join(result)


def chi_squared_score(text):
    """Measure how close the text's letter distribution is to English.

    Lower is better (0 would be a perfect match to the reference
    frequencies). This lets us rank candidate decryptions automatically.
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return float("inf")

    score = 0.0
    for letter in ALPHABET:
        observed = counts[letter]
        expected = ENGLISH_FREQ[letter] / 100 * total
        if expected > 0:
            score += (observed - expected) ** 2 / expected
    return score


def analyze(ciphertext):
    """Run the full automatic attack and return everything the GUI needs."""
    mapping = build_mapping(ciphertext)
    plaintext = decrypt_with_mapping(ciphertext, mapping)
    return {
        "mapping": mapping,
        "plaintext": plaintext,
        "cipher_frequencies": letter_frequencies(ciphertext),
        "cipher_order": sorted_by_frequency(ciphertext),
        "english_order": ENGLISH_ORDER,
        "score": chi_squared_score(plaintext),
    }


# ---------------------------------------------------------------------------
# Smart solver: automatic cipher breaking using BIGRAM (letter-pair) analysis.
#
# Single-letter frequency ranking (build_mapping) is only a *starting guess* and
# rarely correct on its own, because a short message's letter ranking never
# lines up perfectly with standard English. The reason it fails is that single
# letters ignore letter *order*: "S" and "C" have almost the same frequency, so
# single-letter analysis can't tell them apart — but "SE" is common and "CE" is
# not, so a pair (bigram) can.
#
# So we search for the mapping whose decryption best matches English LETTER-PAIR
# frequencies, by hill-climbing:
#
#   1. Start from the single-letter frequency guess.
#   2. Swap two letters in the mapping. Keep the swap if the decryption's bigram
#      fitness improves (english_model.fitness); otherwise undo it.
#   3. Repeat until no swap helps (a local optimum).
#   4. Restart several times from random mappings to escape bad local optima,
#      and keep the best result.
#
# The hill-climb optimises bigram fitness, but to choose between restarts we
# rank by real-word coverage first (a very strong signal, since the cipher keeps
# spaces), then by bigram fitness. That stops a wrong-but-plausible decryption
# from winning. The English bigram statistics come from Peter Norvig's Google
# Books analysis (see english_model.py); the solver itself is our own code.
# ---------------------------------------------------------------------------
def _mapping_from_list(key_list): #converts a key as a list into a dictionary that decrypt_with_mapping can use.
    """A key list (index = cipher letter A..Z, value = plaintext letter) -> dict."""
    return {ALPHABET[i]: key_list[i] for i in range(26)}


def _hill_climb(ciphertext, start_key, max_stale=1200): #takes a starting key and keeps improving it by swapping letters
    """One hill-climb: swap letters, keep improvements, until it stalls.

    Returns the best key list found on this run.
    """
    current = list(start_key)
    current_fit = english_model.fitness(
        decrypt_with_mapping(ciphertext, _mapping_from_list(current)))

    stale = 0
    while stale < max_stale:
        i, j = random.sample(range(26), 2)
        current[i], current[j] = current[j], current[i]   # try a swap
        new_fit = english_model.fitness(
            decrypt_with_mapping(ciphertext, _mapping_from_list(current)))
        if new_fit > current_fit: #if the pairs look more like english it keeps the swap
            current_fit = new_fit
            stale = 0
        else:
            current[i], current[j] = current[j], current[i]  # undo
            stale += 1
    return current


def smart_solve(ciphertext, restarts=12, seed=None):
    """Automatically break the cipher with bigram hill-climbing.

    Returns (mapping, plaintext, fitness). More restarts = more reliable.
    """
    if seed is not None:
        random.seed(seed)

    # First restart starts from the single-letter frequency guess; the rest
    # start from random mappings to explore different parts of the search space.
    unigram_key = [build_mapping(ciphertext)[c] for c in ALPHABET]

    best_key = None
    best_rank = (-1.0, float("-inf"))  # (word_coverage, bigram_fitness)

    for r in range(restarts):
        start = list(unigram_key) if r == 0 else random.sample(ALPHABET, 26)
        result = _hill_climb(ciphertext, start)
        plaintext = decrypt_with_mapping(ciphertext, _mapping_from_list(result))
        rank = (english_model.word_coverage(plaintext),
                english_model.fitness(plaintext))
        if rank > best_rank:
            best_rank = rank
            best_key = result

    mapping = _mapping_from_list(best_key)
    plaintext = decrypt_with_mapping(ciphertext, mapping)
    return mapping, plaintext, best_rank[1]


if __name__ == "__main__":
    from cipher import encrypt, generate_key

    sample = (
        "In cryptography frequency analysis is the study of the frequency "
        "of letters or groups of letters in a ciphertext. The method is used "
        "as an aid to breaking classical ciphers. Frequency analysis is based "
        "on the fact that in any given stretch of written language certain "
        "letters and combinations of letters occur with varying frequencies."
    )
    key = generate_key(seed=7)
    ct = encrypt(sample, key)
    result = analyze(ct)
    print("Ciphertext order:", result["cipher_order"])
    print("English   order :", result["english_order"])
    print("\nApproximate decryption:\n", result["plaintext"])
    print("\nChi-squared score (lower is better):", round(result["score"], 2))
