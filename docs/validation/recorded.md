# Recorded-waveform validation

Run these commands from the repository root. Keep recordings and per-read outputs under `local-intake/`. Both experiments use the same median-of-three filter, per-waveform population z-score and band-constrained L1 matcher as the golden model.

## Recorded nanopore control

The team’s SquiggleFilter import includes multi-read FAST5 files acquired by the original laboratory from its lambda control. The replay conditions measured current directly. Select the first multi-read file by the exact name below. Sort its read-group names, use the first group's 64-sample prefix as the reference, and score 256-sample prefixes from the next eight distinct reads at width 8. Each prefix starts at raw sample zero. Convert ADC counts to pA using the read's channel offset, range and digitisation, then condition and quantize to signed 16-bit codes. This fixed selection exercises file ingestion and arithmetic. The eight queries share one acquisition file and have no independent binary match labels. [Archive provenance and data description](https://github.com/Team-12R/SquiggleFilter/blob/21558e9701141c93c28a9f9c9c0316d2a50c5dfb/data/README.md)

```sh
# REF is a checkout of Team-12R/SquiggleFilter at 21558e9701141c93c28a9f9c9c0316d2a50c5dfb
mkdir -p local-intake/recorded hardware/build
file=FAL11227_e2243762ddcab66a4299cc8b21f76b3f66c41f01_0.fast5
python -m software.recorded.fast5_replay "$REF/data/lambda/fast5/$file" local-intake/recorded/lambda-vectors.txt
c++ -O2 -std=c++17 hardware/hls/{sdtw,testbench}.cpp -o hardware/build/check-native
hardware/build/check-native local-intake/recorded/lambda-vectors.txt
```

The adapter requires h5py and prints the SHA-256 and selected group identifiers. Source SHA-256 was `b18f9c90168f40fcde7dfa2c207c395848d7ed6fb44074a7256758ad526d0b06`. All eight four-word results agreed in native C++ and Python. The first returned status 0, distance 29,344 and inclusive indices 124–179.

## Labeled waveform evaluation

ECG200 provides an independent exercise of reference selection, calibration and held-out scoring on recorded electrical waveforms. Its 200 heartbeats contain two labels. The published 100/100 train/test split is preserved. The first training waveform (class `-1`) is the single reference. The other 99 train the threshold. The evaluation uses all 96 samples, band half-width 4, and a positive prediction at distance ≤ threshold. Calibration evaluates attainable thresholds and maximizes balanced accuracy, breaking ties at the lowest threshold. The test set is scored once with the frozen settings. Subject identifiers are unavailable in these files, so subject independence is unknown. [Dataset and archive download](https://www.timeseriesclassification.com/description.php?Dataset=ECG200)

```sh
# Extract ECG200_TRAIN.ts and ECG200_TEST.ts from the archive to SOURCE.
python -m software.recorded.prepare_ecg200 "$SOURCE" local-intake/recorded/ecg200
python -m software.recorded.validate local-intake/recorded/ecg200/manifest.csv --positive-label=-1 --width 4 --integer
```

| Observed result | Value |
| --- | ---: |
| Integer threshold / floating-point threshold | 38,540 codes / 37.62614147 |
| Test TP / TN / FP / FN, both formats | 19 / 53 / 11 / 17 |
| Accuracy / balanced accuracy | 72.0% / 67.8% |
| Sensitivity / specificity / false-positive rate | 52.8% / 82.8% / 17.2% |

These percentages describe ECG200 only. Nanopore classification sensitivity and false-positive rate require independently labeled reads.

## Intake for a new labeled dataset

Keep the original files locally with their provenance, checksums, units, sampling rate and label definitions. Convert authorized inputs to headerless, one-column numeric waveforms. Build a CSV with columns `id,split,label,waveform,source_group`. Paths are relative to the manifest. Assign specimens or acquisition runs to one split before extracting windows, using the parent source group for every related waveform. Use one preselected positive waveform as `template`, both labels in `calibration`, and both in `test`. Freeze window selection, width, median, numeric format and labels before evaluation. For the current kernel, select signal windows of at most 512 samples and a reference of at most 128. Record any exclusions and the intended deployment workload.

Run the same evaluator with the new manifest and chosen positive label. Add `--include-scores` to retain distances, inclusive endpoints and decisions locally. This intake supports previously exported waveforms. A different raw container or label schema requires an adapter once the data owner supplies the format.
