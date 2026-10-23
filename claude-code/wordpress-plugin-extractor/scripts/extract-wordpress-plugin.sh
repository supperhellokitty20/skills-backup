#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  extract-wordpress-plugin.sh --plugin PLUGIN_OR_ZIP [options]
  extract-wordpress-plugin.sh PLUGIN_OR_ZIP [options]

Extract WordPress plugin source by creating a temporary Docker WordPress install.

Inputs:
  PLUGIN_OR_ZIP can be a WordPress.org slug, local .zip path, or direct .zip URL.

Options:
  --plugin VALUE              Plugin slug, local zip path, or zip URL.
  -o, --output DIR            Output root directory. Default: ./extracted-wordpress-plugins
  --plugin-dir NAME           Expected installed plugin directory name.
  --activate                  Activate the plugin after installation.
  --force                     Replace destination plugin directory if it already exists.
  --keep                      Keep the temporary compose project and files for debugging.
  --wordpress-image IMAGE     WordPress image. Default: wordpress:php8.2-apache
  --wpcli-image IMAGE         WP-CLI image. Default: wordpress:cli-php8.2
  --db-image IMAGE            Database image. Default: mariadb:11
  -h, --help                  Show this help.

Examples:
  extract-wordpress-plugin.sh --plugin woocommerce
  extract-wordpress-plugin.sh --plugin ~/Downloads/premium-plugin.zip --output ./sources
  extract-wordpress-plugin.sh --plugin https://example.com/plugin.zip --plugin-dir plugin-folder
USAGE
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

absolute_dir() {
  mkdir -p "$1"
  (cd "$1" && pwd -P)
}

absolute_file() {
  local file_dir file_base
  file_dir=$(dirname "$1")
  file_base=$(basename "$1")
  (cd "$file_dir" && printf '%s/%s\n' "$(pwd -P)" "$file_base")
}

