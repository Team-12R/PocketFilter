# PocketFilter engineering handoff

Team 12-R works in [Team-12R/PocketFilter](https://github.com/Team-12R/PocketFilter). [PR #1](https://github.com/Team-12R/PocketFilter/pull/1) merged the verified accelerator. [PR #2](https://github.com/Team-12R/PocketFilter/pull/2) contains the two routed overlay packages and the evidence for engineering review.

## What passed

- The Python model agreed with direct path enumeration on 1,260 inputs. Native C++ and AMD C simulation each agreed on 273 synthetic vectors. Seven host-side MMIO and cache tests passed.
- Verilog co-simulation agreed with Python on all four result words for 270 synthetic vectors and eight recorded lambda control queries. The controls took 921,371–921,421 simulated kernel cycles per query. The held-out ECG200 surrogate had 72/100 correct classifications. [Simulation reports and boundaries](docs/validation/accelerator.md) · [Recorded-data protocol](docs/validation/recorded.md)
- Both Vivado 2024.2 builds routed at a 100 MHz PL clock constraint with +6.149 ns worst setup slack and +0.010 ns worst hold slack. Each used 5,355 LUTs, 8,282 registers, 1.5 BRAM tiles and zero DSPs. Both routed DRC and methodology reports registered zero checks found. Packaging checks confirmed the variant-specific DDR settings, paired files, reset connectivity and HWH register map. [Implementation reports](docs/validation/vivado-2024.2)

## Deploy on the board

| Board marking | Download | ZIP SHA-256 |
| --- | --- | --- |
| 4G | [4 GB ZIP](deployment/pocketfilter-4gb.zip) | `d5a0ad55bd4126f97e0ca604ecb9b1fc00e99ca24d5a325d8ed722f2e412f3e7` |
| 8G | [8 GB ZIP](deployment/pocketfilter-8gb.zip) | `c92d81f526f01162bbce785d017b04a29657ad827fe98f1d7b5b6eefb29f5340` |

The 4 GB hardware build used the Tcl from `d2ebb0bbf81e5165e180de3f5a70eb3f62122630`. The 8 GB build reused compatible IP through shared cache, as recorded in `ae5f947ccf1486c46504b333824da1b6e1df717b`. Both use the same kernel and notebook from `d2ebb0b` and Real Digital BSP `b595ecdf37c7204129517de1773b0895bcdcc2ed`. Each archive contains `DEPLOYMENT.json` and member-level SHA-256 hashes.

**Cindy and David.** Read the DDR marking and boot the matching PYNQ image. Verify the ZIP hash, extract the selected archive into the Jupyter workspace and run `hardware/pynq/bringup.ipynb` with exclusive access to the overlay. Save the executed notebook, board revision, image ID and archive hash. Expected words are `(0,0,0,2)`, `(0,2,1,2)` and `(2,-1,-1,-1)`. Preserve the notebook output and any timeout or address error. [Board steps](hardware/pynq/README.md)

**Hamza.** Initialize the pinned model submodule and run `python software/verify_baseline.py references/hamza-model local-intake/replay` with the dependencies in the README. Run the native check, then use the pinned BSP and AMD 2024.2 environment for an independent build. Preserve the four-word integer contract when evaluating later HLS optimizations. The current comparison baseline is II 4 for the inner band loop, with per-query latency in the archived RTL reports. [Host and HLS commands](hardware/hls/README.md) · [Vivado reproduction](hardware/vivado/README.md)

## Assignment 5 evidence index

| Rubric area | Existing engineering evidence |
| --- | --- |
| Level 1 schematic | [Team-created slide 9](docs/design/level-1-schematic.pdf) and [original deck](academic/ECE396/presentations/final-presentation.pdf). |
| Preliminary design | [Assignment 4 selected alternative](academic/ECE396/assignments/04-design-selection.pdf), [active function graph, interfaces and memory](docs/design/software.md), [alignment algorithm](docs/design/sdtw.md) and [routed implementation](docs/validation/vivado-2024.2). |
| Models and simulations | [Original simulation plot](docs/validation/sprint-01/pocketfilter_test_results.png), [observed CSV](docs/validation/sprint-01/results.csv), [HLS and RTL reports](docs/validation/vitis-2024.2), [Vivado log excerpt](docs/validation/vivado-2024.2/build-summary.txt) and [recorded experiments](docs/validation/recorded.md). |

**Appendix source inventory.** At `d2ebb0bbf81e5165e180de3f5a70eb3f62122630`, use `software/golden_model.py`, `software/test_golden_model.py`, `software/verify_baseline.py`, `software/check_vectors.py`, `software/recorded/`, `hardware/hls/`, `hardware/pynq/host.py`, `hardware/pynq/bringup.ipynb` and `hardware/vivado/`. The cache-only build adjustment is in `ae5f947ccf1486c46504b333824da1b6e1df717b`. The archived NumPy simulation lives in [Hamza’s original revision](https://github.com/Katanehh/PocketFilter-Team12R/tree/63b6728ac48b8ef733e98085a1fd69e4e4b4bf26).

Physical replay, board throughput, end-to-end latency, energy and classification against independently labeled nanopore reads remain open. The host dispatch timer measures start write through observed completion. Vivado flagged AXI sideband width differences and excluded the OCM segment. This design uses DDR for sample and result buffers. Physical replay must exercise the DDR path and confirm the control handshake on the board.
