"""
app.py
------
Streamlit interface for the Frequency Analysis Attack tool (CYS401 Idea 11).

Two tabs:
    1. Create Ciphertext  - encrypt a sample or your own text, to attack.
    2. Automatic Attack   - run frequency analysis and see the guess + scores.

Run with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

import cipher
import frequency_analysis as fa
from sample_texts import SAMPLES

st.set_page_config(page_title="Frequency Analysis Attack", layout="wide")

# ---------------------------------------------------------------------------
# Session state: persist data as the user moves between tabs.
# ---------------------------------------------------------------------------
if "ciphertext" not in st.session_state:
    st.session_state.ciphertext = ""
if "true_key" not in st.session_state:
    st.session_state.true_key = ""

st.title("Frequency Analysis Attack")
st.caption(
    "Break a monoalphabetic substitution cipher by comparing ciphertext letter "
    "frequencies to the frequencies of letters in English.  •  CYS401 Project — Idea 11"
)

tab_create, tab_attack = st.tabs(
    ["1 · Create Ciphertext", "2 · Automatic Attack"]
)

# ===========================================================================
# TAB 1 — Create the ciphertext to attack
# ===========================================================================
with tab_create:
    st.subheader("Produce a ciphertext")
    st.write(
        "Pick a sample or paste your own text, then encrypt it with a random "
        "substitution key. The attack in the next tab does **not** use this key — "
        "it only sees the ciphertext."
    )

    col1, col2 = st.columns(2)
    with col1:
        choice = st.selectbox("Sample text", ["(type my own)"] + list(SAMPLES.keys()))
        default_text = "" if choice == "(type my own)" else SAMPLES[choice]
        plaintext = st.text_area("Plaintext", value=default_text, height=200)

    with col2:
        seed_on = st.checkbox("Use a fixed random seed (reproducible key)", value=True)
        seed = st.number_input("Seed", value=42, step=1) if seed_on else None

        if st.button("Encrypt", type="primary"):
            if plaintext.strip():
                key = cipher.generate_key(seed=int(seed) if seed is not None else None)
                st.session_state.true_key = key
                st.session_state.ciphertext = cipher.encrypt(plaintext, key)
                st.success("Ciphertext generated. Go to the Automatic Attack tab.")
            else:
                st.warning("Enter some text first.")

        # Allow pasting a ciphertext directly (no known key).
        st.divider()
        st.write("…or paste a ciphertext you already have:")
        pasted = st.text_area("Ciphertext input", height=120, key="pasted_ct")
        if st.button("Use pasted ciphertext"):
            if pasted.strip():
                st.session_state.ciphertext = pasted.upper()
                st.session_state.true_key = ""  # unknown
                st.success("Loaded. Go to the Automatic Attack tab.")

    if st.session_state.ciphertext:
        st.divider()
        st.text_area("Current ciphertext", value=st.session_state.ciphertext,
                     height=150, disabled=True)
        if st.session_state.true_key:
            st.caption(f"(Hidden ground-truth key, for checking: `{st.session_state.true_key}`)")

# ===========================================================================
# TAB 2 — Automatic frequency-analysis attack
# ===========================================================================
with tab_attack:
    st.subheader("Automatic attack")

    if not st.session_state.ciphertext:
        st.info("Create or paste a ciphertext in tab 1 first.")
    else:
        result = fa.analyze(st.session_state.ciphertext)

        # --- The four steps from the brief, shown explicitly ---
        st.markdown("**Steps 2 & 1 — letters sorted by frequency**")
        step_df = pd.DataFrame({
            "Rank": range(1, 27),
            "Ciphertext (most→least frequent)":
                (result["cipher_order"] + [""] * 26)[:26],
            "English (most→least frequent)": result["english_order"],
        })
        st.dataframe(step_df, hide_index=True, use_container_width=True)

        st.markdown("**Step 3 — estimated mapping** (cipher letter → guessed plaintext)")
        mapping = result["mapping"]
        map_df = pd.DataFrame(
            [{"Cipher": c, "→ Plain": mapping[c]} for c in fa.ALPHABET]
        )
        st.dataframe(map_df.set_index("Cipher").T, use_container_width=True)

        # --- Frequency bar chart: ciphertext vs. English ---
        st.markdown("**Letter frequencies: ciphertext vs. English**")
        chart_df = pd.DataFrame({
            "Ciphertext %": result["cipher_frequencies"],
            "English %": fa.ENGLISH_FREQ,
        })
        st.bar_chart(chart_df)

        # --- Step 4: approximate decryption ---
        st.markdown("**Step 4 — approximate decryption**")
        st.text_area("Automatic guess", value=result["plaintext"],
                     height=180, disabled=True)

        col_a, col_b = st.columns(2)
        col_a.metric("Chi-squared score (lower = more English-like)",
                     round(result["score"], 1))
        if st.session_state.true_key:
            true_pt = cipher.decrypt(st.session_state.ciphertext,
                                     st.session_state.true_key).lower()
            correct = sum(1 for a, b in zip(result["plaintext"], true_pt) if a == b)
            total = sum(1 for ch in true_pt if ch.isalpha())
            letters_right = sum(
                1 for a, b in zip(result["plaintext"], true_pt)
                if a == b and a.isalpha()
            )
            pct = (letters_right / total * 100) if total else 0
            col_b.metric("Letters correct vs. true plaintext", f"{pct:.0f}%")

        st.info(
            "Pure single-letter frequency analysis rarely cracks a message "
            "perfectly on the first pass — especially short ones. The rare "
            "letters (J, Q, X, Z) and close-frequency letters often get "
            "swapped. Use **Smart solve** below to finish the break."
        )

        st.divider()
        st.markdown("### Smart solve (automatic)")
        st.caption(
            "Goes beyond single letters: searches for the key whose decryption "
            "best matches English **letter-pair** (bigram) frequencies, by "
            "hill-climbing. Runs several times and keeps the result with the "
            "best real-word coverage."
        )
        if st.button("Crack it automatically", type="primary"):
            with st.spinner("Searching for the key…"):
                mapping, solved, fit = fa.smart_solve(st.session_state.ciphertext)
            st.session_state.smart_plaintext = solved
            st.session_state.smart_mapping = mapping

        if st.session_state.get("smart_plaintext"):
            st.text_area("Smart-solve result", value=st.session_state.smart_plaintext,
                         height=180, disabled=True)
            if st.session_state.true_key:
                true_pt = cipher.decrypt(st.session_state.ciphertext,
                                         st.session_state.true_key).upper()
                solved_up = st.session_state.smart_plaintext.upper()
                total = sum(1 for ch in true_pt if ch.isalpha())
                right = sum(1 for a, b in zip(solved_up, true_pt)
                            if a == b and a.isalpha())
                st.metric("Letters correct vs. true plaintext",
                          f"{(right / total * 100) if total else 0:.0f}%")
