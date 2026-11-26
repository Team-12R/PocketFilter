"""Build parity vectors from the recorded lambda control in the SquiggleFilter archive."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py

from hardware.hls.generate_vectors import write_vectors
from software.golden_model import preprocess, quantize


def read_prefix(group, size):
    raw = group["Raw/Signal"]
    if raw.ndim != 1 or len(raw) < size:
        raise ValueError(f"Expected at least {size} samples in {group.name}")
    channel = group["channel_id"].attrs
    scale = float(channel["range"]) / float(channel["digitisation"])
    picoamps = (raw[:size].astype("float64") + float(channel["offset"])) * scale
    return quantize(preprocess(picoamps))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fast5", type=Path, help="multi-read lambda control FAST5")
    parser.add_argument("vectors", type=Path)
    args = parser.parse_args()
    with h5py.File(args.fast5, "r") as archive:
        reads = sorted(key for key in archive if key.startswith("read_"))
        if len(reads) < 9:
            parser.error("This replay requires nine distinct reads")
        template = read_prefix(archive[reads[0]], 64)
        write_vectors(args.vectors, ((read_prefix(archive[key], 256), template, 8)
                                     for key in reads[1:9]))
    print(json.dumps({"file": args.fast5.name, "sha256": hashlib.sha256(args.fast5.read_bytes()).hexdigest(),
                      "template": reads[0], "queries": reads[1:9]}, indent=2))


if __name__ == "__main__":
    main()
