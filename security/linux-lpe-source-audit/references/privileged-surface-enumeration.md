# Enumerating the privileged surface

Depth for step 1 and step 2 of the audit. Everything an LPE can live in is in this file's lists.

## 1. Find every way privilege is obtained

```bash
# Passwordless authorization shipped by the project
grep -rn "NOPASSWD" --include='*' . | grep -v '^./.git'
find . -path ./.git -prune -o \( -name '*.policy' -o -name '*sudoers*' -o -name '*polkit*' \) -print
grep -rn "usermod -aG\|gpasswd -a\|groupadd" bin/ install/ | sort -u   # root-equivalent groups

# Other privilege primitives
grep -rnE "setcap|getcap|chmod [0-7]*[4-7][0-7][0-7]|install -m 4" --include='*' . | grep -v '^./.git'

# The project's own map of elevating commands (metadata beats grepping)
grep -rl "requires-sudo=true\|requires_sudo" bin/ | sort
```

## 2. Find every root execution context

```bash
# Shell-level elevation entry points
grep -rn "EUID == 0\|EUID != 0\|require_root\|as_root\|pkexec\|setpriv\|runuser\|sudo -b\|sudo -n" bin/ install/ migrations/ | sort

# Root-owned system contexts
find . -path ./.git -prune -o \( -name '*.service' -o -name '*.timer' -o -name '*.path' -o -name '*.hook' \) -print
find . -path ./.git -prune -o \( -path '*system-sleep*' -o -path '*tmpfiles.d*' -o -path '*udev/rules.d*' -o -path '*libalpm/hooks*' -o -path '*polkit-1*' \) -print
ls default/systemd/system install/provisioning 2>/dev/null   # root units shipped outside the package manager
```

For each unit/hook ask three questions in order: what does it exec, what does that program read, and can a plain user run the same operation from a session (suspend, a package transaction, a login)?

## 3. Inputs the unprivileged caller controls

Trace every one of these into each root context above:

| Input | Why it bites |
|---|---|
| `PATH` | root resolving a bare helper out of a user-writable dir; sudo's `secure_path` vs the script's own `PATH` are different answers |
| Environment, esp. `*_DIR`/`*_ROOT`/`*_MARKER` overrides | test hooks left in shipping code redirect root writes/deletes |
| `$HOME`, `~/.config`, `~/.local/state` | a root step reading user config or state, or a file swap under a path root later consumes |
| `/tmp/<app>-$uid`, `/run/user/$uid` | directory and file *names* are user-chosen; a root glob into them picks up attacker names |
| `/proc/$PID` (`cmdline`, `stat`, `status`) | can be spoofed by arranging the process, and reused across PIDs |
| symlinks at any path root touches | validate-then-use, staging files, and log/state paths |
| file/dir names in a directory the user owns | become filenames or arguments in the root half |
| anything validated *before* elevation | TOCTOU |

## 4. Guard or finding — the decision table

| Looks like a finding | Kill it when |
|---|---|
| `sudo <script>` in a command the user runs | the user authenticates that step; consented elevation |
| `NOPASSWD` grant | the rule names an absolute packaged path, the arguments are fixed or tightly regexed, and the helper re-validates the same shape |
| Root reads `$HOME/...` | every path component is proven root-owned and not group/world-writable before use |
| Root writes at a user-influenced name | the parent directory is root-owned and cannot be pre-created by the user |
| Root execs a path from a variable | the variable is root-owned state (a root-owned config file, a pinned `/usr/bin` path), not caller environment |
| Group grant (docker/input) | it is an explicit, warned opt-in, not the default install path |
| Environment override redirects a root write | the root half ignores the variable (`EUID == 0` branch re-defaults it to the system path) |
| TOCTOU between check and use | the privileged half re-checks after elevation, or stages into a root-only dir and renames |

## 5. Cluster split for parallel review

One child per cluster, each told which files are already cleared and required to return file:line plus quoted real code plus the escalation sequence:

1. root-side halves of every elevation command in `bin/` (excluding the ones already cleared)
2. desktop shell / UI tree plus the default config tree (units, hooks, bash env, menu definitions)
3. `install/` plus the `/etc` templates
4. migrations, update, provisioning and factory-reset pipeline
5. the authorization audit on its own (sudoers, polkit, groups, capability, grant lifecycle)

Verify every child lead in the source before reporting: a child claiming a finding is a claim, not evidence.
