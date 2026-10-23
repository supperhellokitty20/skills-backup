#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  init-patchstack-audit.sh --program PROGRAM --plugin PLUGIN_OR_ZIP [options]
  init-patchstack-audit.sh --program PROGRAM --plugin-source DIR [options]

Create a Patchstack-style WordPress plugin research workspace and extract/copy source.

Options:
  --program VALUE           Patchstack program URL/name or scope reference.
  --plugin VALUE            WordPress.org slug, local zip path, or plugin zip URL.
  --plugin-source DIR       Existing extracted plugin source directory.
  --plugin-dir NAME         Expected plugin directory name.
  -o, --output DIR          Research workspace. Default: ./<target>-research
  --force                   Replace output directory if it exists.
  --start-lab               Start a local WordPress lab after source extraction.
  --lab-port PORT           Port for --start-lab. Default: auto-selected.
  --no-activate             With --start-lab, install WordPress but do not activate the plugin.
  -h, --help                Show this help.
USAGE
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

absolute_dir_existing() {
  (cd "$1" && pwd -P)
}

absolute_dir_create() {
  mkdir -p "$1"
  (cd "$1" && pwd -P)
}

safe_name() {
  local value
  value=${1%%\?*}
  value=${value%%#*}
  value=$(basename "$value")
  value=${value%.zip}
  value=${value%.ZIP}
  value=$(printf '%s' "$value" | tr -cs 'A-Za-z0-9._-' '-')
  value=${value#-}
  value=${value%-}
  printf '%s\n' "${value:-plugin}"
}

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
skill_dir=$(cd "$script_dir/.." && pwd -P)
extractor="${CODEX_HOME:-$HOME/.codex}/skills/wordpress-plugin-extractor/scripts/extract-wordpress-plugin.sh"
lab_script="$script_dir/setup-wordpress-plugin-lab.sh"

program=""
plugin_spec=""
plugin_source=""
plugin_dir=""
output_dir=""
force=0
start_lab=0
lab_port=""
no_activate=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --program)
      [[ $# -ge 2 ]] || die "--program requires a value"
      program=$2
      shift 2
      ;;
    --plugin)
      [[ $# -ge 2 ]] || die "--plugin requires a value"
      plugin_spec=$2
      shift 2
      ;;
    --plugin-source)
      [[ $# -ge 2 ]] || die "--plugin-source requires a value"
      plugin_source=$2
      shift 2
      ;;
    --plugin-dir)
      [[ $# -ge 2 ]] || die "--plugin-dir requires a value"
      plugin_dir=$2
      shift 2
      ;;
    -o|--output)
      [[ $# -ge 2 ]] || die "$1 requires a value"
      output_dir=$2
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --start-lab)
      start_lab=1
      shift
      ;;
    --lab-port)
      [[ $# -ge 2 ]] || die "--lab-port requires a value"
      lab_port=$2
      shift 2
      ;;
    --no-activate)
      no_activate=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$program" ]] || die "--program is required"
if [[ -n "$plugin_spec" && -n "$plugin_source" ]]; then
  die "use either --plugin or --plugin-source, not both"
fi
[[ -n "$plugin_spec" || -n "$plugin_source" ]] || die "provide --plugin or --plugin-source"

need_cmd tar

target_name=${plugin_dir:-}
if [[ -z "$target_name" ]]; then
  if [[ -n "$plugin_source" ]]; then
    target_name=$(basename "$plugin_source")
  else
    target_name=$(safe_name "$plugin_spec")
  fi
fi

if [[ -z "$output_dir" ]]; then
  output_dir="./${target_name}-research"
fi

if [[ -e "$output_dir" ]]; then
  if [[ "$force" -eq 1 ]]; then
    rm -rf "$output_dir"
  else
    die "output directory already exists: $output_dir; pass --force or choose a new path"
  fi
fi

workspace=$(absolute_dir_create "$output_dir")
mkdir -p "$workspace/source" "$workspace/findings" "$workspace/poc" "$workspace/evidence" "$workspace/reports"

source_path=""
extract_log="$workspace/extract.log"

if [[ -n "$plugin_source" ]]; then
  [[ -d "$plugin_source" ]] || die "plugin source directory not found: $plugin_source"
  plugin_source=$(absolute_dir_existing "$plugin_source")
  plugin_dir=${plugin_dir:-$(basename "$plugin_source")}
  source_path="$workspace/source/$plugin_dir"
  mkdir -p "$source_path"
  (cd "$plugin_source" && tar -cf - .) | (cd "$source_path" && tar -xf -)
  printf 'Copied plugin source: %s\n' "$source_path" | tee "$extract_log" >/dev/null
else
  [[ -x "$extractor" ]] || die "wordpress-plugin-extractor script not found or not executable: $extractor"
  extract_args=(--plugin "$plugin_spec" --output "$workspace/source" --force)
  if [[ -n "$plugin_dir" ]]; then
    extract_args+=(--plugin-dir "$plugin_dir")
  fi
  "$extractor" "${extract_args[@]}" | tee "$extract_log"
  source_path=$(awk -F': ' '/Extracted plugin source:/ {print $2}' "$extract_log" | tail -n 1)
  [[ -n "$source_path" && -d "$source_path" ]] || die "could not determine extracted source path from $extract_log"
  plugin_dir=$(basename "$source_path")
fi

cat > "$workspace/ENGAGEMENT.md" <<EOF
# Engagement

- Program: $program
- Plugin input: ${plugin_spec:-$plugin_source}
- Plugin directory: $plugin_dir
- Source path: $source_path
- PoC root: $workspace/poc
- Evidence root: $workspace/evidence
- Reports root: $workspace/reports
- Created: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Scope Notes

- TODO: Confirm this plugin/version is in the Patchstack program scope.
- TODO: Record allowed testing types and exclusions.
- TODO: Record tested version from plugin header/readme.

## Local-Only Default

Use local Docker verification unless the program scope explicitly authorizes another target.
EOF

cat > "$workspace/RECON.md" <<'EOF'
# Recon

## Plugin Metadata

- Plugin name:
- Version:
- Main plugin file:
- Dependencies:

## Focus Areas

1.

## Entry Points

## Trust Boundaries

## Security Controls

## High-Risk Sinks
EOF

cat > "$workspace/findings/VULN-FINDINGS.json" <<'EOF'
[]
EOF

cat > "$workspace/TRIAGE.md" <<'EOF'
# Triage

## Confirmed

## Needs More Evidence

## Dismissed
EOF

cat > "$workspace/poc/INDEX.md" <<'EOF'
# PoC Index

Create one directory per candidate or confirmed vulnerability:

```text
poc/<finding-slug>/
  request.http
  curl.sh
  payload.txt
  verify.md
```

Keep PoCs local-lab focused unless the program scope explicitly authorizes another target.
EOF

cat > "$workspace/evidence/INDEX.md" <<'EOF'
# Evidence Index

Store raw responses, logs, database observations, screenshots notes, and filesystem proof under `evidence/<finding-slug>/`.
EOF

cat > "$workspace/reports/REPORT-DRAFT.md" <<'EOF'
# Report Draft

Use the skill reference report template:

EOF
printf '%s/references/report-template.md\n' "$skill_dir" >> "$workspace/reports/REPORT-DRAFT.md"

if [[ "$start_lab" -eq 1 ]]; then
  [[ -x "$lab_script" ]] || die "lab script not found or not executable: $lab_script"
  lab_args=(--plugin-source "$source_path" --output "$workspace/lab")
  if [[ -n "$lab_port" ]]; then
    lab_args+=(--port "$lab_port")
  fi
  if [[ "$no_activate" -eq 1 ]]; then
    lab_args+=(--no-activate)
  fi
  "$lab_script" "${lab_args[@]}" | tee "$workspace/lab.log"
fi

printf '\nPatchstack research workspace: %s\n' "$workspace"
printf 'Plugin source: %s\n' "$source_path"
printf 'PoC root: %s\n' "$workspace/poc"
printf 'Evidence root: %s\n' "$workspace/evidence"
printf 'Reports root: %s\n' "$workspace/reports"
printf 'Recon file: %s\n' "$workspace/RECON.md"
printf 'Findings file: %s\n' "$workspace/findings/VULN-FINDINGS.json"
if [[ "$start_lab" -eq 0 ]]; then
  printf 'Start lab: %s --plugin-source %s --output %s/lab\n' "$lab_script" "$source_path" "$workspace"
fi
