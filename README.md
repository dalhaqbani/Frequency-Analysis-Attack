# Frequency Analysis Attack — CYS401 Project (Idea 11)

A Python tool that breaks a **monoalphabetic substitution cipher** using
frequency analysis, with a Streamlit interface for demonstration.

## What it does

A substitution cipher replaces each letter with a fixed other letter. Because
each plaintext letter always becomes the *same* ciphertext letter, the
*frequencies* of the letters are preserved — only their labels change. English
has a very stable letter-frequency profile (E, T, A, O… are common; J, Q, X, Z
are rare), so by matching the ciphertext's frequency ranking to English's, we
can guess the key without ever knowing it.

The attack follows the four steps in the project brief:

1. List English letter frequencies, sorted (most → least common).
2. List the ciphertext's letter frequencies, sorted.
3. Merge the two lists into an estimated letter mapping.
4. Apply the mapping to produce an approximate decryption.

A **chi-squared score** rates how English-like each guess is, and a **manual
refinement** step lets the analyst fix the letters the raw guess gets wrong
(this is normal — frequency analysis gets you most of the way, then you finish
by hand using common words and letter pairs).

### Two levels of attack

1. **Single-letter frequency analysis** (`build_mapping`) — the exact method in
   the brief. Fast, but only a *starting guess*: on a real message it typically
   gets the common letters right and swaps several others, so the output is
   partly readable. This is the point of the exercise — it shows *why* simple
   substitution is weak, and *why* single-letter frequencies alone aren't
   enough.
2. **Smart solve** (`smart_solve`) — goes one level deeper, matching English
   **letter-pair (bigram)** frequencies instead of single letters. It
   hill-climbs toward the key (swap two letters, keep the swap if the
   decryption's bigram score improves, repeat), restarts several times to avoid
   dead ends, and keeps the result with the best real-word coverage. Single
   letters can't tell S from C because they have the same frequency — but "SE"
   is common and "CE" is not, so bigrams break the tie. This reliably reaches
   **~95–100%** on normal-length text; any leftover ambiguous letters are
   finished in the Manual Refinement tab. The solver is our own code; only the
   English bigram frequency numbers come from an external source (see below).

## Files

| File | Purpose |
|------|---------|
| `cipher.py` | Substitution cipher — generates the ciphertext to attack |
| `frequency_analysis.py` | The attack engine (the four steps + smart solver) |
| `english_model.py` | English digram stats + common-word list, used to score guesses |
| `sample_texts.py` | Ready-made demo texts |
| `app.py` | Streamlit GUI (3 tabs: create → attack → refine) |
| `requirements.txt` | Dependencies |

## Credits / references

- The English **letter and letter-pair (digram) frequency statistics** in
  `english_model.py` come from **Peter Norvig's analysis of the Google Books
  corpus** (<http://norvig.com/mayzner.html>). These are published frequency
  figures about the English language — reference data, not code.
- Everything else — the single-letter frequency method, the bigram
  hill-climbing solver, the word-coverage ranking, the scoring, and the GUI —
  is our own work.

## Setup & run

```bash
pip install -r requirements.txt
streamlit run app.py
```

You can also run the engine from the command line to see it work without the GUI:

```bash
python cipher.py              # cipher self-test
python frequency_analysis.py  # full attack on a sample
```

## How to demo (suggested flow)

1. **Create Ciphertext** tab → pick the "Frequency analysis (meta)" sample →
   **Encrypt**.
2. **Automatic Attack** tab → show the two frequency rankings side by side, the
   bar chart, and the approximate decryption. Point out the "% letters correct"
   metric.
3. **Manual Refinement** tab → fix the few swapped letters (watch the
   chi-squared score drop and the text turn readable).

## Notes / limitations

- Frequency analysis needs enough text; very short messages don't give the
  counts time to settle, so expect more manual fixing there.
- It targets classical substitution ciphers. Modern ciphers (AES etc.) are
  specifically designed so that frequency analysis gives no information — this
  project is about *why* the classical ones fail, which is the security lesson.

## Team

- Member 1 — cipher & attack engine
- Member 2 — frequency model, scoring & testing
- Member 3 — Streamlit interface, integration & report
