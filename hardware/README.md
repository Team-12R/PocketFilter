# AUP-ZU3 bring-up record

**Status on 25 November 2026.** The checked workstation exposed no serial port through the Windows serial-port inventory. Vivado, Vitis, Vitis HLS and XSCT were absent from the shell path. No board boot log, image identifier, HLS synthesis report or measured board result was available. The recorded evidence therefore ends at the workstation replay.

| Board session | Evidence to capture | Acceptance |
| --- | --- | --- |
| Identify the setup | Board revision, approved power source, boot medium, image identifier and tool versions | A teammate can identify the exact configuration |
| Boot the processing system | Serial or console transcript, OS and board identity | Repeatable boot and an interactive shell |
| Run the ARM baseline | Model commit, fixture ID, score, span and decision | Three decisions agree with the host baseline; record any numeric differences |
| First logic comparison | Tool version, kernel build, fixture and output record | Identical-vector case yields a zero score, span [0, 2] and KEEP |
| Measure the implementation | Instrumentation boundary, accepted-sample count, elapsed time, resource report and energy method | Results tied to a build and workload |

The current design uses the development board and a proposed regulated supply. The team still needs to confirm its power arrangement. If the team builds an external circuit, its schematic, component values, pin numbers and component datasheets belong in the design record. [Integration vector](../docs/validation/README.md)
