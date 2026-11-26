"""Print a read-only progress snapshot for build_boards.sh from the Linux build host."""

import argparse
import re
import time
from pathlib import Path


def duration(seconds):
    minutes, seconds = divmod(int(max(seconds, 0)), 60)
    return f"{minutes}m {seconds:02d}s"


def snapshot(work, variant, baseline=None):
    runs = work / variant / "pocketfilter.runs"
    starts = list(runs.glob("*/.vivado.begin.rst"))
    if not starts:
        print(f"{variant}: no synthesis start recorded")
        return
    first = min(p.stat().st_mtime for p in starts)
    end = runs / "impl_1/.write_bitstream.end.rst"
    now = end.stat().st_mtime if end.is_file() else time.time()
    elapsed = duration(now - first)
    errors = list(runs.glob("*/*.error.rst"))
    if errors:
        print(f"{variant}: failed after {elapsed}. Inspect {errors[0].parent}/runme.log")
        return
    ips = list(runs.glob("pocketfilter_*_synth_1"))
    done = sum((p / ".vivado.end.rst").exists() for p in ips)
    stage = f"component synthesis ({done}/{len(ips)} completed)"
    marker = None
    if (runs / "synth_1/.vivado.begin.rst").exists():
        stage, marker = "top-level synthesis", Path("synth_1/.vivado.begin.rst")
    for name in ("init_design", "opt_design", "place_design", "phys_opt_design", "route_design", "write_bitstream"):
        candidate = Path(f"impl_1/.{name}.begin.rst")
        if (runs / candidate).exists():
            stage, marker = name, candidate
    if end.is_file():
        print(f"{variant}: bitstream written in {elapsed}. Packaging is a separate step.")
        return
    print(f"{variant}: last recorded stage = {stage}; elapsed since first synthesis start = {elapsed}")
    if baseline and marker:
        previous = baseline / marker
        previous_end = baseline / "impl_1/.write_bitstream.end.rst"
        if previous.is_file() and previous_end.is_file():
            remaining = previous_end.stat().st_mtime - previous.stat().st_mtime - (now - (runs / marker).stat().st_mtime)
            if remaining > 0:
                print(f"  Approximate time left from 4 GB run at this stage: {duration(remaining)} (cache and routing differ).")
                return
    print("  ETA unavailable until a comparable implementation completes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="build log containing the Vivado project directory")
    args = parser.parse_args()
    with args.log.open(encoding="utf-8", errors="replace") as stream:
        directory = next((m.group(1) for line in stream
                          if (m := re.match(r"Vivado project directory: (.+)", line))), None)
    if not directory or not Path(directory).is_dir():
        parser.error("Run on the build host with a log pointing to an existing native project")
    work = Path(directory)
    snapshot(work, "4gb")
    snapshot(work, "8gb", work / "4gb/pocketfilter.runs")
