"""Calibrate and evaluate a binary waveform threshold from a local manifest."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from software.golden_model import MAX_REFERENCE, MAX_SIGNAL, MAX_WIDTH, match, preprocess, quantize, read_waveform


@dataclass(frozen=True)
class Record:
    id: str
    split: str
    label: str
    waveform: Path
    source_group: str


def read_manifest(path):
    required = {'id', 'split', 'label', 'waveform'}
    records = []
    ids = set()
    groups = {}
    paths = {}
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError('manifest requires id, split, label, and waveform columns')
        for line, row in enumerate(reader, 2):
            record_id, split, label, waveform, group = (
                (row.get(name) or '').strip()
                for name in ('id', 'split', 'label', 'waveform', 'source_group')
            )
            if None in row or not all((record_id, label, waveform)) or record_id in ids:
                raise ValueError(f'manifest row {line} contains invalid fields or a duplicate ID')
            if split not in {'template', 'calibration', 'test'}:
                raise ValueError(f'manifest row {line} has an unknown split: {split!r}')
            if group and groups.setdefault(group, split) != split:
                raise ValueError(f'source group {group!r} crosses splits')
            resolved = (path.parent / waveform).resolve()
            if paths.setdefault(resolved, split) != split:
                raise ValueError(f'waveform {waveform!r} crosses splits')
            ids.add(record_id)
            records.append(Record(record_id, split, label, resolved, group))
    return records


def choose_threshold(scores):
    """Maximize calibration balanced accuracy, with ties at the lowest threshold."""
    scores = list(scores)
    positives = sum(is_positive for _, is_positive in scores)
    negatives = len(scores) - positives
    if not positives or not negatives:
        raise ValueError('threshold calibration requires both labels')

    positive_at = Counter(value for value, positive in scores if value is not None and positive)
    negative_at = Counter(value for value, positive in scores if value is not None and not positive)
    true_positive, true_negative = 0, negatives
    best_threshold, best_score = 0.0, -1
    for threshold in sorted({0.0, *positive_at, *negative_at}):
        true_positive += positive_at[threshold]
        true_negative -= negative_at[threshold]
        score = true_positive * negatives + true_negative * positives
        if score > best_score:
            best_threshold, best_score = threshold, score
    return best_threshold


def score_records(records, template, width, median, positive_label, integer):
    scores = []
    for record in records:
        signal = preprocess(read_waveform(record.waveform), median)
        if integer:
            if len(signal) > MAX_SIGNAL:
                raise ValueError(f'{record.id} exceeds the kernel signal length')
            signal = quantize(signal)
        result = match(signal, template, width)
        scores.append({
            'id': record.id,
            'label': record.label,
            'positive': record.label == positive_label,
            'distance': None if result is None else result.distance,
            'start': None if result is None else result.start,
            'end': None if result is None else result.end,
        })
    return scores


def summarize(scores, threshold, include_scores):
    confusion = dict.fromkeys(('tp', 'tn', 'fp', 'fn'), 0)
    for row in scores:
        row['accepted'] = row['distance'] is not None and row['distance'] <= threshold
        if row['positive']:
            confusion['tp' if row['accepted'] else 'fn'] += 1
        else:
            confusion['fp' if row['accepted'] else 'tn'] += 1
    tp, tn, fp, fn = (confusion[key] for key in ('tp', 'tn', 'fp', 'fn'))
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)
    result = {
        'scored': len(scores),
        'confusion': confusion,
        'accuracy': (tp + tn) / len(scores),
        'balanced_accuracy': (sensitivity + specificity) / 2,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'false_positive_rate': fp / (tn + fp),
        'unreachable': sum(row['distance'] is None for row in scores),
    }
    if include_scores:
        result['scores'] = scores
    return result


def evaluate(manifest, positive_label, width, median, include_scores=False, integer=False):
    records = read_manifest(manifest)
    templates = [record for record in records if record.split == 'template']
    if len(templates) != 1 or templates[0].label != positive_label:
        raise ValueError('manifest requires exactly one template with the positive label')
    labels = {record.label for record in records}
    if len(labels) != 2 or positive_label not in labels:
        raise ValueError('manifest requires exactly two labels')

    template_record = templates[0]
    template = preprocess(read_waveform(template_record.waveform), median)
    if integer:
        if len(template) > MAX_REFERENCE or not 0 <= width <= MAX_WIDTH:
            raise ValueError('reference length or width exceeds kernel limits')
        template = quantize(template)
    calibration_rows = [record for record in records if record.split == 'calibration']
    calibration = score_records(calibration_rows, template, width, median, positive_label, integer)
    threshold = choose_threshold((row['distance'], row['positive']) for row in calibration)

    test_rows = [record for record in records if record.split == 'test']
    if {record.label for record in test_rows} != labels:
        raise ValueError('held-out test split requires both labels')
    test = score_records(test_rows, template, width, median, positive_label, integer)
    return {
        'template_id': template_record.id,
        'positive_label': positive_label,
        'negative_label': next(iter(labels - {positive_label})),
        'width': width,
        'median': median,
        'score_units': 'integer L1 codes' if integer else 'normalized L1',
        'threshold': threshold,
        'source_groups_known': sum(bool(record.source_group) for record in records),
        'calibration': summarize(calibration, threshold, include_scores),
        'test': summarize(test, threshold, include_scores),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--positive-label', required=True)
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--median', type=int, default=3)
    parser.add_argument('--include-scores', action='store_true')
    parser.add_argument('--integer', action='store_true', help='evaluate the deployed int16 format')
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest, args.positive_label, args.width, args.median, args.include_scores, args.integer)
    except (OSError, ValueError, OverflowError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