candidate_from_spec() {
  local spec base
  spec=$1
  spec=${spec%%\?*}
  spec=${spec%%#*}
  base=$(basename "$spec")
  base=${base%.zip}
  base=${base%.ZIP}
  printf '%s\n' "$base"
}

plugin_spec=""
output_root="./extracted-wordpress-plugins"
plugin_dir=""
activate=0
force=0
keep=0
wordpress_image="${WORDPRESS_IMAGE:-wordpress:php8.2-apache}"
wpcli_image="${WPCLI_IMAGE:-wordpress:cli-php8.2}"
db_image="${DB_IMAGE:-mariadb:11}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin)
      [[ $# -ge 2 ]] || die "--plugin requires a value"
      plugin_spec=$2
      shift 2
      ;;
    -o|--output)
      [[ $# -ge 2 ]] || die "$1 requires a value"
      output_root=$2
      shift 2
      ;;
    --plugin-dir)
      [[ $# -ge 2 ]] || die "--plugin-dir requires a value"
      plugin_dir=$2
      shift 2
      ;;
    --activate)
      activate=1
      shift
      ;;
    --force)
      force=1
      shift
      ;;
    --keep)
      keep=1
      shift
      ;;
    --wordpress-image)
      [[ $# -ge 2 ]] || die "--wordpress-image requires a value"
      wordpress_image=$2
      shift 2
      ;;
    --wpcli-image)
      [[ $# -ge 2 ]] || die "--wpcli-image requires a value"
      wpcli_image=$2
      shift 2
      ;;
    --db-image)
      [[ $# -ge 2 ]] || die "--db-image requires a value"
      db_image=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      if [[ -z "$plugin_spec" ]]; then
        plugin_spec=$1
      else
        die "unexpected argument: $1"
      fi
      shift
      ;;
  esac
done

[[ -n "$plugin_spec" ]] || {
  usage >&2
  exit 2
}

need_cmd docker
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required; expected 'docker compose' to work"

output_root=$(absolute_dir "$output_root")
workdir=$(mktemp -d "${TMPDIR:-/tmp}/wp-plugin-extract.XXXXXX")
project="wpextract$(date +%s)$$"
compose_file="$workdir/compose.yaml"
mkdir -p "$workdir/input"

cleanup() {
  local status=$?
  if [[ "$keep" -eq 1 ]]; then
    printf 'Kept Docker Compose project %s in %s\n' "$project" "$workdir" >&2
    exit "$status"
  fi
  docker compose -f "$compose_file" -p "$project" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$workdir"
  exit "$status"
}
trap cleanup EXIT

install_spec=$plugin_spec
if [[ -f "$plugin_spec" ]]; then
  source_zip=$(absolute_file "$plugin_spec")
  cp "$source_zip" "$workdir/input/"
  install_spec="/input/$(basename "$source_zip")"
fi

cat > "$compose_file" <<YAML
services:
  db:
    image: ${db_image}
    environment:
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wordpress
      MARIADB_PASSWORD: wordpress
      MARIADB_ROOT_PASSWORD: root
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mariadb-admin", "ping", "-h", "localhost", "-uroot", "-proot"]
      interval: 2s
      timeout: 5s
      retries: 30

  wordpress:
    image: ${wordpress_image}
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wp_data:/var/www/html
    depends_on:
      db:
        condition: service_healthy

  wpcli:
    image: ${wpcli_image}
    working_dir: /var/www/html
    user: "33:33"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
      HOME: /tmp
      WP_CLI_CACHE_DIR: /tmp/wp-cli-cache
    volumes:
      - wp_data:/var/www/html
      - ./input:/input:ro
    depends_on:
      db:
        condition: service_healthy
      wordpress:
        condition: service_started

volumes:
  db_data:
  wp_data:
YAML

compose() {
  docker compose -f "$compose_file" -p "$project" "$@"
}

wp() {
  compose run --rm -T wpcli wp "$@"
}

wait_for_wordpress_files() {
  local attempt
  for attempt in $(seq 1 90); do
    if compose exec -T wordpress test -f /var/www/html/wp-config.php >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  compose logs --no-color db wordpress >&2 || true
  die "WordPress files were not initialized in time"
}

printf 'Starting temporary WordPress project %s...\n' "$project"
compose up -d db wordpress >/dev/null
wait_for_wordpress_files

if ! wp core is-installed >/dev/null 2>&1; then
  wp core install \
    --url=http://localhost \
    --title="Plugin Extract" \
    --admin_user=admin \
    --admin_password=adminpass \
    --admin_email=admin@example.com \
    --skip-email >/dev/null
fi

before_file="$workdir/plugins-before.txt"
after_file="$workdir/plugins-after.txt"
wp plugin list --field=name | sort > "$before_file"

install_args=("$install_spec")
if [[ "$activate" -eq 1 ]]; then
  install_args+=("--activate")
fi

printf 'Installing plugin: %s\n' "$plugin_spec"
wp plugin install "${install_args[@]}"

wp plugin list --field=name | sort > "$after_file"

if [[ -z "$plugin_dir" ]]; then
  plugin_dir=$(comm -13 "$before_file" "$after_file" | head -n 1 || true)
fi

if [[ -z "$plugin_dir" ]]; then
  candidate=$(candidate_from_spec "$plugin_spec")
  if [[ -n "$candidate" ]] && wp plugin is-installed "$candidate" >/dev/null 2>&1; then
    plugin_dir=$candidate
  fi
fi

[[ -n "$plugin_dir" ]] || die "could not infer installed plugin directory; rerun with --plugin-dir NAME"

if ! compose exec -T wordpress test -d "/var/www/html/wp-content/plugins/$plugin_dir" >/dev/null 2>&1; then
  die "plugin directory not found in WordPress install: $plugin_dir"
fi

destination="$output_root/$plugin_dir"
if [[ -e "$destination" ]]; then
  if [[ "$force" -eq 1 ]]; then
    rm -rf "$destination"
  else
    die "destination already exists: $destination; choose another --output or pass --force"
  fi
fi

mkdir -p "$output_root"
compose cp "wordpress:/var/www/html/wp-content/plugins/$plugin_dir" "$output_root/" >/dev/null

printf 'Extracted plugin source: %s\n' "$destination"
