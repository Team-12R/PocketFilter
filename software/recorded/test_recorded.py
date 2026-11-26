import tempfile
import unittest
from pathlib import Path

from software.recorded import validate


class RecordedValidationTests(unittest.TestCase):
    def test_equal_balanced_accuracy_uses_smallest_threshold(self):
        scores = [(0.0, False), (2.0, True), (3.0, False), (4.0, True)]
        self.assertEqual(validate.choose_threshold(scores), 2.0)

    def test_scores_held_out_waveforms_at_frozen_threshold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in ('template', 'cal', 'hold'):
                (root / f'{split}-pos.txt').write_text('0\n0\n1\n', encoding='utf-8')
                (root / f'{split}-neg.txt').write_text('1\n0\n0\n', encoding='utf-8')
            (root / 'manifest.csv').write_text(
                'id,split,label,waveform,source_group\n'
                'template,template,yes,template-pos.txt,p1\n'
                'cal-positive,calibration,yes,cal-pos.txt,p2\n'
                'cal-negative,calibration,no,cal-neg.txt,p3\n'
                'hold-positive,test,yes,hold-pos.txt,p4\n'
                'hold-negative,test,no,hold-neg.txt,p5\n'
                'hold-missed,test,yes,hold-neg.txt,p6\n',
                encoding='utf-8',
            )
            report = validate.evaluate(root / 'manifest.csv', 'yes', width=0, median=1)
            self.assertEqual(report['threshold'], 0.0)
            self.assertEqual(report['calibration']['balanced_accuracy'], 1.0)
            self.assertEqual(report['test']['confusion'], {'tp': 1, 'tn': 1, 'fp': 0, 'fn': 1})
            self.assertAlmostEqual(report['test']['accuracy'], 2/3)

    def test_rejects_known_source_group_crossing_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / 'manifest.csv'
            manifest.write_text(
                'id,split,label,waveform,source_group\n'
                'template,template,yes,template.txt,shared\n'
                'test,test,yes,held-out.txt,shared\n',
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ValueError, 'source group .* crosses splits'):
                validate.read_manifest(manifest)


if __name__ == '__main__':
    unittest.main()
