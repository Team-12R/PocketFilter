"""Check boundary behavior of the staged reference model."""

import math
from pathlib import Path
import sys

import numpy as np


def check_vectors(model_dir):
    sys.path.insert(0, str(model_dir))
    from pipeline import evaluate_read
    from preprocess import zscore_normalize
    from sdtw_matcher import window_constrained_sdtw as match

    pulse = np.array([0.0, 1.0, 0.0])
    record = evaluate_read("threshold_tie", pulse, pulse, 0, 0.0, median_kernel_size=1)
    if (record.best_distance, record.decision, record.match_start, record.match_end) != (0.0, "KEEP", 0, 2):
        raise ValueError("Exact-match threshold tie failed")
    np.testing.assert_array_equal(zscore_normalize(np.full(4, 7.0)), np.zeros(4))
    if match(np.array([5., 1., 2., 1., 2.]), np.array([1., 2.]), 0) != (0., 1, 2):
        raise ValueError("Width-zero matcher failed to select the earliest tied start")
    if match(np.array([1.]), np.array([1., 2.]), 0) != (math.inf, -1, -1):
        raise ValueError("Expected unreachable-path sentinel")
    print("PASS: threshold tie, constant signal, earliest tied start, unreachable path")


if __name__ == "__main__":
    check_vectors(Path(sys.argv[1]))
