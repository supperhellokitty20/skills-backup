---
name: chrome-cdp-profile-control
description: "Use when driving a real Chrome profile over CDP."
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

# Driving a real Chrome profile over CDP

Use when asked to drive or control the user's real Chrome, or one specific profile (identified by
account/email), keeping its live logins. Covers the Chrome 136+ default-user-data-dir block, the profile
copy, launching the debug instance, attaching a driver, and proving which account you act as.

## Hard constraint first

**Chrome 136+ refuses `--remote-debugging-port` when `--user-data-dir` is the default path.**
You cannot debug the running personal Chrome in place. Consequences:

- Quit Chrome (graceful: `osascript -e 'quit app "Google Chrome"'`), then launch a *separate instance*
  with `--user-data-dir=<copy>`; the `SingletonLock` in the default dir otherwise blocks a second instance.
- A copy is required even in the "quit and relaunch" plan; only the *path* differs.

## Procedure

1. **Map the target profile**: `~/Library/Application Support/Google/Chrome/Local State` → `profile.info_cache`
   maps `Profile N` → `{name, user_name, gaia_name}`. `user_name` is the Google account.
2. **Quit Chrome**, confirm `pgrep -f "Contents/MacOS/Google Chrome$"` is empty, then copy. Exclude
   `Singleton*`, `LOCK`, `*.lock`, and regenerable caches (`GrShaderCache`, `GraphiteDawnCache`,
   `ShaderCache`, `GPUPersistentCache`, `BrowserMetrics*`) — ~1.8 GB copies in ~20 s down to ~1.4 GB.
   rsync echoing `open (2) …: No such file or directory` for `IndexedDB`/`WebStorage`/`CacheStorage`
   scratch files is harmless; verify the files that matter instead.
3. **Verify login state copied**: `Local State`, `Profile N/Preferences`, `Profile N/Cookies`,
   `Profile N/Login Data`, `Profile N/Web Data`. Modern Chrome keeps cookies at `Profile N/Cookies`
   (not `Profile N/Network/Cookies`).
4. **Launch the debug instance** (headful, so the user can watch/steer):
   `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir=<copy> --profile-directory="Profile 1" --remote-debugging-port=9222 --no-first-run --no-default-browser-check about:blank`
5. **Verify the endpoint**: `curl -s http://127.0.0.1:9222/json/version` → `webSocketDebuggerUrl`.
6. **Verify which profile actually opened** — non-negotiable, see pitfalls: open `chrome://version` over CDP
   and read the **Profile Path** row; it must end in `/Profile 1`, not `/Default`.
7. **Verify identity** on a read-only signed-in page (`https://myaccount.google.com/`,
   `https://github.com/settings/profile`) and match the visible email/name to `info_cache.user_name`.
   Never claim the profile is controlled from the launch flag alone.

Ready-made launcher: `scripts/launch-debug-profile.sh "Profile 1" <durable-copy-path> [port]`.

## Pitfalls

- **`--profile-directory` silently falls back to `Default`.** A launch with the flag still opened
  `.../Default` (Chrome's own `Profile Path` told the truth). Always read `chrome://version`; if it says
  `Default`, kill the instance, relaunch, re-verify.
- **`agent-browser connect <port>` launches its own browser** — it does not attach. Attach with the global
  flag: `agent-browser --cdp 9222 <cmd>` (`AGENT_BROWSER_CDP` also works). Use a named session
  (`AGENT_BROWSER_SESSION=<name>`), plus `--pin-tab` / `tab new <url>`; a stale bound tab errors
  `tab_gone` and needs `tab new`.
- **This agent-browser build has no `text` command**; use `snapshot -i -c`, `get text|url|title`, `tab list`.
- **Hermes' own `browser_exec`** attaches via `browser.cdp_url`. The `patch` tool **refuses** to edit
  `~/.hermes/config.yaml` (security-sensitive) — use `hermes config set browser.cdp_url http://127.0.0.1:9222`,
  revert with `hermes config unset browser.cdp_url`. Never set it unasked: it redirects every future
  `browser_exec` call, in every session, at the user's personal profile.
- **Credential-adjacent commands trip the approval guard.** Cookie-DB reads and
  `security find-generic-password` get blocked on timeout; verify with plain file listings instead.
- **The copy goes stale** versus the live profile, and one account signed in twice can fight over
  sync/session tokens. Treat the copy as a disposable working clone.
- **Scratch dirs are pruned** (~24 h idle): a profile copy there will vanish under a running Chrome.
  Use a durable path for anything meant to persist.

## On macOS, cookies survive the copy

Cookie encryption uses the Keychain item `Chrome Safe Storage` (same app, same machine), with the wrapped
key in the copied `Local State` (`os_crypt.encrypted_key`). A local copy keeps its logins; the same trick
fails across machines or users.

## Restoring the user's environment

After the copy, the user's normal Chrome is quit. Relaunch it with `open -a "Google Chrome"` (default
user-data-dir); it runs fine alongside the debug instance, and tab-session restore still works.