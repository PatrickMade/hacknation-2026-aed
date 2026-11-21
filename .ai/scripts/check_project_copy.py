"""Check the frozen project copy of the harness for internal consistency.

    python3 -B .ai/scripts/check_project_copy.py [--project <root>]

This repository carries a frozen, edited copy of the harness (SDLC.md, "Harness copy"). The upstream pin check no
longer applies, so this gate proves instead, without the network:

1. Skills: both skill roots (.agents/skills, .claude/skills) hold exactly the skills of .ai/apptrick-skills.lock.json
   (plus its local skills), with the locked SHA-256 and executable bit of every file.
2. Extensions: every .ai/skills/<name>/SKILL.md extends an installed skill and has one harness block.
3. References: every `apptrick-<name>` token in the project's text files names an installed skill or one of the
   known non-skill identifiers below (markers, storage keys, retired paths).
4. Residue: no private host, account or store-publishing term in any project file outside .ai/third-party.
5. Linear: the `linear` block of .ai/agentic.config.json passes the Linear adapter's own validation.

Files are the ones Git tracks or would track (`git ls-files -co --exclude-standard`). Prints one JSON object;
exit 0 passed, 1 rejected."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apptrick_linear  # noqa: E402  (next to this file)

EDITION_LOCK = '.ai/apptrick-skills.lock.json'
CONFIG = '.ai/agentic.config.json'
SKILL_ROOTS = ('.agents/skills', '.claude/skills')
EXTENSIONS = '.ai/skills'
# Imported portal releases are checked by scripts/check-portal-source.py.
EXEMPT = ('.ai/third-party/', 'backend/', 'frontend/')
BEGIN = '<!-- apptrick-harness:begin -->'
END = '<!-- apptrick-harness:end -->'
# `apptrick-` tokens that are not skill names.
NON_SKILL = {
    'apptrick-harness',             # the harness block markers
    'apptrick-skills',              # .ai/apptrick-skills.lock.json and the installer work prefix
    'apptrick-skill',               # an example trigger phrase in apptrick-create-skill
    'apptrick-run-ownership',       # PR comment marker of apptrick-advance-pr
    'apptrick-prototype-author',    # browser storage keys of the apptrick-design prototype
    'apptrick-prototype-comments',
    'apptrick-auto-fix-issue',      # retired extension paths that apptrick-upgrade and apptrick-deliver look for
    'apptrick-auto-implement-issue',
    'apptrick-template-workflow',   # the edition lock's allowlisted local skill name
}
REFERENCE = re.compile(r'apptrick-[a-z0-9]+(?:-[a-z0-9]+)*')
# Bracketed letters keep this file itself free of the terms it looks for.
RESIDUE = re.compile(r'p[a]tbox|mac[b]ook|get[m]ac|google[ ]play|app[ ]store|test[f]light|/[U]sers/|/[V]olumes/',
                     re.IGNORECASE)


class Rejected(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise Rejected(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def project_files(root):
    out = subprocess.run(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z'],
                         capture_output=True, check=True).stdout.decode()
    return sorted(rel for rel in out.split('\0') if rel and (root / rel).is_file())


def text_of(path):
    data = path.read_bytes()
    if b'\0' in data:
        return None
    try:
        return data.decode()
    except UnicodeDecodeError:
        return None


def check_skills(root):
    lock = json.loads((root / EDITION_LOCK).read_text())
    skills, local, files = lock['skills'], lock.get('localSkills', []), lock['files']
    executables = set(lock.get('executables', []))
    for skill_root in SKILL_ROOTS:
        base = root / skill_root
        present = {entry.name for entry in base.iterdir() if entry.name.startswith('apptrick-')}
        require(present <= set(skills) | set(local), 'unexpected_skill:' + ','.join(sorted(present - set(skills) - set(local))))
        require(set(skills) <= present, 'skill_missing:' + skill_root + ':' + ','.join(sorted(set(skills) - present)))
        installed = {path.relative_to(base).as_posix(): path for name in skills
                     for path in (base / name).rglob('*') if path.is_file()}
        require(set(installed) == set(files), 'skill_files_differ:' + skill_root + ':'
                + ','.join(sorted(set(installed) ^ set(files))[:5]))
        for rel, path in installed.items():
            require(digest(path.read_bytes()) == files[rel], 'skill_file_drift:' + skill_root + '/' + rel)
            require(bool(path.stat().st_mode & 0o111) == (rel in executables), 'skill_mode_drift:' + skill_root + '/' + rel)
    return set(skills), len(files) * len(SKILL_ROOTS)


def check_extensions(root, skills):
    count = 0
    for path in sorted((root / EXTENSIONS).glob('*/SKILL.md')):
        name = path.parent.name
        require(name in skills, 'extension_without_skill:' + name)
        lines = path.read_text().split('\n')
        require(lines.count(BEGIN) == 1 and lines.count(END) == 1 and lines.index(BEGIN) < lines.index(END),
                'harness_block_markers:' + name)
        count += 1
    return count


def check_text(root, skills):
    unknown, residue, scanned = {}, [], 0
    for rel in project_files(root):
        if rel.startswith(EXEMPT) or rel == 'local/upstream-files.json':
            continue
        text = text_of(root / rel)
        if text is None:
            continue
        scanned += 1
        for token in set(REFERENCE.findall(text)) - skills - NON_SKILL:
            unknown.setdefault(token, rel)
        residue += [f'{rel}:{n}' for n, line in enumerate(text.split('\n'), 1) if RESIDUE.search(line)]
    require(not unknown, 'unknown_skill_reference:' + ','.join(f'{t} ({r})' for t, r in sorted(unknown.items())[:5]))
    require(not residue, 'residue:' + ','.join(residue[:5]))
    return scanned


def check(root):
    skills, edition_files = check_skills(root)
    extensions = check_extensions(root, skills)
    scanned = check_text(root, skills)
    try:
        apptrick_linear.load_config(root / CONFIG)
    except apptrick_linear.AdapterError as error:
        raise Rejected('linear_config_invalid:' + str(error))
    return {'status': 'passed', 'skills': len(skills), 'skillFiles': edition_files, 'extensions': extensions,
            'textFilesScanned': scanned, 'residue': 0, 'linear': 'valid'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check the frozen project copy of the harness')
    parser.add_argument('--project', default='.')
    args = parser.parse_args(argv)
    try:
        result = check(Path(args.project).resolve())
    except (Rejected, OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as error:
        code = str(error) if isinstance(error, Rejected) else type(error).__name__
        print(json.dumps({'status': 'rejected', 'code': code}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
