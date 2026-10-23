#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  setup-wordpress-plugin-lab.sh --plugin-source DIR [options]

Create a disposable local Docker WordPress lab with a plugin mounted.

Options:
  --plugin-source DIR         Extracted plugin source directory.
  --plugin-dir NAME           Plugin directory name inside wp-content/plugins.
  -o, --output DIR            Lab directory. Default: ./wordpress-plugin-lab-<plugin>-<timestamp>
  --port PORT                 Host port. Default: auto-selected free localhost port.
  --no-activate               Do not activate the plugin.
  --wordpress-image IMAGE     WordPress image. Default: wordpress:php8.2-apache
  --wpcli-image IMAGE         WP-CLI image. Default: wordpress:cli-php8.2
  --db-image IMAGE            Database image. Default: mariadb:11
  -h, --help                  Show this help.
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

find_free_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

plugin_source=""
plugin_dir=""
output_dir=""
port=""
activate=1
wordpress_image="${WORDPRESS_IMAGE:-wordpress:php8.2-apache}"
wpcli_image="${WPCLI_IMAGE:-wordpress:cli-php8.2}"
db_image="${DB_IMAGE:-mariadb:11}"

while [[ $# -gt 0 ]]; do
  case "$1" in
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
    --port)
      [[ $# -ge 2 ]] || die "--port requires a value"
      port=$2
      shift 2
      ;;
    --no-activate)
      activate=0
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
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$plugin_source" ]] || die "--plugin-source is required"
[[ -d "$plugin_source" ]] || die "plugin source directory not found: $plugin_source"

need_cmd docker
need_cmd python3
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required; expected 'docker compose' to work"

plugin_source=$(absolute_dir_existing "$plugin_source")
plugin_dir=${plugin_dir:-$(basename "$plugin_source")}
if [[ -z "$output_dir" ]]; then
  output_dir="./wordpress-plugin-lab-${plugin_dir}-$(date +%Y%m%d-%H%M%S)"
fi
[[ ! -e "$output_dir" ]] || die "output directory already exists: $output_dir"
lab_dir=$(absolute_dir_create "$output_dir")
mkdir -p "$lab_dir/plugins/$plugin_dir"
(cd "$plugin_source" && tar -cf - .) | (cd "$lab_dir/plugins/$plugin_dir" && tar -xf -)

port=${port:-$(find_free_port)}
case "$port" in
  ''|*[!0-9]*) die "port must be numeric: $port" ;;
esac

safe_project=$(printf '%s' "$plugin_dir" | tr -cd 'A-Za-z0-9' | cut -c1-24)
project="wplab${safe_project:-plugin}$(date +%s)$$"
compose_file="$lab_dir/compose.yaml"

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
    ports:
      - "127.0.0.1:${port}:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wp_data:/var/www/html
      - ./plugins/${plugin_dir}:/var/www/html/wp-content/plugins/${plugin_dir}:rw
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
      - ./plugins/${plugin_dir}:/var/www/html/wp-content/plugins/${plugin_dir}:rw
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

printf 'Starting WordPress lab project %s...\n' "$project"
compose up -d db wordpress >/dev/null
wait_for_wordpress_files

wp core install \
  --url="http://127.0.0.1:${port}" \
  --title="Patchstack Plugin Lab" \
  --admin_user=admin \
  --admin_password=adminpass \
  --admin_email=admin@example.com \
  --skip-email >/dev/null

wp user create subscriber subscriber@example.com --user_pass=subscriberpass --role=subscriber >/dev/null 2>&1 || true
wp user create contributor contributor@example.com --user_pass=contributorpass --role=contributor >/dev/null 2>&1 || true
wp user create author author@example.com --user_pass=authorpass --role=author >/dev/null 2>&1 || true
wp user create editor editor@example.com --user_pass=editorpass --role=editor >/dev/null 2>&1 || true

if [[ "$activate" -eq 1 ]]; then
  if ! wp plugin activate "$plugin_dir"; then
    wp plugin list >&2 || true
    die "plugin activation failed for '$plugin_dir'; rerun with --plugin-dir or --no-activate"
  fi
fi

wp rewrite structure '/%postname%/' >/dev/null
wp rewrite flush >/dev/null

cat > "$lab_dir/LAB.md" <<EOF
# WordPress Plugin Lab

- URL: http://127.0.0.1:$port
- Plugin directory: $plugin_dir
- Plugin source copy: $lab_dir/plugins/$plugin_dir
- Compose project: $project

## Credentials

- admin / adminpass
- subscriber / subscriberpass
- contributor / contributorpass
- author / authorpass
- editor / editorpass

## Commands

WP-CLI:

\`\`\`bash
docker compose -f "$compose_file" -p "$project" run --rm -T wpcli wp plugin list
\`\`\`

Logs:

\`\`\`bash
docker compose -f "$compose_file" -p "$project" logs --no-color wordpress
\`\`\`

Teardown:

\`\`\`bash
docker compose -f "$compose_file" -p "$project" down -v --remove-orphans
\`\`\`
EOF

printf '\nWordPress lab ready: http://127.0.0.1:%s\n' "$port"
printf 'Lab notes: %s/LAB.md\n' "$lab_dir"
printf 'Teardown: docker compose -f %s -p %s down -v --remove-orphans\n' "$compose_file" "$project"
