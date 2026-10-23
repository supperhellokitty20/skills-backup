# Docker Desktop Linux VM on macOS

## Identify it

Host CPU for *all* containers is spent by one process: `com.apple.Virtualization.VirtualMachine.xpc` (re-parented to `launchd`, so the parent chain tells you nothing). Resolve which app owns it by the disk images it holds open:

```
lsof -p <PID> | grep -iE '\.(img|raw|qcow2?|vmdk|vhdx)$'
#  /Applications/Docker.app/Contents/Resources/linuxkit/desktop.img
#  ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw

docker info --format '{{.Name}} | {{.OperatingSystem}} | {{.KernelVersion}} | CPUs {{.NCPU}} | Mem {{.MemTotal}}'
#  docker-desktop | Docker Desktop | 6.12.69-linuxkit | CPUs 10 | Mem 30963515392
```

It is a **Linux** (linuxkit) VM. Docker Desktop on macOS cannot run Windows containers — if the user calls it "the Windows server", correct that in the first line.

Its instantaneous CPU is spiky and can exceed 100% (one core) while containers report single-digit percentages each; check with `ps -o pcpu= -p <PID>` across a few samples rather than one reading, and check `docker stats --no-stream` to see whether any container is actually busy. An idle 20-container VM still costs a few percent of a core, plus multi-GB RSS — that is overhead, not a runaway.

## Inventory before touching anything

```
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
docker system df
```
The PORTS column is how you tell the user which services will go dark (published bindings) and which come back after a restart.

## Stop everything gracefully, with a restart map

```
docker ps --format '{{.Names}}' | sort > /tmp/docker-was-running.txt   # BEFORE stopping — this is the restart map
docker stop -t 30 $(docker ps -q)                                      # ids echo back on success
docker ps -q | wc -l                                                   # must be 0
docker ps -a -q | wc -l                                                # unchanged: containers persist, exited
```

- Capture the names first. Without the file the user has to reconstruct which of their ~120 stopped containers were the live set.
- `docker stop -t 30` and not `docker kill`: Postgres/MySQL in these stacks need the graceful shutdown to flush. `docker kill` risks corrupt data files.
- `stop` preserves containers, volumes and data. Only `docker rm`, `docker compose down`, or `down -v` destroy state — say which one you are running and never use them for a "just stop it" request.
- Stopping containers returns CPU almost immediately; it does **not** return the VM's RAM (see below).

## Restart

```
docker start $(cat /tmp/docker-was-running.txt)          # the whole set back, same containers
```

Per stack, resolve the compose project from container labels — no need to guess directories:

```
docker ps -a --format '{{.Names}}|{{.Label "com.docker.compose.project"}}|{{.Label "com.docker.compose.project.working_dir"}}'
#  then: cd <working_dir> && docker compose start        (or `up -d` if compose created it)
```

- A **Supabase CLI-managed** stack reports an *empty* `working_dir` label — restart that one with `supabase start` in its project directory, not with compose.
- Read the label output rather than assuming which stacks are compose-managed; long-lived mixed sets (a Supabase CLI stack, several compose PoCs, Langfuse postgres+redis, a WordPress stack) are normal on a research machine.

## Memory and disk do not follow CPU

- Stopping containers leaves the VM's RSS allocated: `ps -o rss= -p <PID> | awk '{printf "%.1f GB", $1/1048576}'`. It can even grow while containers start/stop.
- `docker desktop stop` quits the VM entirely and releases that RAM; the VM comes back on the next docker command. Offer it when the user wants the memory back, not just the cores.
- Disk is a third axis: `docker system df` reports images / containers / volumes / build cache with a RECLAIMABLE column. Large reclaimable figures are normal after months of research stacks. `docker system prune` (stopped containers + unused images + cache), `docker image prune -a`, `docker builder prune` — confirm before pruning, since build cache and unused images may be wanted.
