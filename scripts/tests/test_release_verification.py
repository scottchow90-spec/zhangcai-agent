"""Failure-path tests use synthetic ZIP fixtures, never substitute release assets."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_skill14_archives import verify


class ArchiveChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='zhangcai-archive-fixture-')
        self.root = Path(self.temp.name)
        self.archives = self.root / 'skill-archives'
        self.archives.mkdir()
        (self.root / 'config').mkdir()
        self.skills = [{'id': f'fixture-{i}', 'archive': f'fixture-{i}.zip'} for i in range(14)]
        for skill in self.skills:
            with zipfile.ZipFile(self.archives / skill['archive'], 'w') as bundle:
                bundle.writestr('fixture/SKILL.md', '---\nname: fixture\ndescription: Synthetic test only\n---\nTest body.\n')
        self.write_lock()

    def tearDown(self):
        self.temp.cleanup()

    def write_lock(self):
        lock = []
        for skill in self.skills:
            raw = (self.archives / skill['archive']).read_bytes()
            lock.append({**skill, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        (self.root / 'config/skill14-catalog.json').write_text(json.dumps({'skills': self.skills}))
        (self.root / 'config/skill14-archive-lock.json').write_text(json.dumps({'archives': lock}))

    def test_complete_fixture_is_accepted(self):
        report = verify(self.root, self.archives)
        self.assertEqual(report['status'], 'CLEAN_PASS')
        self.assertEqual(report['checked_count'], 14)

    def test_missing_archive_blocks_release(self):
        (self.archives / self.skills[0]['archive']).unlink()
        report = verify(self.root, self.archives)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual(report['checked_count'], 13)
        self.assertIn('missing archive', report['errors'][0])

    def test_changed_bytes_block_release(self):
        with (self.archives / self.skills[0]['archive']).open('ab') as stream:
            stream.write(b'changed')
        report = verify(self.root, self.archives)
        self.assertIn('hash/size mismatch', report['errors'][0])

    def test_crc_corruption_blocks_even_with_matching_outer_hash(self):
        path = self.archives / self.skills[0]['archive']
        raw = bytearray(path.read_bytes())
        name_length, extra_length = struct.unpack_from('<HH', raw, 26)
        raw[30 + name_length + extra_length] ^= 1
        path.write_bytes(raw)
        self.write_lock()
        report = verify(self.root, self.archives)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('CRC', report['errors'][0])

    def test_traversal_is_rejected_without_writing_outside_staging(self):
        path = self.archives / self.skills[0]['archive']
        with zipfile.ZipFile(path, 'a') as bundle:
            bundle.writestr('../escape.txt', 'must not escape')
        self.write_lock()
        report = verify(self.root, self.archives)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('不安全路径', report['errors'][0])
        self.assertFalse((self.root.parent / 'escape.txt').exists())

    def test_duplicate_ids_cannot_claim_fourteen(self):
        self.skills[-1] = self.skills[0]
        self.write_lock()
        with self.assertRaisesRegex(ValueError, 'fourteen unique IDs'):
            verify(self.root, self.archives)


if __name__ == '__main__':
    unittest.main()
