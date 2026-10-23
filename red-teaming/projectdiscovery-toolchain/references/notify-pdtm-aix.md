# notify, pdtm, aix

## notify — alert fan-out

Install: `go install -v github.com/projectdiscovery/notify/cmd/notify@latest`

Providers: Slack, Discord, Telegram, Pushover, Email (SMTP), Microsoft Teams, Google Chat,
Gotify, and custom webhooks. File/pipe input, line-by-line or bulk, single or multiple providers.

| Flag | Alt | Description | Example |
|---|---|---|---|
| `-bulk` | | enable bulk processing | `notify -bulk` |
| `-char-limit` | `-cl` | max chars per message (default 4000) | `notify -cl 2000` |
| `-config` | | config file | `notify -config config.yaml` |
| `-data` | `-i` | input file to send | `notify -i test.txt` |
| `-delay` | `-d` | delay (seconds) between notifications | `notify -d 2` |
| `-id` | | id(s) to send to | `notify -id recon,scans` |
| `-msg-format` | `-mf` | custom formatting | `notify -mf Hey {{data}}` |
| `-no-color` | `-nc` | disable colors | |
| `-provider-config` | `-pc` | provider config path | `notify -pc provider.yaml` |
| `-provider` | `-p` | provider(s) to send to | `notify -p slack,telegram` |
| `-proxy` | | HTTP/SOCKSv5 proxy | `notify -proxy http://127.0.0.1:8080` |
| `-rate-limit` | `-rl` | max HTTP requests/second | `notify -rl 1` |
| `-silent` | | silent mode | |
| `-verbose` | | verbose mode | |
| `-update` / `-disable-update-check` | `-duc` | update handling | |

Config paths: flags at `$HOME/.config/notify/config.yaml`, providers at
`$HOME/.config/notify/provider-config.yaml`.

**Default sends line by line**; `-bulk` sends the whole message (chunked as needed). Use `-id` to
route different pipeline stages to different channels without separate config files.

### Provider config (full YAML)

```yaml
slack:
  - id: "slack"
    slack_channel: "recon"
    slack_username: "test"
    slack_format: "{{data}}"
    slack_webhook_url: "https://hooks.slack.com/services/XXXXXX"
  - id: "vulns"
    slack_channel: "vulns"
    slack_username: "test"
    slack_format: "{{data}}"
    slack_webhook_url: "https://hooks.slack.com/services/XXXXXX"

discord:
  - id: "crawl"
    discord_channel: "crawl"
    discord_username: "test"
    discord_format: "{{data}}"
    discord_webhook_url: "https://discord.com/api/webhooks/XXXXXXXX"

telegram:
  - id: "tel"
    telegram_api_key: "XXXXXXXXXXXX"
    telegram_chat_id: "XXXXXXXX"        # optional topic id XXXXXXXX:Y
    telegram_format: "{{data}}"
    telegram_parsemode: "Markdown"      # None/Markdown/MarkdownV2/HTML

pushover:
  - id: "push"
    pushover_user_key: "XXXX"
    pushover_api_token: "YYYY"
    pushover_format: "{{data}}"
    pushover_devices: ["iphone"]

smtp:
  - id: email
    smtp_server: mail.example.com
    smtp_username: test@example.com
    smtp_password: password
    from_address: from@email.com
    smtp_cc: [to@email.com]
    smtp_format: "{{data}}"
    subject: "Email subject"
    smtp_html: false
    smtp_disable_starttls: false

googlechat:
  - id: "gc"
    key: "XXXXXXXX"
    token: "XXXXXX"
    space: "XXXXXX"
    google_chat_format: "{{data}}"

teams:
  - id: "recon"
    teams_webhook_url: "https://<domain>.webhook.office.com/webhookb2/xx@xx/IncomingWebhook/xx"
    teams_format: "{{data}}"

gotify:
  - id: 'gotify'
    gotify_host: 'XXXXXX'
    gotify_port: '80'
    gotify_token: 'XXXXXX'
    gotify_format: '{{data}}'
    gotify_disabletls: false
    gotify_title: "recon"

custom:
  - id: webhook
    custom_webhook_url: http://host/api/webhook
    custom_method: GET
    custom_format: '{{data}}'
    custom_headers:
      Content-Type: application/json
      X-Api-Key: ***
  - id: webhookJson
    custom_webhook_url: http://host/api/webhook
    custom_method: GET
    custom_format: '{"text":{{dataJsonString}} }'
    custom_headers:
      Content-Type: application/json
      X-Api-Key: ***
```

Top-level keys are fixed by the Go struct: `slack`, `discord`, `pushover`, `smtp`, `teams`,
`telegram`, `googlechat`, `custom`, `gotify`.

