"""Package one implemented overlay and its offline comparison notebook for a board."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def package(overlay, output):
    root = Path(__file__).resolve().parents[2]
    files = {name: root / name for name in (
        "hardware/pynq/bringup.ipynb", "hardware/pynq/host.py",
        "hardware/pynq/README.md", "software/golden_model.py")}
    for name in ("pocketfilter.bit", "pocketfilter.hwh"):
        files[f"hardware/build/overlay/{name}"] = overlay / name
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    # Create exclusively so an earlier handoff is never overwritten.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.write(path, name)
        archive.writestr("SHA256.json", json.dumps(hashes, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overlay", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.overlay, args.output)
