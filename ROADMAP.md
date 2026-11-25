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
