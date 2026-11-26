# First processor-to-FPGA comparison

Cindy and David can use [bringup.ipynb](bringup.ipynb) to check the AUP-ZU3 overlay. The notebook sends three synthetic waveforms to `sdtw_kernel_0`. For every transaction it compares the four returned signed integers with the repository’s [Python golden model](../../software/golden_model.py).

## On the board

1. Boot the correct PYNQ image for the board revision. Record the revision, image identifier, source commit and Vivado/Vitis versions used for this build.
2. Extract the [board-specific ZIP](../vivado/README.md) into a directory accessible to the board’s Jupyter server. Alternatively, copy the matching BIT and HWH from one implementation into `hardware/build/overlay/` in this checkout, with basename `pocketfilter`. The notebook uses this layout to find the overlay and golden model.
3. Open `hardware/pynq/bringup.ipynb` with the board’s Python 3 PYNQ kernel. Use one notebook session with exclusive access to the overlay. Run the cells in order. The first prints both file hashes and environment versions. The next programs the board and shows the active IP register names, offsets and widths from the HWH.
4. Save an executed copy of the notebook with the setup details. The last cell prints a row only when the hardware agrees with Python. Capture any traceback and the register listing when a comparison fails.

| Synthetic input | Expected (status, distance, start, end) |
| --- | --- |
| Identical three-sample waveforms, conditioned and quantized on the processor | `(0, 0, 0, 2)` |
| Signed codes with an interior best match | `(0, 2, 1, 2)` |
| Two-sample reference cannot fit the one-sample signal at width zero | `(2, -1, -1, -1)` |

## Transaction details

The notebook records processor-observed time from the AXI4-Lite start write to polling AP_DONE with a monotonic clock. The interval includes Python, MMIO and polling delays. Acquisition, preprocessing, allocation and cache synchronization fall outside that boundary. Use a separately instrumented replay for first-sample-to-decision latency.

The notebook uses the compiled AXI4-Lite register offsets and pointer widths from the HWH. The host writes the full device address into each pointer, splitting a 64-bit address over two 32-bit words. It allocates physically contiguous buffers at the kernel’s interface depths, flushes the inputs and output sentinel, then launches the IP. After `AP_DONE` it invalidates the output cache and reads four words. A mismatch reports both complete tuples. The host rejects invalid dimensions and unrepresentable addresses before starting a transaction. [PYNQ allocation and cache operations](https://pynq.readthedocs.io/en/v2.7.0/pynq_libraries/allocate.html) · [PYNQ overlay metadata](https://pynq.readthedocs.io/en/v2.7.0/overlay_design_methodology/overlay_design.html)

The default completion timeout is five seconds. After a timeout or interrupt during execution, keep the notebook kernel alive until the board is reset. Buffers remain reserved because the fabric may still access their DDR addresses. Reboot the board before retrying. A missing IP or unsupported register map calls for checking the matching HWH, hardware build and generated HLS driver map.

## Workstation check

From the repository root, run:

```sh
python -m unittest discover -s hardware/pynq -p test_host.py -v
```

The mock keeps separate processor and device copies of memory and returns scripted result words. Seven tests passed on Windows with CPython 3.11.15. They cover signed samples, 32- and 64-bit addresses, register mapping, cache transfers, input validation, busy and timeout handling, repeated calls and detection of a discrepancy in each output word. Board execution, timing and power require hardware measurements.
