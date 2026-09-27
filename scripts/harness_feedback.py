#!/usr/bin/env python3
"""Record project-owned harness feedback and import it once, using only stdlib."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid


STORE = Path('.unity-codex-harness/feedback')
INBOX = Path('feedback/imported')
MANIFEST = Path('.unity-codex-harness/install-manifest.json')
CATEGORIES = ('bug', 'improvement', 'documentation', 'workflow')
BUNDLE_KIND = 'unity-codex-harness-feedback'
UUID_RE = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
HASH_RE = re.compile(r'[0-9a-f]{64}')


def checked_path(path: Path) -> Path:
    """Do not traverse a symlink in user input, state, or output paths."""
    path = path.absolute()
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f'symlink is not supported: {component}')
    return path


def read_json(path: Path) -> dict:
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key in {path}: {key}')
            result[key] = value
        return result

    value = json.loads(checked_path(path).read_text(encoding='utf-8'),
                       object_pairs_hook=unique_keys)
    if not isinstance(value, dict):
        raise ValueError(f'expected a JSON object: {path}')
    return value


def fields(value: dict, expected: set[str]) -> None:
    if set(value) != expected:
        raise ValueError(f'invalid fields: expected {sorted(expected)}')


def schema(value: dict) -> None:
    if type(value.get('schemaVersion')) is not int or value['schemaVersion'] != 1:
        raise ValueError('unsupported schemaVersion; expected 1')


def nonempty(value, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be a nonempty string')


def identifier(value) -> None:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        raise ValueError('ID must be a lowercase UUID')


def timestamp(value) -> None:
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('timestamp must be UTC with a Z suffix')
    datetime.fromisoformat(value[:-1] + '+00:00')


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(entry: dict) -> str:
    content = json.dumps(entry, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def validate_entry(entry: dict) -> None:
    if not isinstance(entry, dict):
        raise ValueError('feedback entry must be an object')
    fields(entry, {'schemaVersion', 'projectId', 'projectName', 'id',
                   'createdAt', 'category', 'title', 'body', 'relatedId', 'harness'})
    schema(entry)
    identifier(entry['projectId'])
    identifier(entry['id'])
    timestamp(entry['createdAt'])
    for key in ('projectName', 'title', 'body'):
        nonempty(entry[key], key)
    if entry['category'] not in CATEGORIES:
        raise ValueError('unsupported category')
    if entry['relatedId'] is not None:
        identifier(entry['relatedId'])
    harness = entry['harness']
    if not isinstance(harness, dict):
        raise ValueError('harness must be an object')
    fields(harness, {'release', 'releaseTag', 'installManifestSha256'})
    for key in ('release', 'releaseTag'):
        nonempty(harness[key], key)
    value = harness['installManifestSha256']
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ValueError('invalid installManifestSha256')


def identity(path: Path) -> dict:
    value = read_json(path)
    fields(value, {'schemaVersion', 'projectId', 'projectName'})
    schema(value)
    identifier(value['projectId'])
    nonempty(value['projectName'], 'projectName')
    return value


@contextmanager
def lock(directory: Path):
    directory = checked_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = checked_path(directory / '.feedback.lock')
    try:
        lock_path.mkdir()
    except FileExistsError as error:
        raise ValueError(f'feedback store is locked: {lock_path}; remove only '
                         'after confirming no writer is running') from error
    try:
        yield
    finally:
        lock_path.rmdir()


def write_new(path: Path, value: dict) -> None:
    """Publish a whole JSON document; caller holds the destination store lock."""
    path = checked_path(path)
    if path.exists():
        raise ValueError(f'refusing to overwrite: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, prefix='.feedback-',
                                         suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def unity_root(root: Path) -> Path:
    root = checked_path(root)
    for relative in ('Assets', 'Packages', 'ProjectSettings/ProjectVersion.txt'):
        path = checked_path(root / relative)
        valid = path.is_file() if relative.endswith('.txt') else path.is_dir()
        if not valid:
            raise ValueError(f'not a Unity project; missing {relative}')
    return root


def project_entries(root: Path) -> list[dict]:
    root = unity_root(root)
    store = checked_path(root / STORE)
    if not store.exists():
        return []
    project = identity(store / 'project.json')
    entries_path = checked_path(store / 'entries')
    entries = []
    for path in sorted(entries_path.glob('*.json')):
        entry = read_json(path)
        validate_entry(entry)
        if (path.stem != entry['id'] or
                entry['projectId'] != project['projectId'] or
                entry['projectName'] != project['projectName']):
            raise ValueError(f'feedback identity or filename mismatch: {path}')
        entries.append(entry)
    return entries


def record(args) -> dict:
    root = unity_root(args.project_root)
    manifest_path = checked_path(root / MANIFEST)
    if not manifest_path.is_file():
        raise ValueError('install-manifest.json is missing; install or migrate the harness first')
    manifest = read_json(manifest_path)
    harness = manifest.get('harness')
    if not isinstance(harness, dict):
        raise ValueError('invalid install manifest; missing harness metadata')
    body = (checked_path(args.body_file).read_text(encoding='utf-8')
            if args.body_file else args.body)
    store = checked_path(root / STORE)
    # Validate user input before creating even an empty store.
    entry = {
        'schemaVersion': 1,
        'projectId': str(uuid.uuid4()),
        'projectName': args.project_name if args.project_name is not None else root.name,
        'id': str(uuid.uuid4()),
        'createdAt': now(),
        'category': args.category,
        'title': args.title,
        'body': body,
        'relatedId': args.related_id,
        'harness': {
            'release': harness.get('release'),
            'releaseTag': harness.get('releaseTag'),
            'installManifestSha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        },
    }
    validate_entry(entry)
    with lock(store):
        project_path = checked_path(store / 'project.json')
        if project_path.exists():
            project = identity(project_path)
            if args.project_name is not None and args.project_name != project['projectName']:
                raise ValueError('project-name is fixed after the first record')
        else:
            if (store / 'entries').exists():
                raise ValueError('project.json is missing from an existing feedback store')
            project = {key: entry[key] for key in ('schemaVersion', 'projectId', 'projectName')}
            write_new(project_path, project)
        entry.update(project)
        if args.related_id and not any(
                previous['id'] == args.related_id for previous in project_entries(root)):
            raise ValueError('related-id is not recorded in this project')
        relative = STORE / 'entries' / f"{entry['id']}.json"
        write_new(root / relative, entry)
    return {'recorded': 1, 'id': entry['id'], 'path': relative.as_posix()}


def export(args) -> dict:
    entries = project_entries(args.project_root)
    output = checked_path(args.output)
    with lock(output.parent):
        write_new(output, {'schemaVersion': 1, 'kind': BUNDLE_KIND, 'entries': entries})
    return {'exported': len(entries)}


def source_entries(source: Path) -> list[dict]:
    source = checked_path(source)
    if source.is_dir():
        return project_entries(source)
    bundle = read_json(source)
    fields(bundle, {'schemaVersion', 'kind', 'entries'})
    schema(bundle)
    if bundle['kind'] != BUNDLE_KIND or not isinstance(bundle['entries'], list):
        raise ValueError('invalid feedback bundle')
    for entry in bundle['entries']:
        validate_entry(entry)
    return bundle['entries']


def validate_receipt(receipt: dict) -> None:
    fields(receipt, {'schemaVersion', 'importedAt', 'sha256', 'entry'})
    schema(receipt)
    timestamp(receipt['importedAt'])
    validate_entry(receipt['entry'])
    if receipt['sha256'] != digest(receipt['entry']):
        raise ValueError('imported feedback SHA-256 mismatch')


def plan_import(root: Path, entries: list[dict]) -> tuple[list, int]:
    pending = {}
    skipped = 0
    for entry in entries:
        key = (entry['projectId'], entry['id'])
        relative = INBOX / key[0] / f'{key[1]}.json'
        path = checked_path(root / relative)
        if key in pending:
            previous = pending[key][1]
        elif path.exists():
            receipt = read_json(path)
            validate_receipt(receipt)
            previous = receipt['entry']
        else:
            pending[key] = (relative, entry)
            continue
        if previous != entry:
            raise ValueError(f'feedback ID conflict: {key[0]}/{key[1]}; '
                             'record corrections under a new ID')
        skipped += 1
    return list(pending.values()), skipped


def import_feedback(args) -> dict:
    root = checked_path(args.harness_root)
    if (not (root / 'scripts/install.py').is_file() or
            not (root / 'scripts/validate_repository.py').is_file() or
            (root / MANIFEST).exists()):
        raise ValueError('--harness-root must be a harness source checkout, not an installed game')
    entries = []
    for source in args.source:
        entries.extend(source_entries(source))
    # Preflight every source and destination before starting any import writes.
    pending, skipped = plan_import(root, entries)
    if not args.dry_run and pending:
        with lock(root / INBOX):
            pending, skipped = plan_import(root, entries)
            for relative, entry in pending:
                write_new(root / relative, {
                    'schemaVersion': 1, 'importedAt': now(),
                    'sha256': digest(entry), 'entry': entry,
                })
    return {
        'wouldImport' if args.dry_run else 'imported': len(pending),
        'skipped': skipped,
        'items': [{'projectId': entry['projectId'], 'id': entry['id'],
                   'path': relative.as_posix()} for relative, entry in pending],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('record', help='Append feedback in an installed Unity project')
    add.add_argument('--project-root', type=Path, required=True)
    add.add_argument('--project-name', help='Stable display name; only set on first record')
    add.add_argument('--category', choices=CATEGORIES, default='improvement')
    add.add_argument('--title', required=True)
    body = add.add_mutually_exclusive_group(required=True)
    body.add_argument('--body')
    body.add_argument('--body-file', type=Path)
    add.add_argument('--related-id', help='Previous feedback UUID for a correction or follow-up')
    listing = commands.add_parser('list', help='List project feedback as JSON')
    listing.add_argument('--project-root', type=Path, required=True)
    bundle = commands.add_parser('export', help='Write a portable JSON bundle without overwriting')
    bundle.add_argument('--project-root', type=Path, required=True)
    bundle.add_argument('--output', type=Path, required=True)
    importer = commands.add_parser('import', help='Import only new feedback into the harness')
    importer.add_argument('--harness-root', type=Path, required=True)
    importer.add_argument('--source', type=Path, action='append', required=True,
                          help='Unity project root or exported JSON bundle; repeatable')
    importer.add_argument('--dry-run', action='store_true')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        if args.command == 'record':
            result = record(args)
        elif args.command == 'list':
            result = {'entries': project_entries(args.project_root)}
        elif args.command == 'export':
            result = export(args)
        else:
            result = import_feedback(args)
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
