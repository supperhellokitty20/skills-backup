#!/usr/bin/env python3
"""Offline scope gates, endpoint inventories, and bounded path expansion."""
import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit


def host_name(value):
    value = value.lower().rstrip('.')
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        value = value.encode('idna').decode('ascii')
        if len(value) > 253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', x) for x in value.split('.')):
            raise ValueError('invalid hostname')
        return value


def url_parts(value):
    if not isinstance(value, str) or re.search(r'[\s\\\x00-\x1f\x7f]', value):
        raise ValueError('invalid URL characters')
    p = urlsplit(value)
    if p.scheme.lower() not in ('http', 'https') or not p.hostname or p.username is not None or p.password is not None:
        raise ValueError('expected absolute HTTP(S) URL without userinfo')
    host = host_name(p.hostname)
    port = p.port if p.port is not None else (443 if p.scheme.lower() == 'https' else 80)
    if not 1 <= port <= 65535 or p.netloc.endswith(':'):
        raise ValueError('invalid port')
    authority = f'[{host}]' if ':' in host else host
    default = 443 if p.scheme.lower() == 'https' else 80
    if port != default:
        authority += f':{port}'
    origin = f'{p.scheme.lower()}://{authority}'
    url = urlunsplit((p.scheme.lower(), authority, p.path or '/', p.query, ''))
    # urlunsplit drops an empty query marker; retain it for exact request identity.
    if '?' in value.split('#', 1)[0] and not p.query:
        url += '?'
    return url, host, port, origin


class Scope:
    def __init__(self, path):
        self.data = json.loads(Path(path).read_text())
        supported = {'hosts', 'suffixes', 'deny_hosts', 'deny_suffixes', 'schemes', 'ports', 'allow_url_regex', 'deny_url_regex'}
        if not isinstance(self.data, dict) or set(self.data) - supported:
            raise ValueError('unknown scope fields or invalid scope object')
        for k, v in self.data.items():
            if not isinstance(v, list) or any(not isinstance(x, int if k == 'ports' else str) for x in v):
                raise ValueError(f'scope field {k} must be a typed list')
        for k in ('hosts', 'suffixes', 'deny_hosts', 'deny_suffixes'):
            self.data[k] = [host_name(x) for x in self.data.get(k, [])]
        if not self.data['hosts'] and not self.data['suffixes']:
            raise ValueError('scope requires explicit hosts or suffixes')
        for k in ('suffixes', 'deny_suffixes'):
            for x in self.data[k]:
                try:
                    ipaddress.ip_address(x)
                except ValueError:
                    continue
                raise ValueError('IP literals belong in hosts, not suffixes')
        self.allow = [re.compile(x) for x in self.data.get('allow_url_regex', [])]
        self.deny = [re.compile(x) for x in self.data.get('deny_url_regex', [])]
        self.ports = self.data.get('ports', [80, 443])
        self.schemes = self.data.get('schemes', ['http', 'https'])
        if not self.ports or any(type(x) is not int or not 1 <= x <= 65535 for x in self.ports):
            raise ValueError('ports must contain explicit valid port numbers')
        if not self.schemes or set(self.schemes) - {'http', 'https'}:
            raise ValueError('schemes must contain http and/or https')

    def host_ok(self, host):
        def match(exact, suffixes):
            return host in self.data[exact] or any(host == s or host.endswith('.' + s) for s in self.data[suffixes])
        return match('hosts', 'suffixes') and not match('deny_hosts', 'deny_suffixes')

    def accept(self, value, kind='urls'):
        try:
            if kind == 'hosts':
                host = host_name(value)
                return host if self.host_ok(host) else None
            url, host, port, _ = url_parts(value)
            if not self.host_ok(host) or port not in self.ports or urlsplit(url).scheme not in self.schemes:
                return None
            if self.allow and not any(x.search(url) for x in self.allow):
                return None
            if any(x.search(url) for x in self.deny):
                return None
            return url
        except (ValueError, UnicodeError):
            return None


def lines(path):
    if path == '-':
        yield from sys.stdin
    else:
        with open(path) as stream:
            yield from stream


