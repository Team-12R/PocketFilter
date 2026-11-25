# Software preliminary design

The [existing Level 1 schematic](level-1-schematic.pdf) is slide 9 of the [17-slide final presentation](../../academic/ECE396/presentations/final-presentation.pdf). Its five blocks are data input, control and preprocessing, matching, decision and output, and power. The table below adds software-level details such as inclusive span indices.

## Execution platform

The executable baseline runs under CPython and NumPy on a workstation. The proposed target is an AUP-ZU3 with the ARM processing system running Python/PYNQ for replay, preprocessing, control and logging. The programmable logic would run a Vitis HLS C/C++ matching kernel. Input packing, numeric precision, DMA framing, register addresses, clock rate and resource allocation are open design decisions. No custom circuit or semiconductor component selection is established for this sprint.

## Functional decomposition

The call graph shows the simulation entry point, its numerical blocks and evidence outputs. The detailed charts below follow the pinned source and the team’s verification harness.

```mermaid
flowchart TB
    main["Simulation main"] --> gen["generate_controlled_tests"]
    gen --> synth["make_squiggle"]
    gen --> noise["add_noise_and_spikes"]
    main --> ev["evaluate_read · once per fixture"]
    ev --> prep["preprocess_signal · read and reference"]
    prep --> med["median_filter"]
    prep --> norm["zscore_normalize"]
    ev --> match["window_constrained_sdtw"]
    ev --> result["Threshold comparison and MatchResult"]
    main --> csv["export_results_csv"]
    main --> plot["save_summary_plot"]
```

**Notation.** N is read length, M is reference length, L is a generic waveform length, K is median width, W is band half-width, and R is record count. Memory estimates describe the workstation implementation. Python containers, the plotting backend and operating-system overhead are additional.

**Memory example.** The longest fixture has N=342, M=100 and W=15. The two cost rows alone require 169,632 bytes (165.66 KiB). They scale with read length because this implementation evaluates all candidate starts in parallel. A future HLS core needs its own storage schedule, accumulator range and numeric error analysis before anyone can claim a BRAM footprint.

**Score semantics.** The local cost is absolute error between normalized samples. The allowed predecessors are diagonal, vertical and horizontal. Only valid positions inside each candidate’s band contribute. The last reference row selects the cheapest ending position. The decision compares the unrounded score to the threshold; the CSV stores four decimal places. An unreachable path has infinite distance and indices (−1, −1).

## Interfaces for board review

| Producer → consumer | Payload and meaning | Status |
| --- | --- | --- |
| Replay input → ARM control | Per-read ID, sample vector, target reference; units and metadata travel with the data | Model receives arrays; recorded-file adapter pending |
| ARM preprocessing → matcher | Normalized read and reference, lengths N and M, half-width W in samples | Python call implemented; transport and word format pending |
| Matcher → ARM decision | Minimum cumulative distance, inclusive start/end indices, completion or error | Python tuple implemented; hardware handshake pending |
| Control → decision | Threshold in the model’s distance units, read ID | Implemented in the host call |
| Decision → operator | ID, score, span, KEEP/REJECT and configuration | CSV implemented; dashboard pending |
| Regulated supply → board | Power input for the board assembly | Team to verify board revision, supply and permissible connection before bring-up |

