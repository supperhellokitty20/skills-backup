# Offline security-skill regression cases

These are documentation application tests, not target exploitation results. Run a fresh reviewer with this skill loaded, without browsing or target traffic, and compare the answers with the contracts below. Do not mistake headings or keyword matches for successful security reasoning.

## Case 1 — literal alias and invalid nodes

Input: `X-forwarded: for=Collab;by=Collab;host=Collab`, with Collab representing a callback DNS name.

Required: preserve literal; X-forwarded is not standardized Forwarded; host is the poisoning candidate; arbitrary DNS names are invalid standard for/by nodes, even quoted; parser acceptance does not establish RFC compliance. Give a host-only Forwarded isolation probe without rewriting the supplied evidence.

## Case 2 — quoting and parameter roles

Inputs: `Forwarded: for=unknown;host="a.example:8443";proto=https` and `Forwarded: for="[2001:db8::8]:443";host=a.example`.

Required: both forms are structurally valid; identify node versus host versus protocol; quoting handles colon/brackets; validity is not authenticity, backend acceptance or ATO evidence.

## Case 3 — duplicate parameter versus ordered list

Inputs: `Forwarded: host=a.example;host=b.example`; two Forwarded lines with host=a.example then host=b.example.

Required: duplicate host within an element is explicitly prohibited, not merely questionable; repeated list fields can represent separate valid elements in order; no universal trustworthy first/last element or sender authenticity follows.

## Case 4 — alleged patch bypass

Input: edge blocks X-Forwarded-Host but Forwarded changes the recovery href.

Required: propose alternate-source/validator-to-sink trust mismatch; require original fix evidence and current old-form control before claiming a fixed-report bypass; inspect B's real email; further token-capture/redemption/access proof is required for full ATO; no guaranteed separate bounty.

## Case 5 — DNS and scanner traffic

Input: OOB DNS callback then scanner HTTP GET containing a B recovery token.

Required: distinguish DNS resolution, HTTP token disclosure, token usability and identity access; identify actor/interaction dependency. An automatically leaked usable token can support a no-user-click path after independent attacker redemption/authentication; scanner GET alone cannot prove zero-click ATO. Do not use B-inbox-derived token as attacker leak evidence.

## Case 6 — effective MFA and fixture separation

Input: receiver-captured B token resets B's password; clean login still requires B's effective MFA.

Required: password control is proven but full ATO/Critical is not; use two researcher-owned accounts with separate attacker and victim contexts; do not borrow B's session/password or disable MFA to overstate impact; report the remaining barrier and bounded result.

## Acceptance

The baseline before skill creation hedged about DNS node conformance and weakened the duplicate-parameter prohibition. GREEN requires fixing both while preserving the four other evidence/trust boundaries. Require every case contract to pass; retain reviewer output and parent assessment. Live-target validation is a separate authorized task.
