"""Reference matcher for numeric waveforms and its command-line replay."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, median, pstdev

SAMPLE_SCALE = 1024
MAX_SIGNAL = 512
MAX_REFERENCE = 128
MAX_WIDTH = 16


@dataclass(frozen=True)
class Match:
    distance: float | int
    start: int
    end: int


def preprocess(samples, kernel_size=3):
    """Apply an edge-padded median, then normalize by population deviation."""
    values = [float(x) for x in samples]
    if not values or not all(map(math.isfinite, values)):
        raise ValueError("samples must be nonempty and finite")
    if type(kernel_size) is not int or kernel_size < 1 or kernel_size % 2 != 1:
        raise ValueError("median kernel size must be a positive odd integer")
    radius = kernel_size // 2
    padded = [values[0]] * radius + values + [values[-1]] * radius
    filtered = [median(padded[i:i + kernel_size]) for i in range(len(values))]
    sigma = pstdev(filtered)
    if sigma < 1e-12:
        return [0.0] * len(filtered)
    mean = fmean(filtered)
    return [(x - mean) / sigma for x in filtered]


def match(signal, reference, width):
    """Match a finite conditioned waveform with an anchored L1 band.

    Returns None when no path reaches the last reference sample. Python ints
    are kept exact for hardware vectors. The endpoints are inclusive.
    """
    if type(width) is not int or width < 0:
        raise ValueError("band half-width must be a nonnegative integer")
    signal, reference = tuple(signal), tuple(reference)
    if not signal or not reference or not all(map(math.isfinite, (*signal, *reference))):
        raise ValueError("signal and reference must be nonempty and finite")

    best = None
    for start in range(len(signal)):
        columns = min(len(signal) - start, len(reference) + width)
        if columns <= len(reference) - 1 - width:
            break
        cost = [[math.inf] * columns for _ in reference]
        cost[0][0] = abs(reference[0] - signal[start])
        for row, sample in enumerate(reference):
            for col in range(max(0, row - width), min(columns, row + width + 1)):
                if row == col == 0:
                    continue
                up = cost[row - 1][col] if row else math.inf
                left = cost[row][col - 1] if col else math.inf
                diagonal = cost[row - 1][col - 1] if row and col else math.inf
                cost[row][col] = abs(sample - signal[start + col]) + min(up, left, diagonal)
        distance = min(cost[-1])
        if math.isfinite(distance) and (best is None or distance < best.distance):
            best = Match(distance, start, start + cost[-1].index(distance))
    return best


def read_waveform(path):
    """Read a headerless, one-column text/CSV waveform."""
    return [float(line.strip()) for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]


def quantize(samples):
    """Convert normalized values to signed int16, rejecting overflow."""
    codes = [round(sample * SAMPLE_SCALE) for sample in samples]
    if any(code < -32768 or code > 32767 for code in codes):
        raise ValueError("waveform exceeds the signed 16-bit sample range")
    return codes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("signal", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--width", type=int, required=True, help="band half-width in samples")
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--median", type=int, default=3)
    parser.add_argument("--hls", action="store_true", help="use the HLS integer sample format")
    args = parser.parse_args()
    try:
        if not math.isfinite(args.threshold) or args.threshold < 0:
            raise ValueError("threshold must be finite and nonnegative")
        signal = preprocess(read_waveform(args.signal), args.median)
        reference = preprocess(read_waveform(args.reference), args.median)
        scale = SAMPLE_SCALE if args.hls else 1
        if args.hls:
            if len(signal) > MAX_SIGNAL or len(reference) > MAX_REFERENCE or args.width > MAX_WIDTH:
                raise ValueError("input exceeds the HLS size or band limit")
            signal, reference = quantize(signal), quantize(reference)
        result = match(signal, reference, args.width)
    except (OSError, ValueError, OverflowError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "match": asdict(result) if result else None,
        "distance_scale": scale,
        "decision": "KEEP" if result and result.distance <= args.threshold * scale else "REJECT",
    }, allow_nan=False))


if __name__ == "__main__":
    main()
