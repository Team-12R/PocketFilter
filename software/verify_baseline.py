"""Run the pinned reference model on its synthetic fixtures and check the outputs."""

import argparse
import csv
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

REVISION = "63b6728ac48b8ef733e98085a1fd69e4e4b4bf26"
MODULES = ("config.py", "preprocess.py", "sdtw_matcher.py", "pipeline.py", "run_tests.py")
EXPECTED = {
    "read_001_target_match": (17.9474, "KEEP", 111, 205),
    "read_002_warped_match": (18.4654, "KEEP", 122, 219),
    "read_003_background_reject": (51.0970, "REJECT", 180, 275),
}


def stage_model(checkout, work):
    """Read only the five source blobs from the named Git commit."""
    for name in MODULES:
        data = subprocess.check_output(["git", "-C", checkout, "show", f"{REVISION}:{name}"])
        (work / name).write_bytes(data)


def check_decisions(csv_path):
    """Check all rows, including unique IDs, inclusive indices and run settings."""
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(EXPECTED) or {r["read_id"] for r in rows} != set(EXPECTED):
        raise ValueError("Incomplete or duplicate fixture records")
    for row in rows:
        result = (float(row["best_distance"]), row["decision"],
                  int(row["match_start"]), int(row["match_end"]))
        if result != EXPECTED[row["read_id"]]:
            raise ValueError(f"Unexpected result for {row['read_id']}: {result}")
        if int(row["window_width"]) != 15 or float(row["threshold"]) != 30.0:
            raise ValueError("Unexpected model settings")


def run_suite(checkout, output):
    """Generate fresh inputs in isolation, verify results, then retain run evidence."""
    with TemporaryDirectory() as temp:
        work = Path(temp)
        stage_model(checkout, work)
        subprocess.run([sys.executable, "run_tests.py"], cwd=work, check=True)
        results = work / "outputs"
        check_decisions(results / "results.csv")
        subprocess.run([sys.executable, str(Path(__file__).with_name("check_vectors.py")), str(work)],
                       cwd=work, check=True)
        output.mkdir(parents=True, exist_ok=True)
        for name in ("results.csv", "pocketfilter_test_results.png"):
            shutil.copyfile(results / name, output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="local Git clone of Hamza's model")
    parser.add_argument("output", type=Path, help="destination for verified CSV and plot")
    args = parser.parse_args()
    run_suite(args.checkout.resolve(), args.output.resolve())
    print("PASS: three synthetic reference decisions, scores and spans")


if __name__ == "__main__":
    main()
