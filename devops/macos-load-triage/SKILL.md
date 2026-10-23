---
name: macos-load-triage
description: Use when macOS CPU load is high or a process must stop.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [macos, diagnostics, process-management, docker, troubleshooting]
    related_skills: [systematic-debugging]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | This skill ships artifacts: `references/docker-desktop-vm.md`, `scripts/macos-load-snapshot.sh` — list them and treat them as part of this skill's context |
| 3 | Usage | Use the shipped scripts/templates exactly as documented in the body — do not re-implement them inline |
| 4 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-3 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] All bundled files enumerated and relevant ones read
- [ ] Protocol confirmed before any work started

# macOS Load Triage

Diagnose what is consuming a Mac and reclaim it without collateral damage: identifying runaway processes (apps, daemons, VMs, emulators, containers), attributing load to the right layer, stopping them with consent, and proving it worked.

## When to Use

- "Why is my CPU / load so high?", "what's eating my machine?", "the laptop is bogged down".
- A process, emulator, or container set must be stopped to give the machine back to the user.
- A long-running process someone else started (an agent session, a build, an emulator) is still spinning and nobody remembers what it was for.

Not for: code-level bugs (use `systematic-debugging`), driving the macOS UI (`apple:macos-computer-use`), or container escape / privilege work (`docker-privesc`).

## Always-on rules

- **Name the culprit in plain language before the flags.** "An Android emulator for AVD `lnpoc`, started 14 days ago by a Claude Code session, eating 7 of 10 cores" answers the question; the `qemu-system-aarch64-headless -avd lnpoc -gpu swiftshader_indirect` command line does not, and a table built from it reads as noise. Users do not recognize `com.apple.Virtualization.VirtualMachine.xpc` as "Docker Desktop's Linux VM" either — the identifier never does the explaining, and never make them guess the guest OS.
- **Diagnose and reclaim are two separate asks.** When the user asks *why* load is high, report the finding plus the exact stop command and wait for their word. When they say kill it, kill it and verify — do not re-explain, re-ask, or repeat the diagnosis.
- **Graceful before force on anything holding data.** `docker stop -t 30` over `docker kill`, SIGTERM before `kill -9`, `adb emu kill` over killing the qemu process. A hard kill can corrupt Postgres/MySQL data files; a clean flush costs seconds.
- **Verify every stop by reading state back, never by exit code.** `ps -p <PID>`, `pgrep -fl <pattern>`, `docker ps -q | wc -l` — and confirm the launcher parent exited too. Report before → after numbers in the same reply.
- **Never retry a blocked destructive command.** If a destructive command's approval prompt times out, nothing ran and there is no consent. Do a read-only check to confirm state is untouched, then ask explicitly with what will go down (name the stacks/services) and offer graceful vs force. Silently re-issuing the blocked command is the failure to avoid.
- **Say what was NOT reclaimed.** Stopping containers frees CPU but not the VM's RAM; a killed app frees cores but not disk. Separate the axes explicitly.

## Procedure

### 1. Measure
One shot: `scripts/macos-load-snapshot.sh` prints everything steps 1–3 need (load vs cores, top processes, CPU/memory summary, thermal state, per-thread CPU for the hottest PID, its parent chain, and any VM disk images it holds open).

By hand:
```
uptime; sysctl -n hw.ncpu; sysctl -n hw.model
ps -Ao pid,ppid,pcpu,pmem,rss,etime,user,args -r | head -15
top -l 2 -n 0 -s 1 | grep -E 'Processes:|Load Avg|CPU usage|PhysMem'
```

- **Load average on macOS is a raw thread count, not a percentage.** Divide by `hw.ncpu`: load 18 on a 10-core box is 1.8x saturated. It also counts threads in uninterruptible wait, so high load with high idle CPU is possible — normal in the decaying tail right after a fix.
- The 1/5/15-min averages decay slowly. Re-measure ~45s after the fix and report the 1-min figure *moving*; do not claim the problem is solved from the stop command alone.
- Read the shape of the load: one thread at 700%, versus four vCPU threads at ~70% each, versus hundreds of small threads (a build) mean very different things.

