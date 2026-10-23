# WordPress Plugin Audit Workflow

## 1. Workspace, Scope, And Intake

Create one workspace root per Patchstack program or plugin, named `<plugin-or-program>-research` by default. Example: `elementor-research`.

Keep every artifact inside that root:

```text
elementor-research/
  ENGAGEMENT.md              # scope, tested version, authorization notes
  RECON.md                   # attack-surface map and focus areas
  TRIAGE.md                  # confirmed, needs-evidence, dismissed
  source/                    # extracted plugin source
  findings/                  # raw candidate notes and machine-readable findings
  poc/                       # local PoC requests, scripts, payloads, screenshots notes
  evidence/                  # raw HTTP responses, DB dumps, logs, screenshots notes
  reports/                   # Patchstack report drafts and final reports
  lab/                       # disposable local WordPress lab, if started
```

Use this root as the current working directory for recon, finding, PoC creation, verification, and reporting. Do not scatter plugin source, PoCs, or reports elsewhere.

If the user provides a Patchstack program URL, browse it when accessible and record the exact scope in `ENGAGEMENT.md`: plugin name, allowed versions, permitted testing, exclusions, and disclosure rules. If the page is authenticated or ambiguous, ask the user for the plugin slug, zip, or source and the relevant scope text.

Do not assume a plugin is in scope because it is public. Do not test live production sites by default. Use the local WordPress lab for verification unless the program scope explicitly allows a different target.

## 2. Source Extraction

Use `scripts/init-patchstack-audit.sh` with one of:

- `--plugin wordpress-org-slug`
- `--plugin /path/to/plugin.zip`
- `--plugin https://example.com/plugin.zip`
- `--plugin-source /path/to/extracted/plugin`

If the user does not specify `--output`, the script creates `./<target>-research`. For example, `--plugin elementor` creates `./elementor-research`.

Record:

- Plugin source path
- Plugin version from the main plugin header/readme
- Source origin: WordPress.org slug, zip URL, local zip hash, or source directory
- Audit date and Patchstack program/scope reference

Useful commands inside the source directory:

```bash
rg -n "Plugin Name:|Version:|Requires PHP:|Requires at least:|Stable tag:" .
find . -maxdepth 2 -type f | sort
```

## 3. Recon

Create `RECON.md`. Partition the plugin into 5-15 focus areas so follow-up finding work does not collapse onto the same path.

Start with entry points:

```bash
rg -n "add_action\\(|add_filter\\(|register_rest_route\\(|wp_ajax(_nopriv)?_|admin_post(_nopriv)?_|add_shortcode\\(|register_block_type\\(|admin_menu|add_menu_page|add_submenu_page|cron_schedules|wp_schedule_event" .
```

Map trust boundaries and sources:

```bash
rg -n "\\$_(GET|POST|REQUEST|FILES|COOKIE|SERVER)|get_param\\(|get_json_params\\(|shortcode_atts\\(|filter_input\\(|php://input" .
```

Map security controls:

```bash
rg -n "current_user_can\\(|user_can\\(|check_ajax_referer\\(|check_admin_referer\\(|wp_verify_nonce\\(|wp_create_nonce\\(|permission_callback|sanitize_|wp_kses|esc_html|esc_attr|esc_url|esc_js|wp_unslash" .
```

Map high-risk sinks:

```bash
rg -n "\\$wpdb|->query\\(|->get_results\\(|->get_var\\(|prepare\\(|dbDelta\\(|update_option\\(|delete_option\\(|wp_insert_post\\(|wp_update_post\\(|wp_delete_post\\(|wp_remote_(get|post|request)\\(|file_get_contents\\(|fopen\\(|fwrite\\(|unlink\\(|rename\\(|copy\\(|move_uploaded_file\\(|wp_handle_upload\\(|unserialize\\(|maybe_unserialize\\(|eval\\(|include\\(|require\\(" .
```

For each focus area, record:

- Entry point and route/action/shortcode/block name
- Required role or unauthenticated reachability
- Nonce and capability checks, if any
- Data sources and sanitization
- Sensitive sinks and state changes
- Expected candidate vulnerability classes

## 4. Finding

