"""Offline behavioral checks. Run: python3 -m unittest discover -s scripts -v"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pd_data import Scope, url_parts


class DataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = self.root / 'scope.json'
        self.config.write_text(json.dumps({'suffixes': ['example.com'], 'deny_hosts': ['private.example.com'],
                                           'schemes': ['https'], 'ports': [443]}))
        self.scope = Scope(self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, data=''):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('pd_data.py')), *args,
                               '--scope', str(self.config)], input=data, text=True, capture_output=True)

    def test_scope_boundaries(self):
        for url in ['https://example.com/', 'https://app.example.com/a', 'https://APP.example.com:443/a']:
            self.assertIsNotNone(self.scope.accept(url))
        for url in ['https://notexample.com/', 'https://example.com.evil.test/', 'https://example.com@evil.test/',
                    'https://user@example.com/', 'https://private.example.com/', 'http://app.example.com/',
                    'https://app.example.com:8443/', 'https://app.example.com:0/', 'https://app.example.com:/',
                    'https://app.example.com\\@evil.test/', 'https://app.example.com/\nx', '//app.example.com/']:
            self.assertIsNone(self.scope.accept(url), url)

    def test_exact_host_is_not_wildcard(self):
        self.config.write_text(json.dumps({'hosts': ['example.com']}))
        exact = Scope(self.config)
        self.assertEqual(exact.accept('example.com', 'hosts'), 'example.com')
        self.assertIsNone(exact.accept('sub.example.com', 'hosts'))

    def test_url_identity_preserved(self):
        original = 'https://APP.example.com:443/A//b%2Fc/?x=1&x=2&blank=#route'
        self.assertEqual(url_parts(original)[0], 'https://app.example.com/A//b%2Fc/?x=1&x=2&blank=')
        self.assertEqual(url_parts('https://example.com/a?')[0], 'https://example.com/a?')

    def test_ipv6_and_idna(self):
        self.assertEqual(url_parts('https://[2001:db8::1]:8443/a')[3], 'https://[2001:db8::1]:8443')
        self.assertEqual(url_parts('https://bücher.example/')[1], 'xn--bcher-kva.example')

    def test_method_and_provenance(self):
        rows = [
            {'url': 'https://app.example.com/api/items?id=1&id=2', 'method': 'GET', 'source': 'katana'},
            {'url': 'https://app.example.com/api/items?id=1&id=2', 'method': 'GET', 'source': 'capture'},
            {'url': 'https://app.example.com/api/items?id=1&id=2', 'method': 'POST', 'source': 'schema'},
            {'url': 'https://app.example.com/api/items?id=1&id=2', 'source': 'archive'},
            {'url': 'https://private.example.com/api/items', 'source': 'archive'},
            {'url': 'https://app.example.com/api/items?id=1&id=2', 'method': 'GET', 'auth_context': 'user'},
        ]
        result = self.run_cli('inventory', '--output', str(self.root / 'out'), data='\n'.join(map(json.dumps, rows)))
        self.assertEqual(result.returncode, 0, result.stderr)
        records = [json.loads(x) for x in (self.root / 'out/inventory.jsonl').read_text().splitlines()]
        self.assertEqual(len(records), 4)
        get = next(x for x in records if x['method'] == 'GET' and x['auth_context'] == 'unspecified')
        self.assertEqual(len(get['observations']), 2)
        self.assertEqual(get['query_keys'], ['id'])
        self.assertIn('UNKNOWN', {x['method'] for x in records})
        self.assertEqual(json.loads(result.stdout)['rejected_events'], 1)

    def test_path_limit_and_scope(self):
        origins = self.root / 'origins.txt'
        origins.write_text('https://app.example.com\n')
        limited = self.run_cli('paths', '--origins', str(origins), '--limit', '1', data='/api\n/docs\n')
        self.assertEqual(limited.returncode, 2)
        self.assertEqual(limited.stdout, '')
        invalid = self.run_cli('paths', '--origins', str(origins), data='/api\n//evil.test/path\n')
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, '')
        self.config.write_text(json.dumps({'hosts': ['app.example.com'], 'allow_url_regex': [r'^https://app\.example\.com/api(?:/|$)']}))
        result = self.run_cli('paths', '--origins', str(origins), data='/api\n/docs\n')
        self.assertEqual(result.stdout, 'https://app.example.com/api\n')

    def test_fail_closed_scope(self):
        for config in [{}, {'hosts': ['example.com'], 'port': [443]}, {'hosts': ['example.com'], 'ports': [True]},
                       {'suffixes': ['127.0.0.1']}, {'hosts': ['example.com'], 'schemes': ['ftp']}]:
            self.config.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                Scope(self.config)


if __name__ == '__main__':
    unittest.main()
