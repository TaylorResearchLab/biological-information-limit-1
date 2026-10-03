#!/usr/bin/env python3
"""Check archived Msn2 derived files and recompute all five response definitions.

Starts from the archived scalar fluorescence features, not the original traces.
Checks hashes first. Preserves archived outputs. Exact values and discrete fields
must agree exactly; floating values use absolute and relative tolerances 1e-12.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from fractions import Fraction as F
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT / 'workstreams/msn2_pairing_2026-09-23'
sys.path.insert(0, str(WS / 'src'))
import analyze_msn2 as analysis
import reveal_pairing


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def compare(a, b, location: str, errors: list[float]) -> None:
    if isinstance(a, dict):
        require(isinstance(b, dict) and a.keys() == b.keys(), location + ': fields differ')
        for key in a:
            compare(a[key], b[key], location + '/' + key, errors)
    elif isinstance(a, (list, tuple)):
        require(isinstance(b, (list, tuple)) and len(a) == len(b), location + ': lengths differ')
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f'{location}/{i}', errors)
    elif isinstance(a, float):
        require(isinstance(b, (float, int)) and not isinstance(b, bool), location + ': type differs')
        require(math.isfinite(a) and math.isfinite(b), location + ': nonfinite value')
        errors.append(abs(a - b))
        require(math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12), location + ': numerical mismatch')
    else:
        require(type(a) is type(b) and a == b, location + ': exact value differs')


def run() -> dict:
    manifest = json.loads((ROOT / 'provenance/msn2_archive_manifest.json').read_text())
    require(len(manifest['files']) == 9, 'Expected nine archived data/result files')
    for item in manifest['files']:
        path = ROOT / item['path']
        require(path.resolve().is_relative_to(ROOT) and not path.is_symlink(), 'Invalid archive path')
        raw = path.read_bytes()
        require(len(raw) == item['bytes'], item['path'] + ': size mismatch')
        require(hashlib.sha256(raw).hexdigest() == item['sha256'], item['path'] + ': SHA-256 mismatch')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(blob == item['git_blob'], item['path'] + ': Git object mismatch')
    analysis.verify_solver()
    base = WS / 'results/analysis'
    groups = {(con, cond): [] for con in ('1x', '2x') for cond in analysis.CONDITIONS}
    with gzip.open(base / 'cell_features.csv.gz', 'rt', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        expected_header = ['construct', 'condition', 'source_row_1based', 'SIP18_max11', 'HXK1_max11', 'SIP18_at120', 'HXK1_at120']
        require(reader.fieldnames == expected_header, 'Feature columns differ')
        for row in reader:
            key = (row['construct'], row['condition'])
            require(key in groups, 'Unknown feature group')
            require(int(row['source_row_1based']) == len(groups[key]) + 1, 'Source row order differs')
            values = [float(row[col]) for col in expected_header[3:]]
            require(all(math.isfinite(v) and v >= 0 for v in values), 'Invalid feature')
            groups[key].append(values)
    require(sum(map(len, groups.values())) == 40458, 'Feature row count differs')
    features = {key: np.asarray(values) for key, values in groups.items()}
    for con, n in [('1x', 21236), ('2x', 19222)]:
        require(sum(len(features[(con, c)]) for c in analysis.CONDITIONS) == n, 'Construct total differs')
    thresholds, conditions, records, summaries = [], [], [], []
    for scheme, feature, method, q in analysis.SCHEMES:
        offset = 0 if feature == 'max11' else 2
        for con in ('1x', '2x'):
            names = analysis.CONDITIONS if method == 'equal_condition' else (analysis.CONDITIONS[0],)
            threshold = tuple(analysis.inverse_mixture_quantile([features[(con, c)][:, offset + j] for c in names], q) for j in (0, 1))
            thresholds.append(dict(scheme=scheme, construct=con, feature=feature, method=method, quantile=q, threshold_SIP18=threshold[0], threshold_HXK1=threshold[1]))
            counts = {c: analysis.binary_counts(features[(con, c)][:, offset:offset + 2], threshold) for c in analysis.CONDITIONS}
            conditions.extend(dict(scheme=scheme, construct=con, condition=c, counts_00_01_10_11=counts[c]) for c in analysis.CONDITIONS)
            rr = []
            for c0, c1 in combinations(analysis.CONDITIONS, 2):
                r = analysis.analyze_counts(counts[c0], counts[c1])
                r.update(scheme=scheme, construct=con, condition0=c0, condition1=c1)
                r['reference_contrast'] = next((name for name, a, b in analysis.REFERENCES if (a, b) == (c0, c1)), None)
                rr.append(r)
            records.extend(rr)
            summaries.append(dict(scheme=scheme, construct=con, pairs=len(rr),
                positive_gain_pairs=sum(r['gain_over_best_single'] > 0 for r in rr),
                gain_at_least_one_percentage_point=sum(r['gain_over_best_single'] >= F(1, 100) for r in rr),
                median_pairing_gain=float(np.median([float(r['gain_over_best_single']) for r in rr])),
                max_pairing_gain=max(r['gain_over_best_single'] for r in rr),
                median_marginal_only_width=float(np.median([float(r['marginal_only_width']) for r in rr])),
                max_marginal_only_width=max(r['marginal_only_width'] for r in rr),
                independence_overestimates_pairs=sum(r['independence_completion_error_in_accuracy'] > 0 for r in rr),
                independence_underestimates_pairs=sum(r['independence_completion_error_in_accuracy'] < 0 for r in rr),
                max_abs_independence_accuracy_error=max(abs(r['independence_completion_error_in_accuracy']) for r in rr)))
    errors = []
    outputs = {'thresholds.json': thresholds, 'condition_counts.json': conditions, 'pair_results.json': records,
               'reference_contrasts.json': [r for r in records if r['reference_contrast']], 'summary.json': summaries}
    exact_serializations = {}
    for name, result in outputs.items():
        expected_bytes = (base / name).read_bytes()
        compare(analysis.encode(result), json.loads(expected_bytes), name, errors)
        regenerated = (json.dumps(analysis.encode(result), indent=2, allow_nan=False) + '\n').encode()
        exact_serializations[name] = regenerated == expected_bytes
    primary = [analysis.encode(r) for r in conditions if r['scheme'] == 'primary_median']
    expected_primary = json.loads((ROOT / 'workstreams/paper1_checkpoint_2026-09-23/verification_2026-10-02/primary_condition_counts.json').read_text())
    compare(primary, expected_primary, 'primary condition cross-check', errors)
    provenance = json.loads((base / 'member_provenance.json').read_text())
    require(provenance['archive_sha256'] == analysis.SOURCE_SHA, 'Raw archive identity differs')
    require(len(provenance['members']) == 34, 'Expected 34 raw member identities')
    for r in provenance['members']:
        require(r['shape'] == [len(groups[(r['construct'], r['condition'])]), 128], 'Raw member dimensions differ')
    zero = json.loads((base / 'zero_audit.json').read_text())
    require(len(zero) == 34, 'Expected 34 saved zero-audit records')
    for r in zero:
        n = len(groups[(r['construct'], r['condition'])])
        require(r['rows'] == n and r['rows_with_any_zero_either_reporter'] == n, 'Zero-audit row total differs')
        for label in ('SIP18_YFP', 'HXK1_CFP'):
            require(r[label]['entries'] == 64 * n and r[label]['all_zero_rows'] == 0, 'Zero-audit dimensions differ')
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'constraint_reveal.json'
        reveal_pairing.run(base / 'pair_results.json', output)
        require(output.read_bytes() == (WS / 'results/constraint_reveal.json').read_bytes(), 'Reveal output bytes differ')
        reveal = json.loads(output.read_text())
    return dict(status='PASS', archived_files=9, feature_rows=40458, condition_records=len(conditions),
        threshold_records=len(thresholds), comparisons=len(records), response_definitions=5,
        summaries=len(summaries), reference_contrasts=len(outputs['reference_contrasts.json']),
        comparisons_per_scheme=dict(Counter(r['scheme'] for r in records)),
        reveal_cases=len(reveal['cases']), reveal_nested_checks=reveal['nested_interval_checks'],
        max_float_absolute_difference=max(errors, default=0),
        regenerated_json_byte_matches=exact_serializations, python=sys.version, numpy=np.__version__,
        scope='Verification from archived scalar features. Original fluorescence preprocessing and experimental replication were not rerun.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'Choose a new output file')
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
