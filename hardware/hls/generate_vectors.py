"""Generate deterministic testbench inputs from the numerical reference."""

import argparse
from itertools import chain
from pathlib import Path
from random import Random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "software"))
from golden_model import (
    MAX_REFERENCE, MAX_SIGNAL, MAX_WIDTH, match, preprocess, quantize, read_waveform,
)


def cases():
    yield [0, 1, 0], [0, 1, 0], 0
    yield [9, 0, 1, 0, 0, 1, 0], [0, 1, 0], 0
    yield [9, 0, 1, 1, 0, 9], [0, 1, 0], 1
    yield [0, 1], [0, 1, 1], 1
    yield [0], [0, 1, 1], 1
    yield [0, 0, 0], [0], 16
    yield [-32768] * MAX_REFERENCE, [32767] * MAX_REFERENCE, 0
    yield [0] * (MAX_SIGNAL - 1) + [22], [0] * (MAX_REFERENCE - 1) + [22], MAX_WIDTH
    yield [], [1], 0
    yield [1], [], 0
    yield [1], [1], -1
    yield [1], [1], MAX_WIDTH + 1
    yield [1] * (MAX_SIGNAL + 1), [1], 0
    yield [1], [1] * (MAX_REFERENCE + 1), 0
    rng = Random(257)
    for _ in range(256):
        signal = [rng.randrange(-9, 10) for _ in range(rng.randint(1, 24))]
        reference = [rng.randrange(-9, 10) for _ in range(rng.randint(1, 12))]
        yield signal, reference, rng.randint(0, 6)


def archived_cases(folder):
    reference = quantize(preprocess(read_waveform(folder / "target_ref.csv")))
    for name in ("read_001_target_match.csv", "read_002_warped_match.csv",
                 "read_003_background_reject.csv"):
        signal = quantize(preprocess(read_waveform(folder / name)))
        yield signal, reference, 15


def write_vectors(path, fixtures):
    with path.open("w", encoding="ascii", newline="\n") as output:
        for signal, reference, width in fixtures:
            valid = (0 < len(signal) <= MAX_SIGNAL and 0 < len(reference) <= MAX_REFERENCE
                     and 0 <= width <= MAX_WIDTH)
            result = match(signal, reference, width) if valid else None
            if result:
                expected = 0, result.distance, result.start, result.end
            else:
                expected = (2 if valid else 1), -1, -1, -1
            print(len(signal), len(reference), width, *expected, *signal, *reference, file=output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--hamza-fixtures", type=Path, help="optional pinned test_inputs directory")
    args = parser.parse_args()
    additional = archived_cases(args.hamza_fixtures) if args.hamza_fixtures else ()
    write_vectors(args.output, chain(cases(), additional))
