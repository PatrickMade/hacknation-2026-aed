#!/usr/bin/env python3
"""Create local secrets without printing them. Existing configuration is preserved."""
from pathlib import Path
import os
import secrets

root = Path(__file__).resolve().parents[1]
target = root / '.env'
with open(target, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as output:
    for line in (root / '.env.example').read_text().splitlines():
        key, separator, value = line.partition('=')
        if separator and not value and any(word in key for word in ('PASSWORD', 'SECRET', 'KEY')):
            value = secrets.token_hex(32) if key == 'FIELD_ENCRYPTION_KEYS' else secrets.token_urlsafe(24)
            line = key + '=' + value
        output.write(line + '\n')
print('Created .env with local secrets (mode 0600).')
