#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running cb_maintenance local setup script from: $ROOT_DIR"

check_command() { command -v "$1" >/dev/null 2>&1; }

# Ensure Docker / Colima
if check_command docker && docker info >/dev/null 2>&1; then
  echo "Docker daemon available"
else
  echo "Docker daemon not available. Attempting to use Colima..."
  if ! check_command colima; then
    if check_command brew; then
      echo "Installing colima and docker via Homebrew (requires sudo/password if prompted)"
      brew install docker colima
    else
      echo "Please install Docker Desktop or Colima + Docker CLI and re-run this script."
      exit 1
    fi
  fi
  echo "Starting Colima"
  colima start
  export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
fi

echo "Cleaning previous Docker/bench state"
docker-compose down || true
docker-compose down -v || true
sleep 2

# Remove bench directory completely for fresh start
if [ -d "$ROOT_DIR/bench" ]; then
  rm -rf "$ROOT_DIR/bench"
  echo "Removed ./bench directory for fresh initialization"
fi

# Force remove all mariadb volumes
docker volume rm cb_maintenance_mariadb_data 2>/dev/null || true

echo "Building and bringing up services..."
# Use cached build unless forced rebuild is needed
docker-compose up --build -d

# Give services time to start and initialize
sleep 8

echo "Waiting for the site to become available (http://localhost:8000). This may take several minutes..."
MAX_WAIT=900
WAITED=0
SLEEP_INTERVAL=5
while ! curl -sSf http://localhost:8000 >/dev/null 2>&1; do
  WAITED=$((WAITED+SLEEP_INTERVAL))
  if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "Timed out waiting for site. Check container logs with: docker-compose logs -f frappe"
    docker-compose logs --tail=200 frappe
    exit 1
  fi
  sleep "$SLEEP_INTERVAL"
done

echo "Site is up at: http://localhost:8000"

read -r -p "Import case seed data into site1.local now? [y/N] " RESP
if [[ "$RESP" =~ ^[Yy]$ ]]; then
  echo "Importing seed data..."
  docker-compose exec -u frappe -T frappe bash -lc "cd /home/frappe/frappe-bench && bench --site site1.local execute cb_maintenance.maintenance_ops.setup.import_case_data.run"
  echo "Import finished."
else
  echo "Skipping seed data import."
fi

echo "Done. Visit http://localhost:8000 and log in with user 'Administrator' and password 'admin' (if created)."
