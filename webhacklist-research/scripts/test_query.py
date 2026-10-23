"""Exercise the installed reference CLI, offline, against real metadata."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/query.py'


def call(*args):
    proc = subprocess.run(['python3', str(CLI), *args], text=True, capture_output=True)
    if proc.returncode:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


class OfflineRetrieval(unittest.TestCase):
    def test_complete_catalogue_is_queryable_without_network(self):
        self.assertTrue(CLI.exists(), 'Missing offline catalogue lookup helper')
        stats = call('stats')
        self.assertEqual(stats['record_count'], 2082)
        records = call('search', '--limit', '0')
        self.assertEqual(records['total'], 2082)
        self.assertEqual(records['returned'], 2082)
        self.assertFalse(records['truncated'])
        ai = call('search', '--year', '2026-ai', '--limit', '0')
        self.assertEqual(ai['total'], 299)
        self.assertTrue(all(r['preliminary'] and r['rank'] is None for r in ai['results']))
        lead = call('search', 'HTTP Terminator', '--year', '2026-ai')
        self.assertEqual(lead['total'], 1)
        self.assertIn('Can AI do novel security research?', lead['results'][0]['title'])
        detail = call('show', lead['results'][0]['id'])
        self.assertEqual(detail['originalUrl'], 'https://portswigger.net/research/can-ai-do-novel-security-research')
        self.assertEqual(len(detail['sources']), 6)
        self.assertTrue(detail['sources'][0]['mdExists'])
        winners = call('search', '--section', 'winner', '--limit', '0')
        self.assertEqual(winners['total'], 190)
        limited = call('search', '--limit', '3')
        self.assertEqual(limited['returned'], 3)
        self.assertTrue(limited['truncated'])
        refs = call('refs', '--limit', '0')
        self.assertEqual(refs['total'], 2778)
        assets = call('assets', '--limit', '0')
        self.assertEqual(assets['total'], stats['asset_count'])
        nohits = call('search', 'no-such-document-4b61970')
        self.assertEqual(nohits['total'], 0)
        fail = subprocess.run(['python3', str(CLI), 'show', 'nonexistent-id'], text=True, capture_output=True)
        self.assertEqual(fail.returncode, 2)
        fail = subprocess.run(['python3', str(CLI), 'search', '--year', '2016'], text=True, capture_output=True)
        self.assertEqual(fail.returncode, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
