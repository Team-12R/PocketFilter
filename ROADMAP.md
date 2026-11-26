# Sprint 01 · preliminary design review

| Work item | State | Evidence or next owner |
| --- | --- | --- |
| Preserve and reproduce the Python reference | Verified on one workstation | [Pinned submodule](references/hamza-model), [runner](software/verify_baseline.py), [observed outputs](docs/validation/README.md). Akbar or Hamza to repeat from a second machine. |
| Specify software blocks and integration vector | Drafted and exercised on the host | [Interfaces, memory and detailed flowcharts](docs/design/software.md), [first vector](docs/validation/README.md) |
| Validate against recorded inputs | Awaiting labeled data and permission | Akbar + Hamza to document provenance and freeze evaluation settings |
| Boot AUP-ZU3 and repeat the vector | Awaiting a board session | Cindy + David to capture the [bring-up record](hardware/README.md) |
| Locate and incorporate the current Level 1 schematic | Verified in the final presentation | [Level 1 schematic, final presentation slide 9](docs/design/level-1-schematic.pdf). The five blocks and signal labels are visible in the original slide. |
| Confirm the circuit scope and workshop attendance | Team confirmation outstanding | Identify any custom circuit and its required schematic/datasheets. Confirm one workshop per member in the team's course records. |

[Public engineering report draft](academic/ECE396/assignments/05-preliminary-design.pdf) · The local cumulative edition is in the ignored local-intake/Assignment 5 folder.

**Review date.** The preliminary design and cumulative report draft are due Monday, November 30, 2026 at 11:59 p.m. Chicago time. The rubric allocates 10 points to the Level 1 schematic, 20 to preliminary design and 10 to simulation. The instructor requested a web URL for the whole report. The report incorporates the existing team schematic directly.

**Sprint exit.** The synthetic baseline and boundary checks are reproducible. Next gates are a second operator replay, recorded-data access, and a documented board boot. C/C++ and HLS bring-up can use the tested tie vector as their first comparison.

## Implementation sprint

- [x] Implement the floating-point golden model and a bounded integer reference mode.
- [x] Port the matching block to a C++ kernel and prepare the AUP-ZU3 Vitis HLS project.
- [x] Compare the C++ results against 273 Python reference vectors on the host.
- [x] Run AMD C simulation and synthesis, export the IP, and verify 270 synthetic vectors and eight recorded controls in Verilog co-simulation.
- [x] Prepare the Vivado design, PYNQ host, offline packaging and comparison notebook. Bind the host to the generated 4 GB hardware register map.
- [ ] Verify both variant-specific implementation reports and deliver matched BIT/HWH archives.
- [ ] Cindy and David to execute the notebook on the physical AUP-ZU3 and retain its results.
- [ ] Evaluate independently labeled nanopore reads when the sponsor supplies the dataset.

[Vendor reports and requirements traceability](docs/validation/accelerator.md) · [Recorded experiments](docs/validation/recorded.md)

[Algorithm, test evidence and source provenance](docs/design/sdtw.md)
