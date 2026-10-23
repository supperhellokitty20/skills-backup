"""Offline verification of every installed bibliography record and asset."""
import collections
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'references' / name).read_text(encoding='utf-8'))


def verify():
    catalog = read('catalog.json')
    assets = read('assets.json')
    files = read('repository-files.json')
    expected = read('verification-ledger.json')
    assert catalog['source']['commit'] == expected['commit']
    records = catalog['records']
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids)) == expected['record_count']
    assert sorted(ids) == expected['record_ids'], 'Record identity coverage mismatch'
    urls = [r['url'] for r in catalog['references']]
    assert len(urls) == len(set(urls)) == expected['reference_count']
    assert sorted(urls) == expected['manifest_urls'], 'Manifest URL coverage mismatch'
    paths = [r['path'] for r in assets['assets']]
    assert len(paths) == len(set(paths)) == expected['asset_count']
    assert sorted(paths) == expected['asset_paths'], 'Preserved asset coverage mismatch'
    assert len(files['files']) == expected['repository_file_count']
    assert len(catalog['collections']) == expected['collection_count']
    assert sum(c['count'] for c in catalog['collections']) == len(records)
    assert dict(collections.Counter(r['year'] for r in records)) == expected['collection_counts']
    assert dict(collections.Counter(r['section'] for r in records)) == expected['section_counts']
    for row in records:
        assert row['preliminary'] == (row['year'] == '2026-ai')
        assert row['sources'] and row['originalUrl']
        assert 'summary' not in row and 'note' not in row
        if row['preliminary']:
            assert row['rank'] is None and row['section'] == 'candidate'
        for source in row['sources']:
            assert source['url'].startswith(('http://', 'https://'))
            assert 'summary' not in source.get('details', {})
    for ref in catalog['references']:
        assert not {'summary', 'digest', 'steps', 'text'}.intersection(ref)
    linked_paths = {r[key] for r in catalog['references'] for key in ('mdPath', 'pdfPath', 'translationPath') if r.get(key)}
    available = {r['path'] for r in files['files']}
    assert sorted(linked_paths - available) == catalog['coverage']['missing_asset_paths']
    assert not catalog['coverage']['full_article_bodies_included']
    for name, digest in expected['file_sha256'].items():
        actual = hashlib.sha256((ROOT / 'references' / name).read_bytes()).hexdigest()
        assert actual == digest, 'Changed data file: ' + name
    return {'verified': True, 'commit': expected['commit'],
            'record_count': len(ids), 'reference_count': len(urls),
            'asset_count': len(paths), 'collection_count': len(catalog['collections']),
            'missing_archive_path_count': len(catalog['coverage']['missing_asset_paths']),
            'full_article_bodies_included': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
