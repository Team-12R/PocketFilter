# AUP-ZU3 sDTW kernel

The baseline accelerates the matching block. The processor conditions both waveforms with the [Python reference](../../software/golden_model.py), converts them to the integer sample format, dispatches one read and applies its threshold to the returned distance. The C++ kernel has no vendor header dependency.

## Interface

| Port | Representation | Meaning |
| --- | --- | --- |
| `signal`, `reference` | Signed 16-bit memory elements | Conditioned sample × 1024, rounded to nearest with ties to even |
| `signal_size`, `reference_size` | 32-bit control integers | Valid element counts, up to 512 and 128 respectively |
| `width` | 32-bit control integer | Band half-width in samples, 0–16 |
| `result` | Four signed 32-bit memory words | Status, integer L1 distance, zero-based inclusive start, inclusive end |

Status 0 indicates a match path, 1 invalid dimensions, and 2 no feasible path. Error and no-path results return −1 in the other three words. Allocate buffers to the interface depths when calling from the testbench. The input and output buffers use AXI memory-mapped interfaces, and the addresses, lengths, width and start/done control use AXI4-Lite. The processor treats integer distance divided by 1024 as the score and compares it with the configured threshold. A change near the decision threshold may need quantization review.

The kernel visits candidate starts in order and retains two arrays of 33 cost entries. At maximum sizes those rows occupy 264 bytes, and the two sample buffers occupy 1,280 bytes before synthesis. These are source-level storage totals. The bound on finite path cost is 65,535 × 271 = 17,759,985, below the sentinel of 2²⁹. The [AMD verification record](../../docs/validation/accelerator.md) includes synthesized resource estimates and simulated transaction cycles.

## Run locally

From the repository root with a C++ compiler and Python 3.8 or newer:

```sh
mkdir -p hardware/build
python hardware/hls/generate_vectors.py hardware/build/vectors.txt
c++ -std=c++17 -O2 -Wno-unknown-pragmas hardware/hls/sdtw.cpp hardware/hls/testbench.cpp -o hardware/build/sdtw-test
hardware/build/sdtw-test hardware/build/vectors.txt
```

Add `--hamza-fixtures references/hamza-model/test_inputs` to the generator command to include the three earlier synthetic replay inputs after initializing that submodule.

## Run in Vitis HLS

Open a shell with AMD Vitis available and run from the repository root. The script targets `xczu3eg-sfvc784-2-e` with an initial 10 ns clock constraint. It creates a fresh batch project under `hardware/build/pocketfilter_hls` each time.

```sh
# C simulation only
vitis-run --mode hls --tcl hardware/hls/run_hls.tcl
# C simulation, synthesis, then C/RTL co-simulation
POCKETFILTER_HLS_STAGE=cosim vitis-run --mode hls --tcl hardware/hls/run_hls.tcl
```

In PowerShell, set `$env:POCKETFILTER_HLS_STAGE = 'cosim'` before the second invocation. For older Vitis installations use `vitis_hls -f hardware/hls/run_hls.tcl`. The stage `synth` stops after synthesis, and `ip` exports the IP and runs co-simulation. Set `POCKETFILTER_PYTHON` if the AMD shell uses a different Python interpreter. [AMD Tcl CLI](https://docs.amd.com/r/2024.2-English/ug1702-vitis-accelerated-reference/vitis-run-Command) · [AUP-ZU3 device](https://xilinx.github.io/AUP-ZU3/overview.html)

After co-simulation, add the packaged IP to a Vivado design with the AUP-ZU3 processing system. Connect the AXI4-Lite control port to the processor and route the memory masters to DDR. Generate the bitstream and metadata for PYNQ. Use the generated register map, then replay the zero-cost fixture and compare all four result words before trying larger inputs. This requires a board session and the AMD tools.
