# How to resume the pipeline

Every agent writes its own validated file to `data/coded/`, so finished work is never lost.
Run from the project folder.

1. **Rebuild inputs if the container is new** (raw data and batches are not committed):
   ```bash
   python3 -I scripts/fetch_data.py .
   python3 -I scripts/01_fetch_nsf.py
   python3 -I scripts/02_fetch_usaspending.py
   python3 -I scripts/03_make_batches.py    # deterministic batches and reliability sample
   ```
   API results can change slightly over time; compare the new `data/sources.lock.csv` hashes
   with the committed ones. If they differ, the batch contents may differ, so check before mixing
   old and new tags.
2. **See what is pending:** `python3 -I scripts/status.py --json`.
3. **Tag:** launch `scripts/workflows/tag.js` with
   `args: {"jobs": [{"kind": "nsf", "pass": "main", "batch": "batch_NNNN", "model": "sonnet"}, ...]}`.
   - Use `{"kind": "nsf", "pass": "reference", "batch": ...}` (no model, so the default reference
     model) for the batches listed in `data/coded/nsf_reliability_batches.txt`.
   - Use `{"kind": "ojjdp", "batch": ..., "model": "sonnet"}` for mentoring grants.
4. **Reliability:** `python3 -I scripts/04_reliability.py`.
5. **Analysis:** `python3 -I scripts/05_analysis.py`.
6. Commit `data/coded/` and `output/` after each wave (`git status` first: `data/raw/` and
   `data/interim/` must never be staged).