def inventory(args, scope):
    records = {}
    rejected = 0
    for index, line in enumerate(lines(args.input), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get('url'), str):
            raise ValueError(f'event {index} requires a URL string')
        url = scope.accept(row['url'])
        if url is None:
            rejected += 1
            continue
        method = row.get('method') or 'UNKNOWN'
        context = row.get('auth_context') or 'unspecified'
        if not isinstance(method, str) or not re.fullmatch(r'[A-Za-z-]+', method) or not isinstance(context, str):
            raise ValueError(f'event {index} has invalid method/context')
        method = method.upper()
        key = (url, method, context)
        if key not in records:
            p = urlsplit(url)
            file_name = p.path.rsplit('/', 1)[-1]
            ext = Path(file_name).suffix.lower()
            tags = []
            if ext:
                tags.append('file-candidate')
            if ext in ('.js', '.mjs', '.cjs'):
                tags.append('javascript')
            if ext == '.map':
                tags.append('source-map')
            if re.search(r'/(?:api|graphql|graphiql|rest|rpc|v\d+|openapi|swagger)(?:[/.-]|$)', p.path, re.I):
                tags.append('api-candidate')
            records[key] = dict(url=url, method=method, auth_context=context, origin=url_parts(url)[3], path=p.path,
                                query_keys=sorted({k for k, _ in parse_qsl(p.query, keep_blank_values=True)}),
                                tags=tags, observations=[])
        # Preserve complete adapter data; do not turn an HTTP status into existence proof.
        observation = dict(row)
        if observation not in records[key]['observations']:
            records[key]['observations'].append(observation)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    items = [records[k] for k in sorted(records)]
    (out / 'inventory.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items))
    views = {
        'urls.txt': {x['url'] for x in items},
        'origins.txt': {x['origin'] for x in items},
        'files.txt': {x['url'] for x in items if 'file-candidate' in x['tags']},
        'javascript.txt': {x['url'] for x in items if 'javascript' in x['tags']},
        'api-candidates.txt': {x['url'] for x in items if 'api-candidate' in x['tags']},
        'parameterized.txt': {x['url'] for x in items if x['query_keys']},
    }
    for name, values in views.items():
        (out / name).write_text(''.join(x + '\n' for x in sorted(values)))
    summary = {'operations': len(items), 'rejected_events': rejected, **{k: len(v) for k, v in views.items()}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    gate = sub.add_parser('scope', help='Filter plain hosts or URLs from stdin/file; counts on stderr')
    gate.add_argument('--kind', choices=['hosts', 'urls'], default='urls')
    inv = sub.add_parser('inventory', help='Convert normalized endpoint-event JSONL into inventories')
    inv.add_argument('--output', required=True, help='Dedicated output directory; generated views are replaced')
    paths = sub.add_parser('paths', help='Expand root-relative paths across scoped origins, offline')
    paths.add_argument('--origins', required=True)
    paths.add_argument('--limit', type=int, default=1000, help='Maximum product size; fail before producing output')
    for command in (gate, inv, paths):
        command.add_argument('--scope', required=True, help='Scope JSON; see references/operations.md')
        command.add_argument('--input', default='-', help='Input file, default stdin')
    args = parser.parse_args()
    scope = Scope(args.scope)
    if args.command == 'inventory':
        inventory(args, scope)
    elif args.command == 'scope':
        accepted, rejected = set(), 0
        for line in lines(args.input):
            value = line.rstrip('\r\n')
            if not value:
                continue
            result = scope.accept(value, args.kind)
            if result is None:
                rejected += 1
            else:
                accepted.add(result)
        for value in sorted(accepted):
            print(value)
        print(json.dumps({'accepted_unique': len(accepted), 'rejected': rejected}), file=sys.stderr)
    else:
        origins = set()
        for line in lines(args.origins):
            value = line.strip()
            if not value:
                continue
            _, host, port, origin = url_parts(value)
            if not scope.host_ok(host) or port not in scope.ports or urlsplit(origin).scheme not in scope.schemes:
                raise ValueError('origin outside host/scheme/port scope')
            if urlsplit(value).path not in ('', '/') or urlsplit(value).query or urlsplit(value).fragment:
                raise ValueError('expected origin without path/query/fragment')
            origins.add(origin)
        candidates = {x.strip() for x in lines(args.input) if x.strip()}
        if args.limit < 1 or len(origins) * len(candidates) > args.limit:
            raise ValueError('path product exceeds limit; select a smaller batch')
        for path in candidates:
            if not path.startswith('/') or path.startswith('//') or re.search(r'[\s\\#\x00-\x1f\x7f]', path):
                raise ValueError('expected root-relative path without fragment')
        for url in sorted({result for origin in origins for path in candidates if (result := scope.accept(origin + path))}):
            print(url)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, re.error) as exc:
        print(f'pd_data: {exc}', file=sys.stderr)
        sys.exit(2)
