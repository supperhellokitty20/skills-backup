# Infrastructure / auxiliary tools

## cloudlist — multi-cloud asset inventory

*"Cloudlist is a tool for listing Assets from multiple cloud providers."*

| Group | Flags |
|---|---|
| Config | `-config` (default `$HOME/.config/cloudlist/config.yaml`), `-pc, -provider-config` (default `$HOME/.config/cloudlist/provider-config.yaml`) |
| Filters | `-p, -provider`, `-id string[]`, `-host` (hostnames only), `-ip` (IPs only), `-s, -service`, `-ep, -exclude-private` |
| Update | `-up, -update`, `-duc, -disable-update-check` |
| Output | `-o, -output`, `-json`, `-version`, `-v`, `-silent` |

Supported providers (default `-p` value):
`linode,fastly,heroku,terraform,digitalocean,consul,cloudflare,hetzner,nomad,do,scw,openstack,alibaba,aws,gcp,namecheap,kubernetes,azure,custom`

Provider interface (`pkg/schema/schema.go`): `Name()`, `ID()`, `Resources(ctx)`, `Services()`.
Resource fields: `Public, Provider, Service, ID, PublicIPv4/v6, PrivateIpv4/v6, DNSName, Metadata`.
Resources are **deduplicated by IP/DNS**.

GCP supports two modes: Organization-Level Cloud Asset Inventory API, or Individual Service APIs.

## uncover — search-engine asset discovery

*"quickly discover exposed assets on the internet using multiple search engines."*

Flags: `-q, -query` (stdin/file/config input), `-e, -engine` (default `shodan`),
`-asq, -awesome-search-queries`.

Engines: `shodan,shodan-idb,fofa,censys,quake,hunter,zoomeye,netlas,publicwww,criminalip,hunterhow,google,odin,binaryedge,onyphe,driftnet,greynoise`

Per-engine input flags: `-shodan/-s`, `-shodan-idb/-sd`, `-fofa/-ff`, `-censys/-cs`, `-quake/-qk`,
`-hunter/-ht`, `-zoomeye/-ze`, `-netlas/-ne`, `-criminalip/-cl`.

```
echo jira | uncover -e shodan,censys,fofa,quake,hunter,zoomeye,netlas,criminalip,driftnet
```

`-asq` pulls curated dorks — the fastest way to turn a technology name into a target list.
Nuclei template `metadata.shodan-query` / `fofa-query` fields pair directly with this.

## proxify — MITM proxy with DSL match/replace

*"Swiss Army Knife Proxy for rapid deployments. Supports request/response dump, filtering and
manipulation via DSL language, upstream HTTP/Socks5 proxy."*

Features: intercept/manipulate HTTP/HTTPS and NON-HTTP; thick-client and invisible proxy modes;
TLS MITM with client/server certs; HTTP and SOCKS5 upstream; Match/Filter and Replace DSL; full
traffic dump; embedded DNS server; protocol decode plugins (XMPP/SMTP/FTP/SSH); Burp replay.

| Group | Flags |
|---|---|
| Filter/DSL | `-request-dsl/-req-fd`, `-response-dsl/-resp-fd`, `-request-match-replace-dsl/-req-mrd`, `-response-match-replace-dsl/-resp-mrd` |
| Network | `-http-addr/-ha` (default `127.0.0.1:8888`), `-socks-addr/-sa` (default `127.0.0.1:10080`), `-http-proxy`, `-socks5-proxy`, `-pt` (TLS passthrough regex), `-dns-mapping`, `-dns-resolver` |
| Output | `-store-response/-sr` (`proxify_logs`), `-output/-o` (`proxify_logs.jsonl`), `-output-format/-of` (jsonl\|yaml), `-dump-req`, `-dump-resp`, `-out-ca/-oca` |

```
proxify -request-dsl "contains(request,'firefox')"
proxify -response-match-replace-dsl "replace_regex(response, '^authentication failed$', 'authentication ok')"
proxify -request-match-replace-dsl "replace(request,'firefox','chrome')"
```

The match-replace DSL is how you test client-side trust assumptions (flipping a server verdict
in-flight) without touching the application.

## interactsh — out-of-band interaction capture

*"an open-source tool for detecting out-of-band interactions ... designed to detect
vulnerabilities that cause external interactions."* This is the OAST backend nuclei uses for
blind SSRF / RCE / XXE detection.

`interactsh-client` flags:

| Group | Flags |
|---|---|
| Input | `-s, -server` (default `oast.pro,oast.live,oast.site,oast.online,oast.fun,oast.me`) |
| Config | `-config`, `-n/-number`, `-t/-token`, `-pi/-poll-interval` (default 5), `-nf/-no-http-fallback`, `-cidl/-correlation-id-length`, `-cidn/-correlation-id-nonce-length`, `-sf/-session-file` |
| Filter | `-m/-match`, `-f/-filter`, `-dns-only`, `-http-only`, `-smtp-only` |
| Output | `-o`, `-json`, `-ps/-payload-store`, `-psf/-payload-store-file`, `-v` |
| Debug | `-version`, `-health-check/-hc` |

Client protocol: polls `GET /poll?id=<correlationID>&secret=<secretKey>`, supports an
`Authorization` token header, decrypts interactions with `AESKey`.

**Use `-sf/-session-file`.** Correlation IDs are per-session; without a persisted session a
callback arriving minutes later cannot be tied back to the request that triggered it.

## simplehttpserver — payload serving and fake services

Features: HTTP/S web server; file server over an arbitrary directory; request/response dump;
configurable ip/port; configurable HTTP/TCP server with customizable responses via **YAML template**.

Flags: `-listen` (default `0.0.0.0:8000`), `-tcp`, `-tls`, `-rules` (rules YAML), `-path`
(folder, default cwd), `-upload` (enable PUT upload), `-https`, `-cert`, `-key`, `-domain`
(default `local.host`), `-basic-auth` (`username:password`), `-realm`, `-verbose`, `-sandbox`,
`-http1`, `-max-file-size` (default 50), `-max-dump-body-size` (default -1), `-py` (emulate
Python style), `-cors`, `-header` (`name: value`, repeatable).

Rules template shape:

```yaml
- match: <regex>
  match-contains: <literal>
  name: <rule name>
  response: <body>        # supports !!binary for e.g. LDAP responses
```

```
simplehttpserver -rules rules.yaml -tcp -tls -domain localhost
simplehttpserver -basic-auth root:root -upload
```

The `!!binary` response support plus `-tcp` is what makes this usable as a fake LDAP/JDBC
endpoint for deserialization and JNDI testing, not just a file host.