[Source revision](https://github.com/Katanehh/PocketFilter-Team12R/tree/63b6728ac48b8ef733e98085a1fd69e4e4b4bf26) · [Verification harness](../../software/verify_baseline.py) · [Boundary checks](../../software/check_vectors.py)

## Orchestrate one replay

**Subroutine** `evaluate_read`

**Interface.** read_id: str, raw_signal: float64[N], target_ref: float64[M], window_width: int, threshold: float, median_kernel_size: int → MatchResult.

**Memory.** Retains clean read and reference (8(N+M) bytes), plus transient preprocessing or matcher workspace. Both signals are preprocessed on each call.

```mermaid
flowchart TD
A[Start host timer] --> B[Preprocess read and reference]
B --> C[Compute distance and inclusive span]
C --> D{Raw distance at or below threshold?}
D -->|Yes| E[KEEP]
D -->|No| F[REJECT]
E --> G[Stop timer and return rounded record]
F --> G
```

## Condition a waveform

**Subroutine** `preprocess_signal`

**Interface.** signal: float64[L], kernel_size: int → normalized: float64[L]. Called separately for the read and reference.

**Memory.** Keeps the filtered array while producing the normalized array. Each float64 vector costs 8L bytes.

```mermaid
flowchart TD
A[Receive waveform] --> B[Call median_filter]
B --> C[Call zscore_normalize]
C --> D[Return normalized vector]
```

## Suppress isolated spikes

**Subroutine** `median_filter`

**Interface.** signal: float64[L], kernel_size: int → filtered: float64[L]. Supported replay uses positive odd K.

**Memory.** Edge-padded input has L+K−1 elements for odd K>1. The window view shares storage. The median reduction can use O(LK) temporary values.

```mermaid
flowchart TD
A{K at most one?} -->|Yes| B[Return copy]
A -->|No| C{K even?}
C -->|Yes| D[Raise ValueError]
C -->|No| E[Repeat edge samples and form sliding windows]
E --> F[Return one median per window]
```

## Put amplitudes on a common scale

**Subroutine** `zscore_normalize`

**Interface.** signal: float64[L] → normalized: float64[L]. Uses population standard deviation.

**Memory.** Input and output each cost 8L bytes. Centering and reduction can allocate additional O(L) temporary storage.

```mermaid
flowchart TD
A[Compute population standard deviation] --> B{Below 1e-12?}
B -->|Yes| C[Return zeros of input shape]
B -->|No| D[Subtract mean and divide by deviation]
D --> E[Return float64 vector]
```

## Find the minimum-cost alignment

**Subroutine** `window_constrained_sdtw`

**Interface.** signal: float64[N], target_ref: float64[M], window_width: int → distance: float, start: int, end: int. Indices are zero-based and inclusive.

**Memory.** Two float64 cost rows with N(2W+1) entries each use 16N(2W+1) bytes. Index, validity and cost temporaries add O(N). The matcher does O(MN(2W+1)) work.

```mermaid
flowchart TD
A[Check nonempty inputs and nonnegative W] --> B[Initialize previous row to infinity]
B --> C[Start reference row with infinite costs]
C --> D[Select next band offset and valid signal indices]
D --> E[Seed first cell or add local absolute error to cheapest predecessor]
E --> F{More offsets?}
F -->|Yes| D
F -->|No| G{More reference rows?}
G -->|Yes: advance row| C
G -->|No| H[Take first minimum over starts and offsets]
H --> I{Finite minimum?}
I -->|Yes| J[Return distance and span]
I -->|No| K[Return infinity and indices -1]
```

## Persist the replay log

**Subroutine** `export_results_csv`

**Interface.** results: nonempty list[MatchResult], csv_path: Path → CSV file; Python return None.

**Memory.** Retains R result records upstream. The writer creates one record dictionary at a time. Scalar timing is in host milliseconds.

```mermaid
flowchart TD
A[Create parent directory] --> B[Derive columns from first record]
B --> C[Open output and write header]
C --> D[Write next result with read ID]
D --> E{More records?}
E -->|Yes| D
E -->|No| F[Close file]
```

## Construct a deterministic step waveform

**Subroutine** `make_squiggle`

**Interface.** levels: float64[S], dwells: int[S] → float64[L], where L is the sum of the dwell counts.

**Memory.** O(S+L) values. Repetition and casting can briefly hold two length-L buffers.

```mermaid
flowchart TD
A[Read levels and dwell counts] --> B[Repeat each level for its dwell]
B --> C[Cast to float64 and return]
```

## Perturb a fixture

**Subroutine** `add_noise_and_spikes`

**Interface.** signal: float64[L], rng: Generator, noise_std: float, num_spikes: int → noisy: float64[L].

**Memory.** O(L) Gaussian draws and noisy output, plus O(num_spikes) index and sign values; sampling may allocate additional workspace.

```mermaid
flowchart TD
A[Add Gaussian noise] --> B[Pick distinct spike positions]
B --> C[Draw signs and add impulses]
C --> D[Return perturbed waveform]
```

## Build the model inputs

**Subroutine** `generate_controlled_tests`

**Interface.** No arguments → reference: float64[100] and list of three dictionaries containing ID, title, expected label and signal array.

**Memory.** Outputs retain 1,122 float64 samples (8,976 bytes total) plus Python records, random-generation temporaries and CSV storage.

```mermaid
flowchart TD
A[Seed random generator with 42] --> B[Create reference and two embedded patterns]
B --> C[Create unrelated stepped background]
C --> D[Add noise and spikes]
D --> E[Write four inspection CSVs and return full-precision arrays]
```

## Make the model printout

**Subroutine** `save_summary_plot`

**Interface.** target_ref: array, tests: list, results: list[MatchResult], plot_path: Path → PNG file.

**Memory.** O(total fixture samples) plotted vertices plus a figure raster proportional to pixel width × height.

```mermaid
flowchart TD
A[Plot reference] --> B[Plot each replay waveform]
B --> C[Shade reported interval and label score]
C --> D[Save PNG and release figure]
```

## Execute the simulation

**Subroutine** `main (reference model)`

**Interface.** No arguments → fixture CSVs, decision CSV, PNG and console output.

**Memory.** Retains the four input arrays and three result records; sequential matcher work dominates the numerical workspace.

```mermaid
flowchart TD
A[Generate fixtures and initialize results] --> B[Evaluate next fixture]
B --> C[Append record and print row]
C --> D{More fixtures?}
D -->|Yes| B
D -->|No| E[Export CSV and save plot]
```

## Select executable source

**Subroutine** `stage_model`

**Interface.** checkout: Path, work: Path → five Python files in an isolated directory.

**Memory.** One Git blob in memory at a time; disk space equals the combined source size.

```mermaid
flowchart TD
A[Select pinned revision] --> B[Read next named blob with Git]
B --> C[Write bytes to temporary directory]
C --> D{Another module?}
D -->|Yes| B
D -->|No| E[Return]
```

## Validate the result table

**Subroutine** `check_decisions`

**Interface.** csv_path: Path → None on success; ValueError on mismatch.

**Memory.** O(R) rows. The baseline checks three IDs, scores at exported precision, labels, spans, band width and threshold.

```mermaid
flowchart TD
A[Read CSV rows] --> B{Exact count and set of IDs?}
B -->|No| C[Fail]
B -->|Yes| D[Compare each row and configuration]
D --> E{All rows match?}
E -->|No| C
E -->|Yes| F[Pass]
```

## Exercise four numerical edge cases

**Subroutine** `check_vectors`

**Interface.** model_dir: Path → None on success; raises on unexpected values.

**Memory.** Fixed-size float64 vectors of one to five elements and the model's temporary arrays.

```mermaid
flowchart TD
A[Check exact threshold tie] --> B[Check constant normalization]
B --> C[Check earliest tied start at zero band width]
C --> D[Check unreachable path returns infinity and -1 indices]
D --> E[Pass when all checks agree]
```

## Produce independently checked artifacts

**Subroutine** `run_suite`

**Interface.** checkout: Path, output: Path → CSV and PNG in output directory.

**Memory.** Temporary disk holds five source files and the generated fixtures, CSV and plot. Runs the model and checks sequentially.

```mermaid
flowchart TD
A[Open temporary work directory] --> B[Stage pinned model]
B --> C[Run reference main in subprocess]
C --> D[Check CSV then run edge vectors]
D --> E[Copy verified artifacts to destination]
E --> F[Release temporary directory]
```

## Expose the team CLI

**Subroutine** `main (team verifier)`

**Interface.** Two path arguments from the shell → success exit or a nonzero error.

**Memory.** Two paths and argparse state, plus the workspace used by run_suite.

```mermaid
flowchart TD
A[Parse checkout and output paths] --> B[Resolve paths]
B --> C[Call run_suite]
C --> D[Print PASS on success]
```
