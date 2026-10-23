---
name: linux-lpe-source-audit
description: Use when hunting LPE in a Linux system-config codebase.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [security, privilege-escalation, source-review, linux, sudoers, systemd]
    related_skills: [bb-dupe-avoidance, triage-validation, bb-workspace-layout, codebase-inspection]
---

# Linux LPE source audit

Audit a repo whose files land in `/etc`, `/usr/lib/systemd`, `/usr/share/libalpm/hooks`, `/etc/sudoers.d`, `/etc/tmpfiles.d`, `/etc/polkit-1`, or that otherwise runs as root: a distro's shell-script command set, an installer, a desktop shell, a themes/plugins tree, or a config repo a privileged step consumes.

## When to Use

- Asked to find an LPE / privilege escalation / root escalation in a source tree.
- Auditing a distro, desktop shell, installer, theme or plugin system, or any config repo whose output a root step consumes.
- Re-checking an already-hardened project for the class the maintainers have not closed yet.

Not for: reviewing your own uncommitted diff (`requesting-code-review`), or web-app authorization bugs (`hunt-*`).

## The rule that decides everything

An elevation the user consents to is not a vulnerability. Typing a sudo/polkit password and getting root for the thing you asked for is the product working. A finding is an **unprivileged** process reaching root — or a root-equivalent primitive (arbitrary root file write/delete/chown, arbitrary root code exec, docker-group access) — **without** the user knowingly authorizing that exact action. Only five things can produce that, so enumerate them and refuse to look elsewhere first:

1. **Shipped passwordless authorization** — `/etc/sudoers.d/*` (`NOPASSWD`, wildcard/regex arguments, `ALL` user specs), polkit `.policy`/`.rules` with `allow_active`/`allow_any`, root-equivalent group grants (`docker`, `input`, `disk`, `kvm`, `wheel`), setuid modes, file capabilities.
2. **Root process consuming attacker-controlled input** — root systemd units and drop-ins, system-sleep hooks, alpm/pacman hooks, tmpfiles.d, udev rules, root timers, first-boot provisioning services, package scriptlets.
3. **Privilege-boundary error** — root code executing or sourcing user-writable content: themes, plugins, hooks, user configs, PATH-resolved helpers, an env-var-selected binary or script path.
4. **Permission/ownership mistake** — a root-executed file that sits in (or under) a user-writable directory; a writable file a root step sources.
5. **Validated-then-used path (TOCTOU)** in a privileged flow.

If a candidate is not one of those five, it is not the finding. Say so and move on — never pad the report with configuration/origin/internal-hostname disclosures, verbose error leaks, or theoretical races.

## Procedure

**Step 0 — Establish what you are auditing.** Git forensics before reading code, because it decides whether you are hunting a novel bug or a planted one:

```bash
git rev-parse HEAD; git rev-parse origin/$(git branch --show-current)
git rev-list --left-right --count origin/<branch>...HEAD
git status --short
```

HEAD equal to the upstream tip means a novel upstream bug is the only target, so the review must be exhaustive. Extra commits ahead of upstream mean diff them first — a planted bug lives there. Then read the project's own security posture: `AGENTS.md`/`CONTRIBUTING`, any "Privilege Escalation" section, the security test suites (`test/**/security*`, acceptance tests). Those encode the maintainers' threat model and tell you what is already considered closed.

**Step 1 — Enumerate the privileged surface.** Build the list from the maintainers' own metadata rather than grepping at random: command metadata flags (`# <tool>:requires-sudo=true` and friends), unit and hook bodies, and the sudoers/polkit files themselves. The grep battery and file classes are in `references/privileged-surface-enumeration.md`. Nothing outside this list can be an LPE entry point.

**Step 2 — For each entry point, trace every input from the unprivileged caller.** Not just argv: `PATH`, environment (especially test-only override variables), `$HOME` and the XDG dirs, `/tmp/<app>-$uid`, `/run/user/$uid` (its *directory names* are user-controlled), `/proc/$PID` data including processes an attacker can arrange by PID reuse, symlinks at every path root touches, file and directory names, and any path used *after* it was validated. Input classes and the environment-variable tells are in the references file.

**Step 3 — Judge, then kill.** For each candidate write down: file:line, the exact code, which process runs as root, the attacker-controlled input, the step-by-step sequence, and why the existing guard fails. Then hunt for the guard that kills it — pinned `PATH`, root-ownership walks up to `/`, staging file plus atomic rename, an allow-list of sub-actions, a symlink refusal, a re-validation in the privileged half. A guard that exists means the lead is dead; record it as dead rather than hedging it into the report.

**Step 4 — Dupe-check before writing up.** Read the project's release notes and security pages for the class, and search for the target plus the class. Projects with a security team ship per-release "security fixes" lists naming the exact class they closed; if your class is on that list, you have a dupe, not a finding. See the `bb-dupe-avoidance` skill.

**Step 5 — Parallel coverage, verified centrally.** Split the surface by cluster — root-side halves of each elevation command; UI/shell plus the default config tree; installer plus `/etc` templates; migrations/update/provisioning pipeline; the authorization audit — one subagent per cluster. Tell each child which files are already cleared so they do not re-report them, and require file:line plus quoted real code plus the escalation sequence. Child summaries are self-reports: verify every lead in the source yourself before it reaches the user.

## Pitfalls

- **Deliberate developer trust is out of scope, and saying why is part of the job.** A documented feature that puts a user-owned checkout on root's `secure_path` or trusted root is an explicit decision by the administrator, not an LPE. Name it as a boundary and move on.
- **Comment density is not security.** This class of codebase documents every guard in prose. Read the code under the comment, and weight files with *no* security commentary higher than hardened ones — the hardening budget was spent where the maintainers were already thinking.
- **Test-only override variables are the highest-yield lead.** `path=${APP_SOMETHING_DIR:-/etc/real}` read in a root context turns a root write or delete into a user-directed one. Grep every `${...:-}` default adjacent to a `sudo`/`pkexec`/`as_root` call and ask what a plain user gets by exporting it.
- **A script has two trust domains; trace them separately.** The `EUID == 0` branch and the unprivileged wrapper branch run from different PATHs and read different inputs. A helper that is safe as the user is frequently the dangerous one after it re-execs itself through sudo/pkexec — check that the privileged half pins `PATH` and re-validates rather than trusting what the wrapper passed.
- **Before calling a sudoers rule stretchable, check what actually stops it.** Sudoers argument matching, the user spec (`%wheel` vs `ALL`), and the helper's own re-validation all have to fail together. The helper validating the same shape is usually what makes the grant safe, so read the helper, not just the rule.
- **Root-context daemons that read user-owned state are the second-highest yield.** Suspend/resume hooks, package-transaction hooks, and first-boot services run as root with no prompt and are triggerable by any active session. Trace their file reads, their glob expansion into user-owned directories, and whether a directory they write into can be pre-created by a user.
- **Do not dress up an already-fixed class.** Root-equivalent group grants — docker above all — are the most commonly re-reported LPE in this space; confirm the current install path does not grant it, and that any opt-in that does is explicitly warned, before you consider it.

## Reporting

Report findings, not the audit. For each: the finding in one line, file:line, the root context, the attacker-controlled input, the step sequence, and why existing guards fail — evidence first, no process narration. Close with what was audited and cleared, and say plainly when nothing survived (a defended codebase is a result, not a failure). Demonstrated impact only: a path that stops at "could write a config file" is not an LPE until you show root from it.
