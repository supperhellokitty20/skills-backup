# nuclei templates — structure, matchers, authoring

A template is a YAML DSL file (`.yaml`) with: a unique **`id`** (no spaces — output parsing
depends on it), an **`info`** block, a **protocol** key, protocol-specific request details,
**`matchers`**, and **`extractors`**.

Full grammar: https://github.com/projectdiscovery/nuclei/blob/dev/SYNTAX-REFERENCE.md

## Matcher types (7)

| Type | Part matched |
|---|---|
| `status` | integer status comparison |
| `size` | content length |
| `word` | part for a protocol |
| `regex` | part for a protocol |
| `binary` | part for a protocol |
| `dsl` | part for a protocol (helper functions) |
| `xpath` | XML/HTML (matches if the query returns any result) |

```yaml
matchers:
  - type: status
    status: [200, 302]
```

```yaml
matchers:
  - type: binary
    binary: ["504B0304", "526172211A070100", "FD377A585A0000"]  # zip / rar5 / xz
    condition: or
    part: body
```

```yaml
matchers:
  - type: word
    encoding: hex
    words: ["50494e47"]   # "PING"
    part: body
```

```yaml
matchers:
  - type: xpath
    part: body
    xpath: ["/html/head/title[contains(text(), 'Example Domain')]"]
```

```yaml
matchers:
  - type: dsl
    dsl:
      - "len(body)<1024 && status_code==200"
      - "contains(toupper(body), md5(cookie))"
```

DSL can access every protocol response part — `content_length`, `status_code`, `body`, `header`,
`cookie`, and so on. List available helpers with `nuclei -ldf`.

## Protocol examples

### DNS

```yaml
id: basic-dns-example
info: { name: Test DNS Template, author: pdteam, severity: info }
dns:
  - name: "{{FQDN}}"
    type: CNAME
    class: inet
    recursion: true
    retries: 3
    matchers:
      - type: word
        words: ["IN\tCNAME"]
```

DNS `part` values: `request, rcode, question, extra, answer, ns, raw/all/body`.
DNS request fields: `name` (usually `{{FQDN}}`), `type`,
`class` (inet/csnet/chaos/hesiod/none/any), `retries`, `recursion`.

### TCP / network

```yaml
id: basic-network-request
info: { name: Basic Network Request, author: pdteam, severity: info }
tcp:
  - host: ["{{Hostname}}"]
    inputs:
      - data: "PING\r\n"
    read-size: 4
    matchers:
      - type: word
        part: data
        words: ["PONG"]
```

### File

Supports `word` and `regex` matchers/extractors (part: `all`).

```yaml
id: ssh-public-key
info: { name: SSH Public Key Detect, author: pd-team, severity: low }
file:
  - extensions: [pub]
    max-size: 1024
    matchers:
      - type: word
        words: ["ssh-rsa"]
```

```yaml
id: google-api-key
info: { name: Google API Key, author: pdteam, severity: info }
file:
  - extensions: [all, txt]
    extractors:
      - type: regex
        name: google-api-key
        regex: ["AIza[0-9A-Za-z\\-_]{35}"]
```

Run file templates against a directory or a saved response set:

```bash
nuclei -t file.yaml -file -target http-response/
nuclei -t file.yaml -file -target output.txt
```

This pairs with `httpx -sr -srd responses/` — probe once, then grep the stored corpus offline
with file templates instead of re-requesting the target.

## Multi-protocol templates

Protocol-scoped variables are shared across protocols, and data crosses protocols via **dynamic
extractors** stored in template context with a protocol prefix.

| Protocol | Response field | Exported variable |
|---|---|---|
| ssl | subject_cn | `ssl_subject_cn` |
| dns | cname | `dns_cname` |
| http | header | `http_header` |
| code | response | `code_response` |

```yaml
id: dns-http-template
info: { name: dns + http takeover template, author: pdteam, severity: info }
dns:
  - name: "{{FQDN}}"
    type: cname
    extractors:
      - type: dsl
        name: exported_cname
        dsl: [cname]
        internal: true
http:
  - method: GET
    path: ["{{BaseURL}}"]
    matchers:
      - type: dsl
        dsl:
          - "contains(body,'Domain not found')"
          - "contains(exported_cname, 'github.io')"
        condition: and
```

Dump every exported field while developing:
`nuclei -t multi-protocol-template.yaml -u scanme.sh -debug -svd`

## Template object (SYNTAX-REFERENCE highlights)

- `id` (string) — unique, e.g. `id: CVE-2021-19520`
- `info` (model.Info) — name, author, tags, reference, severity, classification
- `flow` (string) — execution flow, e.g. `flow: for region in regions { http(0) }`
- `requests` (http.Request[]) — **deprecated**, use `http`
- `http` (http.Request[]), `dns` (dns.Request[])
- Request-level fields: `skip-variables-check`, `iterate-all`, `digest-username`,
  `digest-password`, `disable-path-automerge`, `pre-condition`, `pre-condition-operator`,
  `global-matchers`
- `MatcherType` enum: word, regex, binary, status, size, dsl, xpath

## Authoring patterns (TEMPLATE-CREATION-GUIDE)

```yaml
info:
  name: ...
  author: ...
  severity: critical
  description: |
    ...
  impact: |
    ...
  remediation: |
    ...
  reference:
    - https://nvd.nist.gov/vuln/detail/CVE-2018-11776
  classification:
    cvss-metrics: CVSS:3.0/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H
    cvss-score: 8.1
    cve-id: CVE-2018-11776
    cwe-id: CWE-94
```

