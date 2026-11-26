import itertools
import unittest

from golden_model import Match, match, preprocess, quantize


def enumerate_paths(signal, reference, width):
    """Explore legal paths directly. Only used on tiny inputs."""
    candidates = []

    def visit(start, row, col, distance):
        distance += abs(reference[row] - signal[col])
        if row == len(reference) - 1:
            candidates.append((distance, start, col))
        for dr, dc in ((1, 0), (0, 1), (1, 1)):
            r, c = row + dr, col + dc
            if r < len(reference) and c < len(signal) and abs(c - start - r) <= width:
                visit(start, r, c, distance)

    for start in range(len(signal)):
        visit(start, 0, start, 0)
    return Match(*min(candidates)) if candidates else None


class GoldenModelTests(unittest.TestCase):
    def test_exhaustive_binary_waveforms(self):
        for length in range(1, 5):
            for signal in itertools.product(range(2), repeat=length):
                for size in range(1, 4):
                    for reference in itertools.product(range(2), repeat=size):
                        for width in range(3):
                            expected = enumerate_paths(signal, reference, width)
                            self.assertEqual(match(signal, reference, width), expected,
                                             (signal, reference, width))

    def test_preprocessing_and_conversion(self):
        self.assertEqual(preprocess([0, 100, 0]), [0.0, 0.0, 0.0])
        self.assertEqual(preprocess([1, 3], 1), [-1.0, 1.0])
        self.assertEqual(quantize([-1.0, 0.5 / 1024, 1.5 / 1024, 1.0]),
                         [-1024, 0, 2, 1024])

    def test_invalid_inputs(self):
        for signal, reference, width in [([], [0], 1), ([0], [0], -1),
                                          ([0], [float("inf")], 0), ([0], [0], 1.5)]:
            with self.assertRaises(ValueError):
                match(signal, reference, width)
        with self.assertRaises(ValueError):
            quantize([32.0])
        with self.assertRaises(ValueError):
            preprocess([0], 2)


if __name__ == "__main__":
    unittest.main()