**Environment-variable interpolation is supported** (e.g. `${SLACK_WEBHOOK_URL}`) — use it rather
than committing webhook URLs into the config. `{{dataJsonString}}` is the JSON-safe form of
`{{data}}` for custom webhooks with JSON bodies.

```sh
subfinder -d hackerone.com -o h1.txt; notify -data h1.txt -bulk -provider discord,slack
subfinder -d hackerone.com -o h1.txt; notify -data h1.txt -bulk -id recon,vulns,scan
```

Provider setup references: Slack incoming webhooks, Discord webhooks
(`support.discord.com/hc/en-us/articles/228383668`), Telegram bots
(`core.telegram.org/bots#3-how-do-i-create-a-bot`), Pushover (shoutrrr docs).

## pdtm — ProjectDiscovery tool manager

Requires go1.24.3. `go install -v github.com/projectdiscovery/pdtm/cmd/pdtm@latest`, or a release
binary from `github.com/projectdiscovery/pdtm/releases`.

```
CONFIG:
   -config string            cli flag configuration file (default "$HOME/.config/pdtm/config.yaml")
   -bp, -binary-path string  custom binary download location (default "$HOME/.pdtm/go/bin")

INSTALL:
   -i,  -install string[]    install project(s) by name (comma separated)
   -ia, -install-all         install all projects
   -ip, -install-path        append path to PATH
   -igp,-install-go-path     append GOBIN/GOPATH to PATH

UPDATE:
   -u,  -update string[]     update project(s) by name
   -ua, -update-all          update all projects
   -up, -self-update         update pdtm itself
   -duc,-disable-update-check

REMOVE:
   -r,  -remove string[]     remove project(s) by name
   -ra, -remove-all          remove all projects
   -rp, -remove-path         remove path from PATH

DEBUG:
   -sp, -show-path           show current binary path and exit
   -version, -v, -nc
   -disable-changelog, -dc   disable release changelog in output
```

Config paths from source:

```go
defaultConfigLocation = filepath.Join(homeDir, ".config/pdtm/config.yaml")
cacheFile             = filepath.Join(homeDir, ".config/pdtm/cache.json")
defaultPath           = filepath.Join(homeDir, ".pdtm/go/bin")
```

**Projects install as released binaries**, so only platforms with published binaries are
supported — a tool missing for your OS/arch is a packaging gap, not a broken pdtm.
`$HOME/.pdtm/go/bin` is added to `$PATH` by default.

`Update()` flow: resolve executable path → return `ErrIsUpToDate` if current → `ErrNoAssetFound`
if no assets → remove old binary → install new → show release notes unless disabled → log
`updated <tool> to <version>`.

Common uses: `pdtm -ia` (install all), `pdtm -i nuclei,httpx`, `pdtm -ua` (update all),
`pdtm -u nuclei`, `pdtm -ra` (remove all), `pdtm -sp` (print binary path).

## aix — LLM CLI wrapper

A CLI front-end for LLM APIs (primarily OpenAI) — **not a recon tool**. Requires Golang 1.19+ and
`OPENAI_API_KEY`.

`go install github.com/projectdiscovery/aix/cmd/aix@latest`

```
INPUT:
   -p,  -prompt string[]         prompt to query (stdin, string, file)

MODEL:
   -g3, -gpt3                    use GPT-3.5 (default true)
   -g4, -gpt4                    use GPT-4.0
   -m,  -model string            specific model (ex: gpt-4-0314)
   -lm, -list-models

CONFIG:
   -ak, -openai-api-key string   api key (string, file, env)
   -t,  -temperature string
   -tp, -topp string
   -sc, -system-context string[] system message (string, file)
   -s,  -stream                  stream to stdout (markdown rendering disabled)

OUTPUT:
   -o,  -output string           file to write output to
   -j,  -jsonl                   json(line) output
   -v,  -verbose
   -silent
   -nc, -no-color
   -nm, -no-markdown
   -version

UPDATE:
   -up, -update  /  -duc, -disable-update-check
```

Default config: `$HOME/.config/aix/config.yaml`.

```bash
aix -p "What is the capital of France?"
aix -p "How to install Linux?" -g4
echo list top trending web technologies | aix
aix -p "What is the capital of France?" -jsonl -o output.txt | jq .
```

JSONL shape:

```json
{
  "timestamp": "2023-03-26 17:55:42.707436 +0530 IST m=+1.512222751",
  "prompt": "What is the capital of France?",
  "completion": "Paris.",
  "model": "gpt-3.5-turbo"
}
```

The `-jsonl` + stdin form is the useful one: it makes `aix` a pipeable triage stage between a
scanner and `notify`. Inside Hermes you already have a model, so reach for `aix` only when the
pipeline must run standalone (cron, remote box, shell script).
