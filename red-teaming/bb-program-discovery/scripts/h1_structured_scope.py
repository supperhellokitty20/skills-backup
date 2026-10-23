#!/usr/bin/env python3
"""Pull a program's structured scope from HackerOne — unauthenticated, read-only.

Why this instead of scraping the scope page: HackerOne renders scope in collapsed tier groups,
so the HTML shows group headers with the asset rows hidden. The same data is machine-readable
from the public `team(handle:)` query, per asset: identifier, type, bounty/submission eligibility,
`instruction` (tier gating, banned flows, testing prerequisites) and `updated_at`. That is exactly
what `scope.md` needs, and it beats retyping an asset list by hand.

Usage:
    h1_structured_scope.py <handle> [<handle> ...]

Writes scans/h1_<handle>_scope.json (RAW — keep it unfiltered) and prints a compact table.
One POST per handle; nothing is sent to the target itself. Run this before the first active
request in an engagement.
"""
import json
import sys
import urllib.request
from pathlib import Path

QUERY = """
query Scope($h: String!) {
  team(handle: $h) {
    name
    handle
    state
    submission_state
    structured_scopes(first: 200) {
      edges {
        node {
          asset_identifier
          asset_type
          eligible_for_bounty
          eligible_for_submission
          instruction
          max_severity
          updated_at
          confidentiality_requirement
          integrity_requirement
          availability_requirement
        }
      }
    }
  }
}
"""

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/126 Safari/537.36")


def fetch(handle: str) -> str:
    body = json.dumps({"query": QUERY, "variables": {"h": handle}}).encode()
    req = urllib.request.Request(
        "https://hackerone.com/graphql",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": UA,
            "Origin": "https://hackerone.com",
            "Referer": f"https://hackerone.com/{handle}/policy_scopes",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    outdir = Path("scans")
    outdir.mkdir(parents=True, exist_ok=True)
    for handle in sys.argv[1:]:
        try:
            raw = fetch(handle)
        except Exception as e:  # network/auth failure is a blocker, not an empty scope
            print(f"## {handle}: REQUEST FAILED: {e!r}")
            continue
        path = outdir / f"h1_{handle}_scope.json"
        path.write_text(raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"## {handle}: non-JSON response ({len(raw)} bytes) -> {path}")
            continue
        if data.get("errors"):
            print(f"## {handle}: API ERROR: {json.dumps(data['errors'])[:300]}")
            continue
        team = (data.get("data") or {}).get("team")
        if not team:
            print(f"## {handle}: no team object (private, renamed, or not a public program)")
            continue
        nodes = [e["node"] for e in team["structured_scopes"]["edges"]]
        print(f"## {handle} ({team.get('name')}) assets={len(nodes)} state={team.get('state')}")
        for n in nodes:
            bounty = "PAID" if n["eligible_for_bounty"] else "vdp "
            print(f"  [{bounty}] {n['asset_type']:<12} {n['asset_identifier'][:80]:<80} "
                  f"upd={str(n['updated_at'])[:10]}")
            if n.get("instruction"):
                print(f"           note: {' '.join(n['instruction'].split())[:220]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
