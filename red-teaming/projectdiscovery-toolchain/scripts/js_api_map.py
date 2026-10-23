#!/usr/bin/env python3
"""Build an API surface map from a downloaded client-side JS bundle.

Offline by design: reads files already on disk and sends no requests, so it can run
against a bundle captured under the engagement's scans/ directory.

Usage:
    python3 js_api_map.py scans/root/app.js
    python3 js_api_map.py --json scans/root/app.js > api_map.json

Emits the HTTP call sites (grouped by service prefix), every host the bundle references,
and config key/value pairs that look like a gateway base URL or a client-shipped key.
Vendor chunks are labelled, because their call sites are library code and their routes are
not the application's.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

# App-code call sites: .get("/path") / .post("/path") ... and axios url: "/path"
CALL = re.compile(r"""\.(get|post|put|patch|delete)\(\s*["'`](/[A-Za-z0-9_/{}.\-$:]{3,})""")
URL_KV = re.compile(r"""url:\s*["'`](/[A-Za-z0-9_/{}.\-$:]{3,})""")
HOST = re.compile(r"https?://([a-z0-9.\-]+\.[a-z]{2,})", re.I)
# Gateway / API client config: base URLs and client-shipped keys
CONFIG = re.compile(
    r"""(gatewayUrl|gatewayUrlUk|gatewaySubscriptionKey|subscriptionKey|baseURL|baseUrl"""
    r"""|apiUrl|apiKey|clientId|merchantId)\s*[:=]\s*["'`]([^"'`]{1,140})"""
)
VENDOR = re.compile(r"(chunk-?vendors|vendors?|polyfill|runtime)", re.I)


def analyse(path: str) -> dict:
    with open(path, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    calls: collections.Counter = collections.Counter()
    for m in CALL.finditer(src):
        calls[(m.group(1).upper(), m.group(2))] += 1
    for m in URL_KV.finditer(src):
        calls[("URL", m.group(1))] += 1
    by_service: dict[str, list[str]] = collections.defaultdict(list)
    for method, route in calls:
        by_service["/" + route.strip("/").split("/")[0]].append(method)
    return {
        "file": path,
        "bytes": len(src),
        "vendor_chunk": bool(VENDOR.search(os.path.basename(path))),
        "calls": {f"{m} {r}": n for (m, r), n in sorted(calls.items())},
        "by_service": {k: sorted(set(v)) for k, v in sorted(by_service.items())},
        "hosts": dict(collections.Counter(HOST.findall(src)).most_common()),
        "config": dict(sorted(set(CONFIG.findall(src)))),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundles", nargs="+", help="path(s) to downloaded .js files")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    results = []
    for path in args.bundles:
        if not os.path.isfile(path):
            print(f"[skip] not a file: {path}", file=sys.stderr)
            continue
        results.append(analyse(path))

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
        return 0

    for r in results:
        tag = "  [VENDOR CHUNK - call sites are library code]" if r["vendor_chunk"] else ""
        print(f"\n=== {r['file']} ({r['bytes']} B){tag} ===")
        print(f"-- call sites ({len(r['calls'])} unique; ${'{'}id{'}'} params are IDOR candidates) --")
        for route, n in r["calls"].items():
            print(f"   {n:4d}  {route}")
        print("-- service prefixes --")
        for prefix, methods in r["by_service"].items():
            print(f"   {prefix:<28} {' '.join(methods)}")
        print("-- hosts referenced --")
        for host, n in r["hosts"].items():
            print(f"   {n:4d}  {host}")
        if r["config"]:
            print("-- gateway / key config --")
            for key, value in r["config"].items():
                print(f"   {key} = {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
