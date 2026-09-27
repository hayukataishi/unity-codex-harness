from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/harness_feedback.py'


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


feedback = load_module('harness_feedback')


class HarnessFeedbackTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.create_project('Game A')
        self.harness = self.root / 'harness'
        (self.harness / 'scripts').mkdir(parents=True)
        for name in ('install.py', 'validate_repository.py'):
            (self.harness / 'scripts' / name).touch()

    def create_project(self, name):
        project = self.root / name
        for directory in ('Assets', 'Packages', 'ProjectSettings'):
            (project / directory).mkdir(parents=True)
        (project / 'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.4.10f1\n')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/install.py'), str(project)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return project

    def cli(self, *args, script=CLI, ok=True):
        result = subprocess.run([sys.executable, str(script), *map(str, args)],
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)
        return result.stderr

    def record(self, project=None, *extra):
        project = project or self.project
        return self.cli('record', '--project-root', project, '--title', '改善の提案',
                        '--body', '期待と実際\n再現手順', *extra,
                        script=project / 'scripts/unity_codex_harness/harness_feedback.py')

    def pull(self, *extra, ok=True):
        return self.cli('import', '--harness-root', self.harness, '--source', self.project,
                        *extra, ok=ok)

    def snapshot(self, root):
        return {str(path.relative_to(root)): path.read_bytes()
                for path in root.rglob('*') if path.is_file()}

    def entries(self):
        return sorted((self.project / feedback.STORE / 'entries').glob('*.json'))

    def change_entry(self, change):
        path = self.entries()[0]
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data), encoding='utf-8')

    def test_record_accumulates_stable_identity_and_release(self):
        first = self.record(None, '--project-name', '共有名')
        second = self.record()
        self.assertNotEqual(first['id'], second['id'])
        entries = self.cli('list', '--project-root', self.project)['entries']
        self.assertEqual(len(entries), 2)
        self.assertEqual(len({entry['projectId'] for entry in entries}), 1)
        self.assertTrue(all(entry['projectName'] == '共有名' for entry in entries))
        for entry in entries:
            self.assertEqual(entry['harness']['release'], '0.1.0')
            self.assertEqual(entry['harness']['releaseTag'], 'v0.1.0')
            self.assertNotIn(str(self.root), json.dumps(entry))

    def test_body_file_and_follow_up_preserve_original(self):
        first = self.record()
        original = self.entries()[0].read_bytes()
        body = self.root / 'note.md'
        body.write_text('追記\n詳しい再現手順', encoding='utf-8')
        self.cli('record', '--project-root', self.project, '--title', '訂正',
                 '--body-file', body, '--related-id', first['id'])
        self.assertEqual((self.project / first['path']).read_bytes(), original)
        entries = self.cli('list', '--project-root', self.project)['entries']
        follow_up = next(entry for entry in entries if entry['relatedId'])
        self.assertEqual(follow_up['relatedId'], first['id'])
        self.assertEqual(follow_up['body'], body.read_text())

    def test_import_twice_skips_and_keeps_source_and_receipts_unchanged(self):
        self.record()
        self.record()
        before = self.snapshot(self.project)
        self.assertEqual(self.pull()['imported'], 2)
        receipts = self.snapshot(self.harness)
        self.assertEqual(self.pull(), {'imported': 0, 'skipped': 2, 'items': []})
        self.assertEqual(self.snapshot(self.project), before)
        self.assertEqual(self.snapshot(self.harness), receipts)

    def test_new_entry_after_import_only_imports_new_feedback(self):
        self.record()
        self.pull()
        new = self.record()
        result = self.pull()
        self.assertEqual((result['imported'], result['skipped']), (1, 1))
        self.assertEqual(result['items'][0]['id'], new['id'])

    def test_dry_run_does_not_create_state_or_modify_source(self):
        self.record()
        before = self.snapshot(self.root)
        self.assertEqual(self.pull('--dry-run')['wouldImport'], 1)
        self.assertEqual(self.snapshot(self.root), before)
        self.assertFalse((self.harness / 'feedback').exists())
        self.assertEqual(self.pull()['imported'], 1)

    def test_clone_and_bundle_are_deduplicated_together(self):
        self.record()
        clone = self.root / 'renamed clone'
        shutil.copytree(self.project, clone)
        bundle = self.root / 'bundle.json'
        self.cli('export', '--project-root', clone, '--output', bundle)
        result = self.pull('--source', clone, '--source', bundle)
        self.assertEqual((result['imported'], result['skipped']), (1, 2))
        shutil.rmtree(self.project)
        result = self.cli('import', '--harness-root', self.harness, '--source', bundle)
        self.assertEqual((result['imported'], result['skipped']), (0, 1))

    def test_different_projects_with_same_feedback_id_remain_distinct(self):
        first = self.record()
        other = self.create_project('Game B')
        second = self.record(other)
        path = other / second['path']
        entry = json.loads(path.read_text())
        entry['id'] = first['id']
        path.unlink()
        (path.parent / f"{first['id']}.json").write_text(json.dumps(entry))
        result = self.pull('--source', other)
        self.assertEqual(result['imported'], 2)
        self.assertEqual(len({item['projectId'] for item in result['items']}), 2)

    def test_same_id_changed_content_stops_before_importing_any_new_entry(self):
        self.record()
        self.pull()
        self.change_entry(lambda entry: entry.update(body='改変'))
        self.record()
        before = self.snapshot(self.harness)
        self.assertIn('ID conflict', self.pull(ok=False))
        self.assertEqual(self.snapshot(self.harness), before)

    def test_conflicting_sources_rejected_before_first_write(self):
        self.record()
        bundle = self.root / 'bundle.json'
        self.cli('export', '--project-root', self.project, '--output', bundle)
        self.change_entry(lambda entry: entry.update(title='変更'))
        self.assertIn('ID conflict', self.pull('--source', bundle, ok=False))
        self.assertFalse((self.harness / 'feedback').exists())

    def test_formatting_changes_do_not_cause_reimport(self):
        self.record()
        self.pull()
        self.change_entry(lambda entry: None)
        self.assertEqual(self.pull()['skipped'], 1)

    def test_malformed_source_after_valid_source_causes_no_writes(self):
        self.record()
        malformed = self.root / 'bad.json'
        malformed.write_text('{bad JSON')
        self.pull('--source', malformed, ok=False)
        self.assertFalse((self.harness / 'feedback').exists())

    def test_invalid_schema_id_and_types_are_rejected(self):
        self.record()
        path = self.entries()[0]
        original = path.read_text()
        for key, value in [('schemaVersion', 2), ('schemaVersion', True),
                           ('projectId', '../outside'), ('id', 'bad'),
                           ('createdAt', 'not-a-date'), ('title', ''),
                           ('body', []), ('harness', []), ('category', 'invalid')]:
            with self.subTest(key=key, value=value):
                path.write_text(original)
                self.change_entry(lambda entry: entry.update({key: value}))
                self.pull(ok=False)
                self.assertFalse((self.harness / 'feedback').exists())

    def test_duplicate_json_keys_are_rejected(self):
        self.record()
        path = self.entries()[0]
        path.write_text(path.read_text().replace('"schemaVersion": 1',
                                                '"schemaVersion": 1, "schemaVersion": 1'))
        self.assertIn('duplicate JSON key', self.pull(ok=False))

    def test_corrupt_receipt_is_not_treated_as_successfully_imported(self):
        self.record()
        result = self.pull()
        path = self.harness / result['items'][0]['path']
        receipt = json.loads(path.read_text())
        receipt['entry']['body'] = 'corrupted'
        path.write_text(json.dumps(receipt))
        before = self.snapshot(self.harness)
        self.assertIn('SHA-256 mismatch', self.pull(ok=False))
        self.assertEqual(before, self.snapshot(self.harness))

    def test_retry_after_partial_io_failure_imports_remaining_only(self):
        self.record()
        self.record()
        args = feedback.parse_args(['import', '--harness-root', str(self.harness),
                                    '--source', str(self.project)])
        real_write = feedback.write_new
        calls = 0

        def fail_second(path, value):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated disk failure')
            return real_write(path, value)

        with patch.object(feedback, 'write_new', side_effect=fail_second):
            with self.assertRaises(OSError):
                feedback.import_feedback(args)
        self.assertFalse((self.harness / feedback.INBOX / '.feedback.lock').exists())
        result = self.pull()
        self.assertEqual((result['imported'], result['skipped']), (1, 1))

    def test_failed_atomic_publish_leaves_no_receipt_or_temp_file(self):
        self.record()
        args = feedback.parse_args(['import', '--harness-root', str(self.harness),
                                    '--source', str(self.project)])
        with patch.object(feedback.os, 'replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                feedback.import_feedback(args)
        self.assertEqual(list((self.harness / feedback.INBOX).rglob('*.json')), [])
        self.assertEqual(list((self.harness / feedback.INBOX).rglob('*.tmp')), [])
        self.assertEqual(self.pull()['imported'], 1)

    def test_lock_rejects_concurrent_writer_without_stealing_lock(self):
        self.record()
        lock = self.harness / feedback.INBOX / '.feedback.lock'
        lock.mkdir(parents=True)
        self.assertIn('locked', self.pull(ok=False))
        self.assertTrue(lock.is_dir())
        self.assertEqual(list((self.harness / feedback.INBOX).rglob('*.json')), [])

    def test_symlink_in_source_and_destination_is_rejected(self):
        self.record()
        path = self.entries()[0]
        moved = self.root / 'moved.json'
        path.rename(moved)
        path.symlink_to(moved)
        self.assertIn('symlink', self.pull(ok=False))
        path.unlink()
        moved.rename(path)
        external = self.root / 'external'
        external.mkdir()
        (self.harness / 'feedback').symlink_to(external, target_is_directory=True)
        self.assertIn('symlink', self.pull(ok=False))
        self.assertEqual(list(external.iterdir()), [])

    def test_filename_and_project_identity_mismatch_are_rejected(self):
        self.record()
        self.change_entry(lambda entry: entry.update(id=str(uuid.uuid4())))
        self.assertIn('mismatch', self.pull(ok=False))

    def test_empty_project_and_bundle_are_noops(self):
        self.assertEqual(self.pull()['imported'], 0)
        bundle = self.root / 'empty.json'
        self.assertEqual(self.cli('export', '--project-root', self.project,
                                  '--output', bundle)['exported'], 0)
        self.assertEqual(self.pull('--source', bundle)['imported'], 0)
        self.assertFalse((self.harness / 'feedback').exists())

    def test_export_does_not_overwrite_existing_bundle(self):
        self.record()
        bundle = self.root / 'bundle.json'
        self.cli('export', '--project-root', self.project, '--output', bundle)
        before = bundle.read_bytes()
        self.cli('export', '--project-root', self.project, '--output', bundle, ok=False)
        self.assertEqual(bundle.read_bytes(), before)

    def test_record_requires_installed_project_and_nonempty_body(self):
        self.cli('record', '--project-root', self.project, '--title', 'x', '--body', ' ', ok=False)
        self.assertFalse((self.project / feedback.STORE).exists())
        (self.project / feedback.MANIFEST).unlink()
        self.assertIn('install-manifest', self.cli('record', '--project-root', self.project,
                       '--title', 'x', '--body', 'x', ok=False))

    def test_installer_update_preserves_feedback_and_integrity(self):
        self.record()
        before = self.snapshot(self.project / feedback.STORE)
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/install.py'),
                                 str(self.project), '--force'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(self.project / feedback.STORE), before)
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_harness_integrity.py'),
                                 '--project-root', str(self.project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((self.project / feedback.MANIFEST).read_text())
        managed = {item['path']: item['ownership'] for item in manifest['files']}
        for path in ('scripts/unity_codex_harness/harness_feedback.py',
                     '.agents/skills/manage-harness-feedback/SKILL.md',
                     'docs/unity_harness_feedback.md'):
            self.assertEqual(managed[path], 'harness-managed')
        self.assertFalse(any(path.startswith(str(feedback.STORE)) for path in managed))
        self.assertFalse((self.project / 'feedback/imported').exists())

    def test_imported_data_is_excluded_from_install_and_release(self):
        self.record()
        self.pull()
        shutil.copy(ROOT / 'harness.release.json', self.harness)
        installer = load_module('install')
        builder = load_module('build_release')
        install_paths = {item.relative for item in installer.source_files(self.harness, False)}
        release_paths = set(builder.release_files(self.harness))
        for paths in (install_paths, release_paths):
            self.assertFalse(any(path.parts[0] == 'feedback' for path in paths))
        self.assertIn(Path('docs/unity_harness_feedback.md'), release_paths)

    def test_installed_game_cannot_be_import_destination(self):
        self.record()
        self.assertIn('source checkout', self.cli('import', '--harness-root', self.project,
                      '--source', self.project, ok=False))


if __name__ == '__main__':
    unittest.main()
