# Patchstack Vulnerability Report Template

## Title

`Plugin Name <= version - vulnerability class via affected component`

## Summary

Briefly describe the vulnerable component, affected versions, required privileges, and security impact.

## Scope

- Program:
- Plugin:
- Tested version:
- Source origin:
- Local lab URL:
- Local PoC path:
- Evidence path:
- Required role:
- Vulnerability class:
- CWE:
- Severity:

## Preconditions

List account role, plugin settings, feature enablement, nonce/session requirements, and any environmental assumptions.

## Root Cause

Explain the vulnerable source-to-sink path with file:line references. Include the missing or insufficient nonce, capability check, sanitization, escaping, authorization, allowlist, or path normalization.

## Reproduction

1. Install and activate the tested plugin version in a local WordPress lab.
2. Configure any required plugin settings.
3. Authenticate as the required role, if applicable.
4. Send the minimal request or perform the UI action.
5. Observe the vulnerable behavior.

Include exact local requests, parameters, payloads, and observations. For authenticated flows, describe how the nonce/cookie was obtained in the local lab.

Store the minimal PoC under `poc/<finding-slug>/` in the research workspace and reference that path here.

## Evidence

- Request:
- Response or UI observation:
- Database/filesystem evidence:
- PoC files:
- Relevant source references:
- Reproducibility: `N/N`

## Impact

Describe what an attacker can do from the required role and why it matters. Tie this to concrete outcomes such as stored script execution in an admin context, unauthorized data access, file write/delete, SQL query manipulation, or privilege escalation.

## Remediation

Recommend specific fixes:

- Add or tighten `current_user_can()` checks
- Add nonce validation for state-changing actions
- Use `$wpdb->prepare()` or strict allowlists for SQL
- Sanitize input and escape output in the correct context
- Normalize and constrain filesystem paths
- Restrict upload MIME/extensions and validate file content
- Add REST `permission_callback`

## Notes

Mention duplicates, variants, uncertain version ranges, non-default settings, or anything intentionally not tested.
