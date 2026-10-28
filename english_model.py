"""
english_model.py
----------------
English letter-pair (bigram/digram) statistics, used to SCORE how English-like
a candidate decryption is.

Single-letter frequencies tell you which letters are common, but not which
letters sit *next to* each other. "TH", "HE", "IN", "QU" are extremely common
in English; "QZ" or "JX" essentially never occur. Scoring letter PAIRS tells a
good decryption from a bad one far more reliably than single letters can, which
is what lets the solver crack a substitution cipher automatically.

DIGRAM_PCT is a 26x26 table of English digram frequencies (as percentages).
Rows = first letter, columns = second letter, both ordered by the single-letter
frequency order in ORDER. So DIGRAM_PCT[0][0] is the frequency of "EE".

Data source: Peter Norvig's analysis of the Google Books corpus
(http://norvig.com/mayzner.html), via the public-domain frequency tables in the
cipher-solver package. Frequency counts are facts about English, not code.
"""

import math

ORDER = "ETAOINSRHLDCUMFPGWYBVKXJQZ" #sorted from most common to least common
_INDEX = {letter: i for i, letter in enumerate(ORDER)}

# 26x26 English digram frequencies in percent (rows/cols follow ORDER).
DIGRAM_PCT = [
    [0.3780, 0.4130, 0.6880, 0.0730, 0.1830, 1.4540, 1.3390, 2.0480, 0.0260, 0.5300, 1.1680, 0.4770, 0.0310, 0.3740, 0.1630, 0.1720, 0.1200, 0.1170, 0.1440, 0.0270, 0.2550, 0.0160, 0.2140, 0.0050, 0.0570, 0.0050],
    [1.2050, 0.1710, 0.5300, 1.0410, 1.3430, 0.0100, 0.3370, 0.4260, 3.5560, 0.0980, 0.0010, 0.0260, 0.2550, 0.0260, 0.0060, 0.0040, 0.0020, 0.0820, 0.2270, 0.0030, 0.0010, 0.0000, 0.0000, 0.0000, 0.0000, 0.0040],
    [0.0120, 1.4870, 0.0030, 0.0050, 0.3160, 1.9850, 0.8710, 1.0750, 0.0140, 1.0870, 0.3680, 0.4480, 0.1190, 0.2850, 0.0740, 0.2030, 0.2050, 0.0600, 0.2170, 0.2300, 0.2050, 0.1050, 0.0190, 0.0120, 0.0020, 0.0120],
    [0.0390, 0.4420, 0.0570, 0.2100, 0.0880, 1.7580, 0.2900, 1.2770, 0.0210, 0.3650, 0.1950, 0.1660, 0.8700, 0.5460, 1.1750, 0.2240, 0.0940, 0.3300, 0.0360, 0.0970, 0.1780, 0.0640, 0.0190, 0.0070, 0.0010, 0.0030],
    [0.3850, 1.1230, 0.2860, 0.8350, 0.0230, 2.4330, 1.1280, 0.3150, 0.0020, 0.4320, 0.2960, 0.6990, 0.0170, 0.3180, 0.2030, 0.0890, 0.2550, 0.0010, 0.0000, 0.0990, 0.2880, 0.0430, 0.0220, 0.0010, 0.0110, 0.0640],
    [0.6920, 1.0410, 0.3470, 0.4650, 0.3390, 0.0730, 0.5090, 0.0090, 0.0110, 0.0640, 1.3520, 0.4160, 0.0790, 0.0280, 0.0670, 0.0060, 0.9530, 0.0060, 0.0980, 0.0040, 0.0520, 0.0520, 0.0030, 0.0110, 0.0060, 0.0040],
    [0.9320, 1.0530, 0.2180, 0.3980, 0.5500, 0.0090, 0.4050, 0.0060, 0.3150, 0.0560, 0.0050, 0.1550, 0.3110, 0.0650, 0.0170, 0.1910, 0.0020, 0.0240, 0.0570, 0.0080, 0.0010, 0.0390, 0.0000, 0.0000, 0.0070, 0.0000],
    [1.8540, 0.3620, 0.6860, 0.7270, 0.7280, 0.1600, 0.3970, 0.1210, 0.0150, 0.0860, 0.1890, 0.1210, 0.1280, 0.1750, 0.0320, 0.0420, 0.1000, 0.0130, 0.2480, 0.0270, 0.0690, 0.0970, 0.0010, 0.0010, 0.0010, 0.0010],
    [3.0750, 0.1300, 0.9260, 0.4850, 0.7630, 0.0260, 0.0150, 0.0840, 0.0010, 0.0130, 0.0030, 0.0010, 0.0740, 0.0130, 0.0020, 0.0010, 0.0000, 0.0050, 0.0500, 0.0040, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.8290, 0.1240, 0.5280, 0.3870, 0.6240, 0.0060, 0.1420, 0.0100, 0.0020, 0.5770, 0.2530, 0.0120, 0.1350, 0.0230, 0.0530, 0.0190, 0.0060, 0.0130, 0.4250, 0.0070, 0.0350, 0.0200, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.7650, 0.0030, 0.1510, 0.1880, 0.4930, 0.0080, 0.1260, 0.0850, 0.0050, 0.0320, 0.0430, 0.0030, 0.1480, 0.0180, 0.0030, 0.0020, 0.0310, 0.0080, 0.0500, 0.0030, 0.0190, 0.0000, 0.0000, 0.0050, 0.0010, 0.0000],
    [0.6510, 0.4610, 0.5380, 0.7940, 0.2810, 0.0010, 0.0230, 0.1490, 0.5980, 0.1490, 0.0020, 0.0830, 0.1630, 0.0030, 0.0010, 0.0010, 0.0010, 0.0000, 0.0420, 0.0010, 0.0000, 0.1180, 0.0000, 0.0000, 0.0050, 0.0010],
    [0.1470, 0.4050, 0.1360, 0.0110, 0.1010, 0.3940, 0.4540, 0.5430, 0.0010, 0.3460, 0.0910, 0.1880, 0.0010, 0.1380, 0.0190, 0.1360, 0.1280, 0.0000, 0.0050, 0.0890, 0.0030, 0.0050, 0.0040, 0.0010, 0.0000, 0.0020],
    [0.7930, 0.0010, 0.5650, 0.3370, 0.3180, 0.0090, 0.0930, 0.0030, 0.0010, 0.0050, 0.0010, 0.0040, 0.1150, 0.0960, 0.0040, 0.2390, 0.0010, 0.0010, 0.0620, 0.0900, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.2370, 0.0820, 0.1640, 0.4880, 0.2850, 0.0000, 0.0060, 0.2130, 0.0000, 0.0650, 0.0000, 0.0010, 0.0960, 0.0010, 0.1460, 0.0000, 0.0010, 0.0000, 0.0090, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.4780, 0.1060, 0.3240, 0.3610, 0.1230, 0.0010, 0.0550, 0.4740, 0.0940, 0.2630, 0.0010, 0.0010, 0.1050, 0.0160, 0.0010, 0.1370, 0.0000, 0.0010, 0.0120, 0.0010, 0.0000, 0.0010, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.3850, 0.0150, 0.1480, 0.1320, 0.1520, 0.0660, 0.0510, 0.1970, 0.2280, 0.0610, 0.0030, 0.0000, 0.0860, 0.0100, 0.0010, 0.0000, 0.0250, 0.0010, 0.0260, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.3610, 0.0070, 0.3850, 0.2220, 0.3740, 0.0790, 0.0350, 0.0310, 0.3790, 0.0150, 0.0040, 0.0010, 0.0010, 0.0010, 0.0020, 0.0010, 0.0000, 0.0000, 0.0020, 0.0010, 0.0000, 0.0010, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.0930, 0.0170, 0.0160, 0.1500, 0.0290, 0.0130, 0.0970, 0.0080, 0.0010, 0.0150, 0.0070, 0.0140, 0.0010, 0.0240, 0.0010, 0.0250, 0.0030, 0.0030, 0.0000, 0.0040, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0020],
    [0.5760, 0.0170, 0.1460, 0.1950, 0.1070, 0.0020, 0.0460, 0.1120, 0.0010, 0.2330, 0.0020, 0.0020, 0.1850, 0.0030, 0.0000, 0.0010, 0.0000, 0.0000, 0.1760, 0.0110, 0.0040, 0.0000, 0.0000, 0.0230, 0.0000, 0.0000],
    [0.8250, 0.0000, 0.1400, 0.0710, 0.2700, 0.0000, 0.0010, 0.0010, 0.0000, 0.0000, 0.0000, 0.0000, 0.0020, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0050, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.2140, 0.0010, 0.0170, 0.0060, 0.0980, 0.0510, 0.0480, 0.0030, 0.0030, 0.0110, 0.0010, 0.0000, 0.0030, 0.0020, 0.0020, 0.0010, 0.0030, 0.0020, 0.0060, 0.0010, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.0220, 0.0470, 0.0300, 0.0030, 0.0390, 0.0000, 0.0000, 0.0000, 0.0040, 0.0010, 0.0000, 0.0260, 0.0050, 0.0000, 0.0020, 0.0670, 0.0000, 0.0000, 0.0030, 0.0000, 0.0020, 0.0000, 0.0030, 0.0000, 0.0000, 0.0000],
    [0.0520, 0.0000, 0.0260, 0.0540, 0.0030, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0590, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.1480, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [0.0500, 0.0000, 0.0250, 0.0070, 0.0120, 0.0000, 0.0000, 0.0000, 0.0010, 0.0010, 0.0000, 0.0000, 0.0020, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0020, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0030],
]

# Build a {"AB": log-probability} lookup once, with a floor for pairs that
# essentially never appear, so an impossible pair is heavily penalised but not
# fatal.
_FLOOR = math.log(1e-7) #score for pairs that never happen
BIGRAM_LOGPROB = {}
for _i, _a in enumerate(ORDER): # _i row, _a first letter
    for _j, _b in enumerate(ORDER):  #_j column, _b second letter
        _pct = DIGRAM_PCT[_i][_j] #look up pair's %
        BIGRAM_LOGPROB[_a + _b] = math.log(_pct / 100.0) if _pct > 0 else _FLOOR #store the pair's log score


def fitness(text): # takes any text and returns a number on how english like are its letter pairs
    """Average English-ness of TEXT (higher = more English-like).

    Sum the log-probability of every adjacent letter pair, then divide by the
    number of pairs so the score does not depend on text length.
    """
    letters = [c for c in text.upper() if c.isalpha()]
    if len(letters) < 2:
        return float("-inf")
    total = 0.0
    pairs = 0
    for a, b in zip(letters, letters[1:]): #walks through every adjacent pair
        total += BIGRAM_LOGPROB.get(a + b, _FLOOR) #gives a score to the pair
        pairs += 1
    return total / pairs


if __name__ == "__main__":
    good = "the quick brown fox jumps over the lazy dog"
    bad = "xqz jkv wmq zpl bfg nrt kxz vqm"
    print("English  fitness:", round(fitness(good), 3))
    print("Nonsense fitness:", round(fitness(bad), 3))


# ---------------------------------------------------------------------------
# Common English words, used to pick the best solve among several random runs.
#
# Digram scores alone can be fooled: a wrong decryption may still contain common
# letter pairs. But because the cipher preserves spaces, a correct solve turns
# almost every token into a real English word, while a wrong one does not. So
# counting how much of the text is covered by real words is a much stronger
# signal for choosing the best candidate.
# ---------------------------------------------------------------------------
COMMON_WORDS = frozenset("""
the be to of and a in that have i it for not on with he as you do at this but his
by from they we say her she or an will my one all would there their what so up out
if about who get which go me when make can like time no just him know take people
into year your good some could them see other than then now look only come its over
think also back after use two how our work first well way even new want because any
these give day most us is are was were been has had did said get go went make made
know knew take took see saw come came want find each she many then them these so some
her him his how man new now old see two way who boy did its let put end why try god
water long little very after word called just where through much before line right
too mean old any same tell does set three must state high such follow act why ask men
change went light kind off need house picture again change point year live me back
give most very after thing our just name good sentence man think say great where help
through line before turn cause same mean differ move right picture again change off
play spell air away animal house point page letter mother answer found study still
learn should america world high every near add food between own below country plant
last school father keep tree never start city earth eye light thought head under
story saw left few while along might close something seem next hard open example
begin life always those both paper together got group often run important until
children side feet car mile night walk white sea began grow took river four carry
information security system data network computer attack cipher message letter
frequency analysis text english language method used library documents discussed
""".split())


def word_coverage(text): #another check, checks what fraction of the text  is real english words
    """Fraction of letters that fall inside recognised common English words.

    Splits on spaces/punctuation, then for each token checks membership in
    COMMON_WORDS. Returns matched-letters / total-letters (0.0 to 1.0).
    Higher = more of the text reads as real English words.
    """
    import re
    tokens = re.findall(r"[a-z]+", text.lower()) #split the text into words
    if not tokens:
        return 0.0
    total = sum(len(t) for t in tokens) #count total letters, count letters that sit inside a recognized common word, and return ratio
    matched = sum(len(t) for t in tokens if t in COMMON_WORDS)
    return matched / total if total else 0.0