```yaml
info:
  tags: cve,cve2018,rce,apache,struts,ognl   # specific AND comprehensive
  metadata:
    verified: true          # only if YOU tested it
    max-request: 1          # auto-calculated — do NOT set manually
    shodan-query: 'http.component:"Apache Struts"'
    fofa-query: 'body="struts" && title="Apache"'
```

Basic HTTP request:

```yaml
http:
  - method: GET|POST|PUT|DELETE
    path:
      - "{{BaseURL}}/endpoint"
      - "{{Hostname}}/another-path"
    headers:
      User-Agent: Custom-Agent-String
      Content-Type: application/json
      Origin: https://example.com
    body: |
      {"param": "{{payload}}"}
    disable-cookie: false     # cookies are reused by default
    matchers-condition: and   # require ALL matchers
    matchers:
      - type: word
        words: ["success_indicator"]
        part: body
```

Extractor feeding a matcher:

```yaml
http:
  - method: GET
    path: ["{{BaseURL}}/info"]
    extractors:
      - type: regex
        name: version
        regex: ['Version: ([0-9\.]+)']
        group: 1
    matchers:
      - type: word
        words: ["Application Info"]
        part: body
```

Header-spoofing (auth-bypass class):

```yaml
headers:
  X-Forwarded-For: 127.0.0.1
  X-Real-IP: 127.0.0.1
matchers-condition: and
matchers:
  - type: word
    words: ["Admin Dashboard", "Administrative Panel"]
    part: body
  - type: status
    status: [200]
```

## Review priorities (TEMPLATE-REVIEW-GUIDE)

1. Quality & consistency — formatting, syntax, field standardization
2. Metadata enhancement — search queries, classifications, documentation
3. Tags optimization — category alignment, searchability
4. Classification — CVE/CWE alignment, severity scoring
5. Matcher refinement — detection logic, false-positive prevention

Community contributions most often fall short on metadata/classification; review attention goes
to technical accuracy and matcher quality.

## Real CVE template patterns

**CVE-2024-3080** — ASUS DSL-AC88U auth bypass (critical, CWE-287, CVSS 9.8). Path-traversal
encoding plus `stop-at-first-match`:

```yaml
id: CVE-2024-3080
info:
  name: ASUS DSL-AC88U - Authentication Bypass
  severity: critical
  classification:
    cvss-metrics: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
    cvss-score: 9.8
    cve-id: CVE-2024-3080
    cwe-id: CWE-287
    epss-score: 0.57883
    epss-percentile: 0.98126
  metadata: { max-request: 2 }
  tags: cve,cve2024,asus,router,auth-bypass,lfi,vkev,vuln
http:
  - method: GET
    path:
      - "{{BaseURL}}/js/..%2f%2f/wizard.htm"
      - "{{BaseURL}}/images/..%2f%2f/wizard.htm"
    stop-at-first-match: true
    matchers-condition: and
    matchers:
      - type: word
        part: body
        words: ["show_wizardmenu();"]
      - type: status
        status: [200]
```

- **CVE-2021-27651** (Pega Infinity) — `host-redirects: true`, DSL
  `compare_versions(version, '< 8.5.2', '>= 8.2.1')`, and an `internal: true` regex extractor
  that captures the version for the matcher.
- **CVE-2020-26214** (Alerta < 8.1.0) — `compare_versions(version, '< 8.1.0')` + word matcher on
  `"alarm_model"`, `"actions"`, `"severity"` + status 200.
- **CVE-2022-47003** (Mura CMS < 10.0.580) — raw multi-request, `redirects: true`, extractor
  pulls `siteid` with `internal: true` and reuses it in the next request.
- **CVE-2023-22527** — template injection via raw request:

```yaml
matchers:
  - type: dsl
    dsl:
      - x_vuln_check != ""
      - contains(to_lower(body), 'empty{name=')
    condition: and
extractors:
  - type: dsl
    dsl: [x_vuln_check]     # prints output of whoami
```

- **CVE-2025-49113** — OOB confirmation via interactsh:

```yaml
matchers:
  - type: dsl
    name: exploit_check
    dsl:
      - 'status_code == 200'
      - 'contains(interactsh_protocol, "dns")'
      - 'contains_all(body, "add2attachment_list", "rcmfile", "mimetype", "firstfile")'
    condition: and
```

- **CVE-2025-53770** — encoded-payload DSL matcher:

```yaml
matchers:
  - type: dsl
    dsl:
      - 'contains(x_nuclei,"CVE-2025-53770")'
      - 'contains(body, "MSOTlPn_DWP")'
    condition: and
```

The repeated winning pattern: an `internal: true` extractor captures a version or token, and a
`dsl` matcher with `condition: and` combines it with a content signal — that is what separates a
confirmed finding from a banner-grab false positive.

## Credential-stuffing / custom portals

```bash
cat jira.txt | nuclei -var username=email.txt -var password=pass.txt \
  -id jira-login-check -attack-type clusterbomb
```

Custom target-specific templates are recommended for internal/custom portals.

Contributing: PR against `projectdiscovery/nuclei-templates`, follow YAML best practices, test
before submitting. Reference: https://docs.projectdiscovery.io/templates/introduction
