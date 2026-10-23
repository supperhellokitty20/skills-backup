# Tool selection and official sources

Use this reference for branch selection or missing-tool setup. Checked against official repositories/documentation and installed CLI help on 2026-09-08. Flags and availability vary by version; local help and a small output sample are authoritative for the installed binary. This map covers the ecosystem relevant to reconnaissance, not every library in the GitHub organization.

## Discovery and enrichment

| Tool | Role and handoff | Selection constraint / official source |
| --- | --- | --- |
| subfinder | Domains → passive hostname candidates; JSONL retains providers | Default passive host discovery; [repo](https://github.com/projectdiscovery/subfinder) |
| chaos (`chaos-client`) | Domain → curated subdomain data | Optional provider data; private config/environment for keys; [repo](https://github.com/projectdiscovery/chaos-client) |
| uncover | Search-engine query → host/IP/port candidates | Provider syntax and quotas differ; validate ownership before probing; [repo](https://github.com/projectdiscovery/uncover) |
| cloudlist | Authorized cloud account inventory → host/IP seeds | Select account/provider IDs; [repo](https://github.com/projectdiscovery/cloudlist) |
| alterx | Existing names + patterns → offline permutations | Estimate and cap output before resolution; [repo](https://github.com/projectdiscovery/alterx) |
| shuffledns | Candidates/wordlist + resolvers → wildcard-filtered names | Requires massdns; high concurrency defaults, separate DNS budget; [repo](https://github.com/projectdiscovery/shuffledns) |
| dnsx | Hostnames → DNS answers, CNAME/AAAA/NS/MX/TXT enrichment | Resolution is active; wildcard mode has incompatible flags; [repo](https://github.com/projectdiscovery/dnsx) |
| asnmap | Organization/domain/IP/ASN → network associations | Association does not authorize an entire ASN; [repo](https://github.com/projectdiscovery/asnmap) |
| mapcidr | Authorized CIDRs → counts, intersections, address lists | Offline; count first, avoid broad or IPv6 expansion; [repo](https://github.com/projectdiscovery/mapcidr) |
| cdncheck | IP/hostname → CDN/cloud/WAF attribution | Annotation, not proof of origin ownership; [repo](https://github.com/projectdiscovery/cdncheck) |
| naabu | Approved hosts/IPs and ports → open host:port records | Optional active CONNECT scan; `-passive` queries provider data; [repo](https://github.com/projectdiscovery/naabu) |
| tlsx | Approved TLS services → certificate/SAN metadata | SANs return to candidate scope gate; [repo](https://github.com/projectdiscovery/tlsx) |
| httpx | Hosts/URLs → reachable services and HTTP metadata | Central probe and bounded `-path` discovery stage; [usage](https://docs.projectdiscovery.io/opensource/httpx/usage) |
| urlfinder | Domains → passive archived/indexed URLs | Results can be stale, external, or contain sensitive queries; [repo](https://github.com/projectdiscovery/urlfinder) |
| katana | Scoped URLs → links, JS endpoints, forms, optional XHR | Standard first, headless selectively; [usage](https://docs.projectdiscovery.io/opensource/katana/usage), [running](https://docs.projectdiscovery.io/opensource/katana/running) |

## Analysis and supporting tools

| Tool | Use in this skill | Boundary / official source |
| --- | --- | --- |
| nuclei + nuclei-templates | Selected discovery/exposure checks or local custom path template | Inspect exact requests; broad CVE scans, fuzzing, code execution, and workflows are separate scope; [engine](https://github.com/projectdiscovery/nuclei), [templates](https://github.com/projectdiscovery/nuclei-templates) |
| proxify | Capture authorized browser/API traffic with observed methods | Bind loopback, isolate test-browser trust, protect captures; logging filters are not automatically egress filters; [repo](https://github.com/projectdiscovery/proxify) |
| interactsh-client/server | Correlate OOB events in separately requested validation | Not needed for path inventory; no automatic OAST callbacks; [repo](https://github.com/projectdiscovery/interactsh) |
| vulnx (formerly cvemap) | Enrich identified software with vulnerability intelligence | Version/banner matches are leads, not validated vulnerabilities; [repo](https://github.com/projectdiscovery/vulnx) |
| notify | Send selected deltas to an existing destination | Only with explicit user authorization to send; [repo](https://github.com/projectdiscovery/notify) |
| pdtm | Install/manage ProjectDiscovery binaries | Tool management, not scanning; inspect catalog/platform support; [repo](https://github.com/projectdiscovery/pdtm) |

The older `dnsprobe` utility's common probing role is covered by dnsx; verify repository status before using legacy scripts. `jq`, `sort`, `comm`, `tee`, `curl`, and Python are not ProjectDiscovery products. `anew` is TomNomNom's tool; `ffuf`, `gau`, `waybackurls`, `puredns`, `massdns`, and standalone `jsluice` are also external. Label optional integrations accurately; do not require them when PD tools satisfy the task.

## Setup when needed

Do not install the entire suite to parse existing artifacts. Inspect `command -v TOOL`, `TOOL -version`, and `TOOL -h`. Capture resolved binary paths; `httpx -h` must identify the ProjectDiscovery toolkit. Go requirements change; inspect the selected release's `go.mod` instead of copying a stale minimum version.

For requested setup, choose released binaries or PDTM:

```bash
go install github.com/projectdiscovery/pdtm/cmd/pdtm@latest
pdtm -h
pdtm -i subfinder,dnsx,httpx,urlfinder,katana
```

`pdtm -ia` installs the currently supported catalog when the user wants the full suite. Record versions. Manage PATH in the current session when possible; do not rewrite shell startup files as a recon side effect. Preserve existing binaries/configs unless an update was requested or is necessary and explained.

Fallback core module paths:

```text
github.com/projectdiscovery/subfinder/v2/cmd/subfinder
github.com/projectdiscovery/dnsx/cmd/dnsx
github.com/projectdiscovery/httpx/cmd/httpx
github.com/projectdiscovery/katana/cmd/katana
github.com/projectdiscovery/urlfinder/cmd/urlfinder
github.com/projectdiscovery/naabu/v2/cmd/naabu
github.com/projectdiscovery/nuclei/v3/cmd/nuclei
github.com/projectdiscovery/tlsx/cmd/tlsx
```

Use `go install MODULE@VERSION` with a chosen release. Avoid obsolete Nuclei `/v2` install examples. Native dependencies such as massdns and browser runtimes are separate. Provider keys remain in private supported configuration; report enabled source names, never values. Missing keys reduce coverage without blocking independent branches.

Refresh choices from the [official index](https://docs.projectdiscovery.io/opensource) and repositories when substantially newer releases are used.