For each focus area, trace source to sink and write candidate notes under `findings/`. Store all PoC material for a candidate under `poc/<finding-slug>/`; store raw responses, logs, screenshots notes, database exports, or filesystem observations under `evidence/<finding-slug>/`. Prioritize:

- Missing capability check on AJAX, REST, admin-post, import/export, settings, or object mutation paths
- Missing nonce on state-changing authenticated actions, especially CSRF to stored XSS, settings change, file operation, or privilege-impacting state change
- SQL injection where user input reaches `$wpdb` without `prepare()` or strict allowlisting
- Stored/reflected XSS where attacker-controlled input reaches HTML/JS/admin notices/emails without context-appropriate escaping
- Arbitrary file upload/read/write/delete, path traversal, unsafe import/export, or archive extraction
- SSRF through `wp_remote_*` or URL fetches without scheme/host allowlisting
- Object injection/deserialization, dynamic include/require, eval-like behavior
- IDOR/broken access control on post/user/order/license/object IDs

Candidate notes must include:

- Vulnerability hypothesis
- Source-to-sink path with file:line evidence
- Required role and preconditions
- Minimal local PoC plan
- Planned PoC path under `poc/<finding-slug>/`
- Why existing nonce/capability/sanitization is insufficient

## 5. Verification

Start a local lab only when a candidate has a plausible path:

```bash
scripts/setup-wordpress-plugin-lab.sh --plugin-source ./source/PLUGIN_DIR --output ./lab
```

Use the lab credentials from `lab/LAB.md`. Build minimal requests with `curl`, browser dev tools, or WP-CLI. For authenticated requests, capture cookies and nonces from the local lab; do not invent nonces.

Verification evidence should prove:

- Exact role/session used
- Exact request sequence and payload
- Observed vulnerable behavior in response, database, filesystem, or browser
- Whether the issue reproduces at least twice in a clean or reset local state
- Why the behavior is not expected WordPress or plugin behavior

For each confirmed issue, keep the minimal local proof in `poc/<finding-slug>/`, such as:

- `request.http` or `curl.sh` for the exact local request
- `payload.txt` for the minimal payload
- `verify.md` for setup, role, nonce source, observations, and reproducibility
- Supporting helper scripts only when a plain request is insufficient

Good proof examples:

- SQLi: show altered query semantics or database extraction from the local lab, not just suspicious concatenation
- Stored XSS: show payload persistence and execution/reachability in the victim context
- CSRF: show state change without nonce validation from an authenticated victim role
- IDOR: show one low-privileged user accessing or modifying another user's object
- File issues: show constrained local file path, file creation/deletion/read proof, and path control

Dismiss or downgrade:

- Admin-only self-XSS without privilege boundary impact
- Actions protected by a valid nonce and appropriate capability
- Findings only reachable by administrators uploading code or editing templates
- Debug/test/demo code not reachable in production plugin paths
- Pure best-practice issues without an exploitable impact

## 6. Triage

Deduplicate by root cause: if one fix would close multiple symptoms, keep one finding and mention variants. Rank by real exploit preconditions:

- High: unauthenticated or low-privileged path with meaningful data exposure, account takeover, stored XSS against admins, SQLi, file write/delete, or privilege escalation
- Medium: authenticated subscriber/customer/contributor path with clear impact but limited preconditions
- Low: narrow role requirements, limited data, CSRF with modest impact, or defense-in-depth bypass
- Not a bug: not reproducible, expected behavior, admin-only without boundary crossing, or missing material impact

Write final triage into `TRIAGE.md`, keep raw candidates under `findings/`, keep PoCs under `poc/`, and keep raw evidence under `evidence/`.

## 7. Report

Use `references/report-template.md`. Write drafts and final report files under `reports/`. A report is ready only when it has:

- In-scope plugin and affected version
- Clear title and vulnerability class
- Preconditions and required role
- Source-root evidence with file:line references
- Minimal local reproduction steps
- Local PoC path under `poc/`
- Impact tied to the Patchstack bug bar
- Remediation guidance
- Any known false-positive caveats

Keep exploit code minimal and local. Include enough PoC detail for maintainers to reproduce and fix, without turning the report into a live-target exploitation guide.
