# First sprint Â· reproducible baseline

**Sprint review goal:** A teammate can reproduce a software smoke test and see what has been verified on the AUP-ZU3. The report and presentation describe the proposed design. This checklist starts open.

| Work item | Suggested lead from the handoff | Evidence to bring to review |
| --- | --- | --- |
| Reproduce the existing Python model | Akbar + Hamza | Record the source commit, dependencies, exact invocation, input fixture and observed output. Have a second teammate repeat it. |
| Establish the recorded-data baseline | Akbar + Hamza | Confirm access and usage terms for the sponsor's labeled recordings. Record the dataset version, label definition and evaluation split. If access is pending, record the dependency and keep synthetic smoke-test results labeled. |
| Bring up the AUP-ZU3 | Cindy + David | Record the board revision, toolchain and image versions, boot evidence and one repeatable board sanity check. |
| Agree on the first integration test | Team | Write down input and output types, units, expected result and tolerance for one fixture that software and hardware can both consume. |

## Working checklist

- [ ] Put the software reproduction steps and fixture description under `software/`.
- [ ] Record the labeled-data access decision and evaluation method in `docs/validation/`.
- [ ] Put the board bring-up record and sanity-check output under `hardware/`.
- [ ] At review, link the evidence, record blockers and select the first C/C++ or HLS comparison.

Accuracy, latency, throughput, utilization and power each need a defined measurement method. Report observations as they become available. The [design selection report](academic/ECE396/assignments/04-design-selection.pdf) records the original validation proposal.
