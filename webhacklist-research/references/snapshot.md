# Snapshot and exhaustive coverage

Source site: https://webhacklist.com/
Source repository: https://github.com/irsdl/webhacklist
Pinned commit: `fe6f2609d3db4d999e10683397b2d2820d1d2dad`
Source manifest update: `2026-10-12T11:47:48+00:00`
2026 collection as-of date: `2026-10-12`

The live homepage refused the initial direct HTTP request. This index was therefore derived from the site's public canonical repository, not from a claimed successful crawl of the rendered homepage. The site's own Node catalogue builder was run against one pinned snapshot and its `--check` verification passed. Its exact record identities were independently reconciled with `website/story-identities.json`; every record's related-source graph was reconciled with `archived-references/source-groups.json`.

## Covered records

- 2,082 annual list records in 20 collections.
- 1,783 records from finalized 2006–2025 collections: 190 winners, 946 other original nomination records, and 647 later audit additions.
- 299 preliminary, unranked, not community-vetted 2026 AI leads.
- 2,778 URL entries from the complete archive manifest, including articles, papers, slides, advisories, code, repositories and videos.
- Every related-source link for every annual record, including link-only tools. There are 3,533 distinct literal related-source URL strings. This is NOT a count of unique papers: URL spellings and multiple artifacts can refer to the same work.
- 5,903 preserved-file inventory entries, including Markdown/PDF research files, figures, diagrams and original-listing files.
- A linked inventory of all 6,524 repository files, including evaluation notes and other site content.

The 2,075 research groups do not equal the record count: some records legitimately share a group or primary citation. No annual record was deduplicated away.

## Collection counts

- 2006: 78
- 2007: 96
- 2008: 82
- 2009: 98
- 2010: 92
- 2011: 70
- 2012: 81
- 2013: 54
- 2014: 72
- 2015: 71
- 2016-17: 122
- 2018: 123
- 2019: 94
- 2020: 85
- 2021: 69
- 2022: 92
- 2023: 107
- 2024: 165
- 2025: 132
- 2026-ai: 299

## Availability and limits

The manifest records 2,481 Markdown paths and 2,439 PDF paths. Of its references, 297 have neither preservation path. Some other entries are available only in one format. There are 44 distinct referenced archive paths absent from the pinned Git tree. Their exact paths appear under `coverage.missing_asset_paths` in `catalog.json`; missing source artifacts also have false `mdExists`/`pdfExists` flags. These are repository-snapshot checks, not fresh HTTP checks of the deployed website.

Bibliographic inclusion is complete against this snapshot; reading, independent attribution validation and exploit reproduction are not. Publication dates, URL health, tags, source classifications and author names are imported as reported, not corrected by inference. Original research bodies and source-derived summaries are not copied because the site's MIT licence explicitly does not relicense them. The large-PDF hosting fallbacks can be live URLs; use a pinned Markdown copy and recorded provenance when exact snapshot identity matters.

## Files

- `catalog.json`: all annual records, full related-source links and all manifest reference metadata.
- `collections/<year>.md`: human-readable bibliography for every annual record.
- `assets.json`: preserved files, byte sizes, Git blob identifiers and download URLs; a Git blob identifier is not a file SHA-256.
- `repository-files.json`: every file in the complete, non-truncated pinned Git tree.
- `tag-vocabulary.json`: source tags, query aliases and the archive's explicitly 2021 OWASP mapping.
- `provenance.json`: source URLs and SHA-256 hashes of canonical input files.
- `verification-ledger.json`: independently reconciled record/source/asset identity sets and installed data hashes.

Use `query.py search` for records and `show` for their full related-source graph. `refs` searches manifest URL entries; it does not replace the record's complete related-source graph.

Run the portable `test_query.py` and `verify.py` scripts before claiming the installed index works. A future refresh must use one pinned commit and repeat exact-set reconciliation, including failed/missing artifacts; never splice sources from different commits or relabel 2026 candidates as ranked results.
