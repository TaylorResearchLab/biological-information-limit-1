'Shared output handling and verification for the manuscript examples.'
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
DATA = ROOT / 'data'
sys.path.insert(0, str(SRC))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f'Empty results for {path.name}')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def check_rows(actual: list[dict], expected: list[dict]) -> int:
    """Match row order, fields and text; reject nonfinite or changed numerical values."""
    if len(actual) != len(expected):
        raise AssertionError('Result row count changed')
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a.keys() != e.keys():
            raise AssertionError(f'Fields changed in row {i}')
        for key in e:
            sa, se = str(a[key]), str(e[key])
            try:
                x, y = float(sa), float(se)
            except ValueError:
                if sa != se:
                    raise AssertionError(f'Label changed: row {i}, {key}')
            else:
                if not (math.isfinite(x) and math.isfinite(y)):
                    raise AssertionError(f'Nonfinite value: row {i}, {key}')
                if se.lstrip('-').isdigit():
                    ok = sa == se  # Integer counts and exact ratios remain exact.
                else:
                    ok = math.isclose(x, y, abs_tol=1e-12, rel_tol=1e-12)
                if not ok:
                    raise AssertionError(f'Value changed: row {i}, {key}: {sa} vs {se}')
    return len(actual)


def check_table(out: Path, name: str, example_dir: Path) -> int:
    return check_rows(read_csv(out / name), read_csv(ROOT / 'artifacts' / example_dir.name / name))


def verify_sources(prefixes: tuple[str, ...]) -> dict[str, str]:
    manifest = json.loads((ROOT / 'provenance/source_manifest.json').read_text())
    entries = [e for e in manifest['files'] if e['path'].startswith(prefixes)]
    if not entries:
        raise ValueError('No source paths matched')
    checked = {}
    for entry in entries:
        p = ROOT / entry['path']
        raw = p.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if len(raw) != entry['bytes'] or digest(p) != entry['sha256'] or blob != entry['git_blob']:
            raise AssertionError(f'Source checksum changed: {entry["path"]}')
        checked[entry['path']] = entry['sha256']
    return checked


def output_destination(path: Path) -> Path:
    root = ROOT.resolve()
    runs = root / 'runs'
    out = path.expanduser().resolve()
    if root.is_relative_to(out):
        raise ValueError('Choose a new folder beneath runs/, or outside the repository.')
    if out.is_relative_to(root):
        if runs.is_symlink() or out == runs or not out.is_relative_to(runs):
            raise ValueError('Choose a new folder beneath runs/, or outside the repository.')
    return out


def prepare_out(out: Path) -> Path:
    out = output_destination(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError(f'{out} already contains files. Choose a new --out folder.')
    out.mkdir(parents=True, exist_ok=True)
    return out


def validate_output_file(path: Path) -> Path:
    path = output_destination(path)
    if path.exists():
        raise FileExistsError('Choose a new output file.')
    return path


def arguments(description: str, name: str, *, full_derived: bool = False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--out', type=Path, default=ROOT / 'runs' / name,
                        help=f'New output folder. Default: runs/{name}')
    parser.add_argument('--skip-figures', action='store_true', help='Write numerical results only.')
    if full_derived:
        parser.add_argument('--full-derived', action='store_true',
                            help='Also verify all five Msn2 response definitions from the supplied scalar features.')
    return parser.parse_args()


def run_script(script: Path | str, args: list[str], log: Path) -> None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg', PYTHONPATH=str(SRC))
    command = [sys.executable, str(script)] if isinstance(script, Path) else [sys.executable, '-m', script]
    with log.open('w', encoding='utf-8') as handle:
        result = subprocess.run([*command, *args], cwd=ROOT,
                                env=env, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{script} failed. Read {log}')


def exact_reference(generated: Path, reference: Path) -> dict:
    a, b = digest(generated), digest(reference)
    if a != b:
        raise AssertionError(f'Reference bytes differ for {generated.name}')
    return {'byte_identical': True, 'sha256': a, 'reference_path': str(reference.relative_to(ROOT))}


def finish(out: Path, parameters: dict, checks: dict, sources: dict, started: float) -> None:
    write_json(out / 'parameters_used.json', parameters)
    outputs = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    report = {'status': 'PASS', 'checks': checks, 'source_sha256': sources,
              'output_sha256': outputs, 'elapsed_seconds': round(time.perf_counter()-started, 3),
              'python': sys.version, 'packages': {p: importlib.metadata.version(p)
                for p in ('numpy', 'scipy', 'mpmath', 'matplotlib')}}
    write_json(out / 'verification.json', report)
    print(f'PASS. Results and verification saved in {out}')
    for name in outputs:
        if name.endswith(('.csv', '.png')) and '/' not in name:
            print(f'  {name}')


def entry(function) -> None:
    try:
        function()
    except (OSError, ValueError, AssertionError, RuntimeError, ImportError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc
