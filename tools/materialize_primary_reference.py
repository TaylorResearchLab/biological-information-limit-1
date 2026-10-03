#!/usr/bin/env python3
"""Store regenerated primary records only when they match the archived bytes.

This packaging utility uses output from the preserved primary reproduction
program. Every target is checked against its historical SHA-256 before writing.
Existing files with different bytes cause an error. Scientific code is unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'workstreams/method_comparison_2026-09-23/'
KEYS = ['construct', 'condition0', 'condition1', 'counts', 'reference_contrast',
        'marginal_only_accuracy_bounds', 'best_fixed_deterministic_worst_case',
        'paired_accuracy', 'SIP18_MI_bits', 'HXK1_MI_bits', 'paired_MI_bits',
        'independence_completion_MI_bits']
EXPECTED = {
    'inputs/primary_records.json': '3d3eabda2d14617d9e25fb645ffd89cb9c8a1eb9583d8acaa8ac6dcb000fbb0e',
    'results/science/decision_comparison.json': '89d1900392d8ed2c0e4d16b80666ff7776bbfdf620e6e780abcd52f71be3d38d',
    'results/science/information_panel.json': '24685289ecb0e49be24a63ee23690bb6479fccd462a9eeaca383946906851296',
    'results/science/information_reveal.json': '3e82eb1b550aa337e58372289d9b7be0986a700cc6d7904ad1be51622edddd89',
    'results/science/summary.json': '1083dbfbe43b1c1b7427842ddb18fcd5b9a35772fd93b2b8320da73cbae20f4b',
}


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-run', required=True, type=Path,
                        help='The primary/ directory from a successful reproduce.py run.')
    args = parser.parse_args()
    source = args.from_run.resolve()
    report = json.loads((source / 'verification_summary.json').read_text())
    if report.get('status') != 'PASS' or report.get('primary_comparisons') != 272:
        raise ValueError('A successful 272-comparison primary run is required.')
    records = json.loads((source / 'primary_pair_results.json').read_text())
    if len(records) != 272:
        raise ValueError('Expected 272 primary records.')
    payloads = {'inputs/primary_records.json': encode([{k: r[k] for k in KEYS} for r in records])}
    for name in ['decision_comparison.json', 'information_panel.json', 'information_reveal.json']:
        payloads['results/science/' + name] = (source / 'information' / name).read_bytes()
    summary = json.loads((source / 'information/summary.json').read_text())
    summary['input_sha256'] = EXPECTED['inputs/primary_records.json']
    payloads['results/science/summary.json'] = encode(summary)
    # Validate every payload and destination before writing any reference file.
    for name, data in payloads.items():
        if hashlib.sha256(data).hexdigest() != EXPECTED[name]:
            raise ValueError(f'Historical file identity did not reproduce: {name}')
        path = ROOT / PREFIX / name
        if path.exists() and path.read_bytes() != data:
            raise FileExistsError(f'Existing reference differs: {path}')
    manifest_path = ROOT / 'provenance/import_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    indexed = {e['path']: e for e in manifest['files']}
    added = []
    for name, data in payloads.items():
        path = ROOT / PREFIX / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        record = {'path': PREFIX + name, 'bytes': len(data), 'sha256': EXPECTED[name],
                  'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                  'origin': 'scientific_checkpoint_32b0e66'}
        indexed[record['path']] = record
        added.append(record)
    manifest['files'] = sorted(indexed.values(), key=lambda e: e['path'])
    manifest['scope'] = ('Public source and primary reference archive. All five materialized input/result files '
                         'match the historical scientific checkpoint. Larger fluorescence-derived tables '
                         'remain a separate archival addition.')
    manifest_path.write_bytes(encode(manifest))
    (ROOT / 'SHA256SUMS').write_text(''.join(f"{e['sha256']}  {e['path']}\n" for e in manifest['files']))
    readme = ROOT / 'README.md'
    text = readme.read_text().replace('checks all 23 imported files', 'checks all 28 imported files')
    readme.write_text(text)
    result = {'status': 'PASS', 'source_checkpoint': manifest['scientific_checkpoint'],
              'scope': 'Byte-identical archival materialization from the reproduced primary records.',
              'files': added}
    (ROOT / 'provenance/primary_reference_materialization.json').write_bytes(encode(result))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
