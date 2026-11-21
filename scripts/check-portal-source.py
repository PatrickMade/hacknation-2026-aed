#!/usr/bin/env python3
"""Verify the imported release and the explicitly documented local changes."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
modified = {
    'backend/docker/app/Dockerfile',
    'frontend/proxy.local.conf.json',
    'frontend/src/app/app.config.ts',
    'frontend/src/app/app.module.ts',
    'frontend/src/app/services/leflet.service.ts',
}
manifest = json.loads((root / 'local/upstream-files.json').read_text())
errors = []
for name, expected in manifest.items():
    path = root / name
    if not path.is_file():
        errors.append('Missing source: ' + name)
    elif name not in modified and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append('Undocumented modification: ' + name)
for name in modified:
    if name not in manifest or name not in (root / 'UPSTREAM.md').read_text():
        errors.append('Undocumented override: ' + name)
if errors:
    raise SystemExit('\n'.join(errors))
assert 'GNU GENERAL PUBLIC LICENSE' in (root / 'LICENSE').read_text()
assert 'enabled: false' in (root / 'frontend/src/app/app.module.ts').read_text()
assert 'disabled: true' in (root / 'frontend/src/app/app.module.ts').read_text()
assert 'http://flags/api' in (root / 'backend/mcod/settings/jury.py').read_text()
print('Verified {} upstream files, {} documented modifications and local telemetry settings.'.format(len(manifest), len(modified)))
