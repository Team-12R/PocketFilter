"""Convert the univariate UEA/UCR ECG200 .ts release to local PocketFilter inputs."""

import argparse
import csv
import hashlib
from pathlib import Path


HASHES = {
    "TRAIN": "6b855dbcbae2d968937c2416d22bdc2dc74be90d5ce6345f56950fa7e754b3fe",
    "TEST": "526d18e133ea51ac13dc528fa2bb13f63b4f93473bc329f0fb8a03d4ec92c235",
}


def prepare(source, destination):
    inputs = {}
    for split, digest in HASHES.items():
        data = (source / f"ECG200_{split}.ts").read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Unexpected ECG200_{split}.ts checksum")
        lines = data.decode("utf-8-sig").splitlines()
        inputs[split] = lines[lines.index("@data") + 1:]
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "manifest.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["id", "split", "label", "waveform"])
        for split, rows in inputs.items():
            for index, row in enumerate(filter(str.strip, rows)):
                samples, label = row.rsplit(":", 1)
                role = "test" if split == "TEST" else "calibration"
                if split == "TRAIN" and index == 0:
                    if label != "-1":
                        raise ValueError("First training waveform must have the chosen reference class")
                    role = "template"
                name = f"{split.lower()}-{index:03d}"
                (destination / f"{name}.csv").write_text("\n".join(samples.split(",")) + "\n", encoding="ascii")
                writer.writerow([name, role, label, f"{name}.csv"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)
