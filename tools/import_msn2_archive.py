#!/usr/bin/env python3
"""One-time exact-byte transfer of authorized archived Msn2 derived files.

The source map contains temporary file-specific download links, not repository
credentials. Validate every byte identity before including a file in the archive.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'workstreams/msn2_pairing_2026-09-23'
sys.path.insert(0, str(BASE / 'src'))
import analyze_msn2 as analysis
import reveal_pairing


def checked(entry: dict, raw: bytes) -> None:
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256'] or blob != entry['git_blob']:
        raise ValueError('Archived identity differs: ' + entry['path'])


def main() -> None:
    manifest = json.loads((ROOT / 'provenance/msn2_archive_manifest.json').read_text())
    entries = manifest['files']
    sources = json.loads((ROOT / 'tools/msn2_transfer_urls.json').read_text())
    expected_names = {Path(e['path']).name for e in entries[:-2]}
    if set(sources) != expected_names:
        raise ValueError('Transfer source list differs from the seven authorized files')
    payloads = {}
    for e in entries[:-2]:
        name = Path(e['path']).name
        url = sources[name]
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'prod-files-secure.s3.us-west-2.amazonaws.com':
            raise ValueError('Unexpected transfer endpoint')
        print('::add-mask::' + url, flush=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read(e['bytes'] + 1)
        checked(e, raw)
        payloads[e['path']] = raw
        print('Verified ' + name, flush=True)
    # Lossless transport encoding of the fetched historical zero-audit JSON.
    compact = json.loads((ROOT / 'tools/zero_audit_transfer.json').read_text())
    zero = []
    pairs = [(con, c) for con in ('1x', '2x') for c in analysis.CONDITIONS]
    if len(compact) != len(pairs):
        raise ValueError('Zero-audit record count differs')
    for (con, cond), values in zip(pairs, compact):
        n = values[0]
        r = dict(construct=con, condition=cond, rows=n)
        for label, offset in [('SIP18_YFP', 1), ('HXK1_CFP', 5)]:
            z, internal, final, t120 = values[offset:offset + 4]
            r[label] = dict(zero_entries=z, entries=n * 64, all_zero_rows=0,
                rows_with_any_zero=n, rows_with_internal_zero=internal,
                rows_with_zero_final_frame=final, rows_with_zero_in_120min_window=t120)
        r['rows_with_any_zero_either_reporter'] = n
        zero.append(r)
    raw = (json.dumps(zero, indent=2) + '\n').encode()
    checked(entries[-2], raw)
    payloads[entries[-2]['path']] = raw
    # Recreate the saved descriptive reveal with unchanged reviewed code.
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / 'pairs.json'
        source.write_bytes(payloads[str((BASE / 'results/analysis/pair_results.json').relative_to(ROOT))])
        output = Path(directory) / 'reveal.json'
        reveal_pairing.run(source, output)
        raw = output.read_bytes()
    checked(entries[-1], raw)
    payloads[entries[-1]['path']] = raw
    # All identities must pass before any scientific archive target is written.
    for name, raw in payloads.items():
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Unsafe destination')
        if path.exists() and path.read_bytes() != raw:
            raise FileExistsError('Different existing bytes: ' + name)
    for name, raw in payloads.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    target = ROOT / 'provenance/import_manifest.json'
    imported = json.loads(target.read_text())
    old = {e['path']: e for e in imported['files']}
    for entry in entries:
        if entry['path'] in old and old[entry['path']] != entry:
            raise ValueError('Import record conflict')
        old[entry['path']] = entry
    imported['files'] = [old[name] for name in sorted(old)]
    imported['scope'] = 'Public source, primary reference results and complete archived Msn2 derived outputs for all five response definitions. Imported scientific files match their archived byte identities.'
    target.write_text(json.dumps(imported, indent=2) + '\n')
    (ROOT / 'SHA256SUMS').write_text(''.join(e['sha256'] + '  ' + e['path'] + '\n' for e in imported['files']))
    report = dict(status='PASS', file_count=len(entries), source_commit=manifest['source_commit'],
        transfer_scope='Seven archived files copied through temporary file-specific downloads. Zero audit restored from lossless JSON transport. Constraint reveal regenerated with unchanged source and accepted only on exact historical byte agreement.',
        preserved_scientific_source=True, raw_fluorescence_preprocessing_rerun=False,
        files=[dict(path=e['path'], bytes=e['bytes'], sha256=e['sha256'], git_blob=e['git_blob']) for e in entries])
    (ROOT / 'provenance/msn2_archive_transfer.json').write_text(json.dumps(report, indent=2) + '\n')
    print('All nine archived files match historical byte identities.')


if __name__ == '__main__':
    main()
