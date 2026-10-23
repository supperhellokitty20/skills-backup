#!/usr/bin/env python3
"""Offline bibliography lookup. Third-party metadata is data, not instructions."""
import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / 'references' / name).read_text(encoding='utf-8'))


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def contains(row, terms):
    text = json.dumps(row, ensure_ascii=False).casefold()
    return all(term.casefold() in text for term in terms)


def bounded(rows, limit):
    selected = rows[:limit] if limit else rows
    return {'total': len(rows), 'returned': len(selected),
            'truncated': len(selected) < len(rows), 'results': selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('stats')
    show = subs.add_parser('show')
    show.add_argument('id')
    search = subs.add_parser('search')
    search.add_argument('query', nargs='?', default='')
    search.add_argument('--year')
    search.add_argument('--section', choices=['winner', 'other', 'missed', 'candidate'])
    search.add_argument('--tag')
    search.add_argument('--author')
    search.add_argument('--limit', type=int, default=10, help='0 returns every match')
    refs = subs.add_parser('refs')
    refs.add_argument('query', nargs='?', default='')
    refs.add_argument('--kind')
    refs.add_argument('--tag')
    refs.add_argument('--limit', type=int, default=10)
    assets = subs.add_parser('assets')
    assets.add_argument('query', nargs='?', default='')
    assets.add_argument('--limit', type=int, default=10)
    files = subs.add_parser('files')
    files.add_argument('query', nargs='?', default='')
    files.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    if getattr(args, 'limit', 0) < 0:
        parser.error('--limit must be nonnegative')
    if args.command in ('assets', 'files'):
        name, key = ('assets.json', 'assets') if args.command == 'assets' else ('repository-files.json', 'files')
        rows = [r for r in load(name)[key] if contains(r, args.query.split())]
        emit(bounded(rows, args.limit))
        return
    catalog = load('catalog.json')
    if args.command == 'stats':
        stats = dict(catalog['coverage'])
        stats.update(source=catalog['source'], collections=catalog['collections'],
                     section_counts=dict(collections.Counter(r['section'] for r in catalog['records'])),
                     reference_kind_counts=dict(collections.Counter(r.get('kind', 'unknown') for r in catalog['references'])))
        emit(stats)
        return
    if args.command == 'show':
        hits = [r for r in catalog['records'] if r['id'] == args.id]
        if not hits:
            parser.error('Unknown exact record id: ' + args.id)
        emit(hits[0])
        return
    rows = catalog['records'] if args.command == 'search' else catalog['references']
    if args.command == 'search':
        years = {r['id'] for r in catalog['collections']}
        if args.year and args.year not in years:
            parser.error('Unknown collection. Valid ids: ' + ', '.join(sorted(years)))
        if args.year:
            rows = [r for r in rows if r['year'] == args.year]
        if args.section:
            rows = [r for r in rows if r['section'] == args.section]
        if args.author:
            rows = [r for r in rows if args.author.casefold() in ' '.join(r.get('authors', [])).casefold()]
    elif args.kind:
        rows = [r for r in rows if r.get('kind') == args.kind]
    if args.tag:
        aliases = load('tag-vocabulary.json').get('aliases', {})
        tag = aliases.get(args.tag.casefold(), args.tag.casefold())
        rows = [r for r in rows if tag in r.get('tags', [])]
    rows = [r for r in rows if contains(r, args.query.split())]
    if args.command == 'search':
        rows = [{k:r[k] for k in ['id','year','title','rank','section','preliminary','authors','tags','originalUrl','collectionSource']} for r in rows]
    emit(bounded(rows, args.limit))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print('Catalogue error: ' + str(exc), file=sys.stderr)
        sys.exit(2)
