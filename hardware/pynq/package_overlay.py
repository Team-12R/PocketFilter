"""Package one implemented overlay and its offline comparison notebook for a board."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def package(overlay, output, variant=None, source_commit=None):
    root = Path(__file__).resolve().parents[2]
    files = {name: root / name for name in (
        "hardware/pynq/bringup.ipynb", "hardware/pynq/host.py",
        "hardware/pynq/README.md", "software/golden_model.py")}
    for name in ("pocketfilter.bit", "pocketfilter.hwh"):
        files[f"hardware/build/overlay/{name}"] = overlay / name
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    metadata = {}
    if variant:
        metadata["DEPLOYMENT.json"] = json.dumps({
            "board": "Real Digital AUP-ZU3",
            "ddr_variant": variant,
            "source_commit": source_commit,
            "vivado": "2024.2",
            "board_preset_commit": "b595ecdf37c7204129517de1773b0895bcdcc2ed",
            "instructions": "Match the board DDR marking and PYNQ image to ddr_variant. "
                            "Extract the archive and run hardware/pynq/bringup.ipynb on the board.",
        }, indent=2) + "\n"
        for name, data in metadata.items():
            hashes[name] = hashlib.sha256(data.encode("utf-8")).hexdigest()
    # Create exclusively so an earlier handoff is never overwritten.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.write(path, name)
        for name, data in metadata.items():
            archive.writestr(name, data)
        archive.writestr("SHA256.json", json.dumps(hashes, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overlay", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--variant", choices=("4gb", "8gb"))
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    if bool(args.variant) != bool(args.source_commit):
        parser.error("--variant and --source-commit must be provided together")
    package(args.overlay, args.output, args.variant, args.source_commit)
