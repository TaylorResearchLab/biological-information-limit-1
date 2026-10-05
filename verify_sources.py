#!/usr/bin/env python3
'Verify source file checksums and Python syntax.'
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def verify(root: Path, manifest: dict) -> dict:
    root = root.resolve()
    seen = set()
    python_files = 0
    for entry in manifest['files']:
        name = entry['path']
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or str(rel) != name or name in seen:
            raise ValueError(f'Invalid or duplicate manifest path: {name}')
        seen.add(name)
        path = root / rel
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError(f'File must remain inside the repository: {name}')
        data = path.read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'Size or SHA-256 mismatch: {name}')
        git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if git_blob != entry['git_blob']:
            raise ValueError(f'Git object mismatch: {name}')
        if path.suffix == '.py':
            ast.parse(data, filename=name)
            python_files += 1
    if not seen:
        raise ValueError('Manifest must contain files.')
    return {'status': 'PASS', 'source_files': len(seen), 'python_sources': python_files}


def main() -> None:
    manifest = json.loads((ROOT / 'provenance/source_manifest.json').read_text())
    print(json.dumps(verify(ROOT, manifest), indent=2))


if __name__ == '__main__':
    main()
