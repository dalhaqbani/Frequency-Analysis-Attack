"""
cipher.py
---------
Monoalphabetic substitution cipher used to PRODUCE the ciphertext that the
frequency-analysis attack will try to break. This is the "target" the attack
works against so the tool can be demonstrated end-to-end.

A monoalphabetic substitution cipher replaces every plaintext letter with a
fixed different letter. The key is just a permutation of the 26 letters of
the alphabet.
"""

import random
import string

ALPHABET = string.ascii_uppercase  # "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_key(seed=None):
    """Return a random substitution key (a shuffled 26-letter alphabet).

    Example: key[0] is the letter that 'A' maps to.
    """
    if seed is not None:
        random.seed(seed)
    letters = list(ALPHABET)
    random.shuffle(letters)
    return "".join(letters)


def _build_tables(key):
    """Build encryption and decryption translation tables from a key."""
    key = key.upper()
    if sorted(key) != sorted(ALPHABET):
        raise ValueError("Key must be a permutation of the 26 letters A-Z.")
    encrypt_table = str.maketrans(ALPHABET, key)
    decrypt_table = str.maketrans(key, ALPHABET)
    return encrypt_table, decrypt_table


def encrypt(plaintext, key):
    """Encrypt plaintext with the given substitution key.

    Non-letters (spaces, punctuation, digits) are left unchanged so the
    structure of the message is preserved — which is exactly what makes a
    frequency attack possible.
    """
    encrypt_table, _ = _build_tables(key)
    return plaintext.upper().translate(encrypt_table)


def decrypt(ciphertext, key):
    """Decrypt ciphertext when the real key is known (ground truth)."""
    _, decrypt_table = _build_tables(key)
    return ciphertext.upper().translate(decrypt_table)


if __name__ == "__main__":
    # Quick self-test
    k = generate_key(seed=42)
    msg = "The quick brown fox jumps over the lazy dog."
    ct = encrypt(msg, k)
    print("Key       :", k)
    print("Plaintext :", msg.upper())
    print("Ciphertext:", ct)
    print("Decrypted :", decrypt(ct, k))
