# Reproduce the synthetic baseline

The model lives in [references/hamza-model](../references/hamza-model), a Git submodule pointing at Hamza Kittaneh's commit `63b6728ac48b8ef733e98085a1fd69e4e4b4bf26`. Work from the PocketFilter repository root with Git, Python 3.11, NumPy 1.26.4 and Matplotlib 3.8.0. These are the versions used for this reproduction; upstream also records its original environment in requirements.txt.

```powershell
git submodule update --init -- references/hamza-model
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy==1.26.4 matplotlib==3.8.0
.\.venv\Scripts\python.exe software/verify_baseline.py references/hamza-model local-intake/replay
```

On macOS or Linux use `.venv/bin/python` for the last two commands. A new repository checkout can include the model immediately with `git clone --recurse-submodules https://github.com/Team-12R/PocketFilter.git`.

The verifier extracts the five executable modules at the pinned commit into a temporary directory. It runs the upstream simulation, checks all three rows against the expected exported scores and spans, then runs four boundary checks. A mismatch exits nonzero. A successful run writes results.csv and pocketfilter_test_results.png. Use a different destination to retain multiple runs. The fixture generator uses full-precision in-memory samples for the simulation; its inspection CSVs round to four decimals.

See the [call graph and contracts](../docs/design/software.md) for the computational and verification routines. Upstream contributions retain their original Git history.
