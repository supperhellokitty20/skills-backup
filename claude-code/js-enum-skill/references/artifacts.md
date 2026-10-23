# Artifact contract

Use these outputs when task asks for thorough or reproducible JavaScript enumeration. Prefix filenames with target identifier when useful.

## Collection

- `subdomains.txt` — normalized in-scope hosts plus discovery source in companion CSV.
- `gau-urls.txt` — raw historical URL collection.
- `javascript-urls.txt` — deduplicated JavaScript candidates.
- `fetch-results.json` — URL, final URL, referrer, source, timestamp, status, content type, bytes, SHA-256, local body name.
- `source-map-urls.txt` — every unique resolved map URL, one per line.
- `historical-source-map-references.csv` — map URL, current status, original JavaScript URL, snapshot timestamp, snapshot URL.

## Reconstruction

- `MAPS.csv` — one row per map: exact URL, parent JavaScript, discovery source, HTTP status, content type, bytes, SHA-256, source count, embedded-content count, first-party count, parse error, reconstructed-file count.
- `FILES.csv` — one row per reconstructed logical file: path, SHA-256, original source names, map count, exact map URLs, variant status.
- `PROVENANCE.csv` — one row per file/map occurrence: reconstructed path, SHA-256, original source name, exact source-map URL.
- `MANIFEST.json` — machine-readable settings, exclusions, conflicts, failures, and nested provenance.
- `PROVENANCE.md` — human-readable list of every processed map plus every reconstructed file and its map URLs.

No map may disappear because it contributed zero first-party files. Record zero contribution explicitly.

## API catalog

Recommended CSV fields:

```text
source_file,line,call_expression,method,base_url,path_expression,resolved_path,auth_context,custom_headers,path_ids,query_fields,body_fields,data_class,risk_tags,test_hypothesis
```

Count call sites and unique normalized operations separately. Preserve unresolved expressions instead of guessing values.

## Secret triage

Recommended evidence fields:

```text
candidate_id,type,source_file,line,source_map_urls,first_seen,last_seen,client_intended,provider,privilege_hypothesis,validation_method,validation_status,http_status,evidence_path,notes
```

Store full values only in access-controlled raw evidence when assessment rules require them. Public reports should use fingerprint plus first/last characters unless disclosure recipient explicitly requires complete value through an approved channel.

## Reporting split

Produce separate sections or files for:

1. Source-map exposure — public accessibility and proprietary source recovery.
2. Secret candidates — contextual classification and validation status.
3. API design inventory — routes and client trust assumptions.
4. Pentest plan — dynamic tests, safety constraints, accounts, expected controls.
5. Confirmed findings — reproducible impact only.

This split prevents source exposure from inheriting severity of an unvalidated credential or API hypothesis.
