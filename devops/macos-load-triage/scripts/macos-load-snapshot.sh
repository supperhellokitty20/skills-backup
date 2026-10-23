#!/bin/bash
# One-shot macOS load snapshot: what is eating this machine right now.
# Usage: bash macos-load-snapshot.sh [PID_TO_DRILL]
# Covers steps 1-3 of the macos-load-triage skill.
set -u

echo "=== host / load (divide load by cores for saturation) ==="
uptime
echo "cores: $(sysctl -n hw.ncpu)   model: $(sysctl -n hw.model)"
echo
echo "=== top CPU consumers (ranked by recent CPU) ==="
ps -Ao pid,ppid,pcpu,pmem,rss,etime,user,args -r | head -15
echo
echo "=== CPU / memory summary (steady state, 2 samples) ==="
top -l 2 -n 0 -s 1 2>/dev/null | grep -E 'Processes:|Load Avg|CPU usage|PhysMem'
echo
echo "=== thermal + memory pressure ==="
pmset -g therm 2>/dev/null
sysctl -n machdep.xcpm.cpu_thermal_level 2>/dev/null
memory_pressure 2>/dev/null | tail -3
echo

# Pick the hottest process if none was given.
PID="${1:-}"
if [ -z "$PID" ]; then
  PID=$(ps -Ao pid,pcpu -r | awk 'NR==2{print $1}')
fi

echo "=== per-thread CPU for PID $PID (column 2 = %CPU) ==="
ps -M -p "$PID" 2>/dev/null | sort -k2 -nr | head -12
echo
echo "=== identity of PID $PID ==="
ps -p "$PID" -o pid,ppid,pcpu,pmem,rss,etime,state,args 2>/dev/null
echo "--- parent chain (parent args often reveal which session launched it) ---"
PP=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' ')
if [ -n "${PP:-}" ]; then
  ps -p "$PP" -o pid,ppid,etime,args 2>/dev/null
fi
echo "--- VM / disk images it holds open (identifies which app owns an XPC VM) ---"
lsof -p "$PID" 2>/dev/null | grep -iE '\.(img|raw|qcow2?|hdd|vmdk|vhdx)$' | awk '{print $9}' | sort -u
echo "--- cumulative CPU time (compare against instantaneous %CPU) ---"
ps -o pid,time= -p "$PID" 2>/dev/null
