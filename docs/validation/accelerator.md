# AUP-ZU3 verification record · 26 November 2026

Vitis HLS 2024.2 in Ubuntu 24.04.2 under WSL ran C simulation, synthesis, Verilog co-simulation and IP export for `xczu3eg-sfvc784-2-e`. Vivado 2024.2 build 5239630 loaded the exported IP and the pinned Real Digital board definitions. The existing installation was sufficient.

| Verification boundary | Executed result |
| --- | --- |
| Python reference | 1,260 exhaustive small inputs matched direct path enumeration. Hamza’s three archived synthetic cases reproduced both endpoints, scores and decisions. Four boundary checks passed. |
| Host C++ and AMD C simulation | Each passed 273 synthetic vectors including the three archived inputs. The separate recorded-control build passed eight additional vectors. |
| HLS synthesis | Requested clock 10 ns, clock uncertainty 2.70 ns, estimated period 7.300 ns. Kernel estimate of 4,137 LUT, 2,692 FF, 8 BRAM18K, 0 DSP and 0 URAM. The inner band-cell loop achieved II 4. Input-copy loops achieved II 1. Top-level latency and interval are data dependent and reported as undefined in synthesis. [Generated report](vitis-2024.2/csynth.rpt) |
| XSim, 270 default vectors | All four result words matched. Transaction latency min/mean/max was 52 / 28,041 / 6,958,077 cycles. Transaction interval was 52 / 28,125 / 6,958,077 cycles. The maximum was the 512-sample, 128-sample reference, width-16 case. [Summary](vitis-2024.2/default-cosim.rpt) · [Per transaction](vitis-2024.2/default-cycles.rpt) |
| XSim, eight recorded controls | Exact agreement on status, integer distance, start and end. Latency min/mean/max was 921,371 / 921,377 / 921,421 cycles, approximately 9.21 ms per query at the simulated 10 ns clock. [Summary](vitis-2024.2/recorded-cosim.rpt) · [Per transaction](vitis-2024.2/recorded-cycles.rpt) · [Input provenance](recorded.md) |
| Processor host | Seven MMIO/cache tests passed on the workstation. The corrected 4 GB Vivado HWH bound to the host with pointer offsets 0x10, 0x1c and 0x40 and control base 0xA0000000. Both reset inputs have active-low polarity and share the PS reset net. |

The original Vivado integration pass exposed an asserted auxiliary reset. The corrected designs connect both active-low reset inputs to PS reset and check polarity during validation. Vivado routed both DDR variants and wrote their bitstreams at the 100 MHz constraint. Worst setup and hold slack were +6.149 ns and +0.010 ns in each design, with zero routed DRC findings. See the [routed reports](vivado-2024.2) and [deployment checksums](../../HANDOFF.md). First board acceptance requires loading the matched BIT/HWH and saving an executed copy of the [comparison notebook](../../hardware/pynq/bringup.ipynb).

## Requirements traceability

| Requirement | Evidence and remaining gate |
| --- | --- |
| ER1, ER5 · decisions and model agreement | Host replay and RTL word comparisons cover the exercised vectors. Verify the same words and host decisions on board. |
| ER2, ER3, ER10, ER13 · offline board execution and independent deployment | Variant-specific [build scripts](../../hardware/vivado/README.md), offline packaging and [operator procedure](../../hardware/pynq/README.md) are available. A second operator must perform the physical replay. |
| ER4, ER7, ER8 · latency, sustained throughput and energy | XSim reports kernel cycles only. Measure the full acquisition-to-decision boundary, sustained sample rate and energy under the same workload on the board. |
| ER6, ER9, ER11 · labels, controls and provenance | [Recorded validation](recorded.md) documents a frozen calibration threshold, held-out surrogate results and input provenance. Independent nanopore labels remain outstanding. |