### 2. Attribute to threads
```
ps -M -p <PID> | sort -k2 -nr | head -12      # column 2 is per-thread %CPU
```
This is what separates an emulator's vCPU threads (each ~70% of a core) plus emulation threads from a single pegged thread. Then compare instantaneous %CPU against cumulative CPU time (`ps -o time= -p <PID>`): a process at 70% now whose lifetime average is ~4% only started misbehaving recently — say so, because that changes whether a restart or a code fix is the answer.

### 3. Resolve opaque processes (VMs, emulators, XPC services)
- **Parent chain is useless for XPC-service VMs** — they are re-parented to `launchd` (ppid 1). Resolve identity by open disk images: `lsof -p <PID> | grep -iE '\.(img|raw|qcow2?|vmdk|vhdx)$'`. Docker Desktop ⇒ `Docker.app/Contents/Resources/linuxkit/desktop.img` + `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`; confirm with `docker info --format '{{.OperatingSystem}} {{.KernelVersion}} {{.NCPU}}'`.
- **Answer "for what" from provenance, not speculation.** Read the parent's full command line (`ps -p <ppid> -o args`) and its log redirect: a `/bin/zsh -c ... source ~/.claude/shell-snapshots/... && eval '...'` wrapper names the agent session that launched it, and `~/.claude/projects/*/*.jsonl` transcripts (grep the working-dir slug or the AVD/app name) reveal the project it belonged to — a bare AVD name usually expands into a named engagement.
- **Guests lie about their own CPU.** Check inside: `adb shell uptime; adb shell "top -n 1 -b | head -18"`. A guest showing most of its cores idle while guest sys/irq dominate means the *host* is burning cores on device/GPU emulation, not real guest work — a headless emulator with `-gpu swiftshader_indirect` (software rendering) is the classic case. A long-lived un-snapshotted boot is the usual trigger for the spin starting recently.
- Emulator/AVD identity: `emulator -list-avds`, `adb devices -l`, and the on-disk footprint `du -sh ~/.android/avd/*.avd` — quoting the size tells the user whether deleting it is cheap.

### 4. Rule out the innocent (cheap, usually not the cause)
```
pmset -g therm                                   # thermal warning recorded?
sysctl -n machdep.xcpm.cpu_thermal_level 2>/dev/null
memory_pressure | tail -5                        # pressure vs merely "used"
```
macOS daemons that look alarming but are back-pressure — `bird` (iCloud Drive), `mds`/`mdworker` (Spotlight), `deleted`/`deleted_helper` (CacheDelete), `duetexpertd`, `triald` — ramp up exactly when cores free up. They are catching up, not causing it: say that instead of presenting them as culprits.

### 5. Stop
| Target | Command | Note |
|---|---|---|
| Android emulator | `adb -s emulator-5554 emu kill` | clean; the launcher parent exits with it |
| Docker containers | `docker stop -t 30 $(docker ps -q)` | save the names to a restart map FIRST — see `references/docker-desktop-vm.md` |
| GUI app | normal quit, then SIGTERM | |
| Anything else | `kill <PID>` (SIGTERM), escalate to `kill -9` only if it survives | |

### 6. Verify and report
Re-check the PID and its parent are gone, then report:
- a short table of whichever consumers remain,
- before → after on load average and CPU idle percentage,
- an explicit split of what was reclaimed versus not (a container VM keeps its RSS after containers stop; disk is a separate axis from CPU),
- the restart path if it was something they will want back.

## Support files
- `scripts/macos-load-snapshot.sh` — one-shot snapshot covering steps 1–3.
- `references/docker-desktop-vm.md` — identifying the Docker Desktop Linux VM, graceful stop-all with a restart map, memory/disk reclamation.