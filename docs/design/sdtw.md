# Window-constrained sDTW

Assignment 4 selected one diagonal band per candidate start. The team software uses cumulative absolute difference and permits diagonal, horizontal and vertical moves. A candidate at signal index `s` starts at reference index 0 and signal index `s`. For reference index `i` and signal index `j`, a cell is legal when `abs(j - s - i) <= width` and `s <= j < len(signal)`. The best path reaches the final reference sample. The read may have samples on either side of the match. Equal scores resolve to the earlier start, then the earlier end. [Assignment 4 selection](../../academic/ECE396/assignments/04-design-selection.pdf) · [Final presentation, slide 5](../../academic/ECE396/presentations/final-presentation.pdf)

SquiggleFilter provides precedent for dynamic programming on a waveform using absolute local differences and rolling storage. Its notebook's recurrence, scoring and endpoint rules differ from the team contract. The Python and C++ implementations here follow the team's anchored band and Hamza Kittaneh’s original model. [SquiggleFilter notebook revision](https://github.com/Team-12R/SquiggleFilter/blob/21558e9701141c93c28a9f9c9c0316d2a50c5dfb/sdtw_analysis.ipynb) · [Hamza’s pinned matcher](https://github.com/Katanehh/PocketFilter-Team12R/blob/63b6728ac48b8ef733e98085a1fd69e4e4b4bf26/sdtw_matcher.py)

## Processor and programmable logic

| Stage | Python golden model | AUP-ZU3 deployment |
| --- | --- | --- |
| Condition waveforms | Edge-median filter, population z-score | ARM processing system |
| Select representation | Floating-point by default. Integer mode rounds normalized values × 1024 to signed 16-bit codes | ARM prepares buffers |
| Match | Straightforward full cost grid for each candidate | Vitis HLS C++ with two rolling band rows |
| Report | JSON distance, inclusive match span and KEEP/REJECT | ARM reads status, divides integer distance by 1024, and applies threshold |

A valid distance at or below the threshold is KEEP. A missing path is represented as `null` in Python and status 2 in the C++ result. The integer score is exact for the encoded samples. Differences between floating-point and integer results can occur near ties or thresholds. The first kernel limits are 512 signal samples, 128 reference samples and half-width 16. The team uses these bounds for functional verification. [Execution and target configuration](../../hardware/hls/README.md)

## Verification

The Python tests agreed with a direct enumeration of legal paths on 1,260 small binary inputs. The GNU C++17 host testbench matched the Python integer reference on 273 vectors, including the three archived samples. Comparisons check distance, both endpoints and status exactly. The vectors exercise zero width, ties, infeasible paths, dimensions at and beyond the hardware bounds, and full-range signed samples.

The Python model also reproduced Hamza’s three fixture results using the archived, rounded input CSVs. Floating-point distances matched within 1e-10, with identical spans. The HLS-format golden model preserved the decision and span on these three fixtures.

| Fixture | Float distance | Integer distance | Inclusive span | Decision at 30 |
| --- | ---: | ---: | --- | --- |
| Embedded pattern | 17.9474307473 | 18,371 | 111–205 | KEEP |
| Variable dwell | 18.4654012356 | 18,905 | 122–219 | KEEP |
| Unrelated pattern | 51.0970359902 | 52,318 | 180–275 | REJECT |

Vitis HLS synthesis, C/RTL co-simulation, timing and board replay require the AMD tools and a board session. The host tests establish numerical equivalence on the exercised inputs.
