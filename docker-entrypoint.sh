#!/bin/bash
set -e

echo "========== Frappe Bench Initialization =========="

BENCH_DIR="/home/frappe/frappe-bench"
WORKSPACE="/workspace"
SITE_NAME="site1.local"

# Wait for database to be ready
echo "Waiting for MariaDB to be ready..."
for attempt in $(seq 1 60); do
  if python3 <<'PY' >/dev/null 2>&1
import socket
import sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    sock.connect(("mariadb", 3306))
    sys.exit(0)
except Exception:
    sys.exit(1)
finally:
    sock.close()
PY
  then
    echo "✓ MariaDB is ready"
    break
  fi

  echo "  Attempt ${attempt}: waiting..."
  sleep 2
done

if ! python3 <<'PY' >/dev/null 2>&1
import socket
import sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    sock.connect(("mariadb", 3306))
    sys.exit(0)
except Exception:
    sys.exit(1)
finally:
    sock.close()
PY
then
  echo "✗ MariaDB not available"
  exit 1
fi

echo "\nStep 1: Initializing bench..."
if [ -d "$BENCH_DIR/apps/frappe" ]; then
  echo "  ✓ Existing bench found"
else
  if [ -e "$BENCH_DIR" ]; then
    echo "  Removing incomplete bench directory"
    find "$BENCH_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  fi
  echo "  Running bench init..."
  set +e
  bench init "$BENCH_DIR" --frappe-branch version-15 --python python3 --ignore-exist
  INIT_RESULT=$?
  set -e
  if [ $INIT_RESULT -eq 0 ] || [ -d "$BENCH_DIR/apps/frappe" ]; then
    echo "  ✓ Bench initialized"
  else
    echo "  WARNING: bench init returned $INIT_RESULT, but continuing..."
  fi
fi

echo "\nStep 2: Linking app..."
APP_LINK="$BENCH_DIR/apps/cb_maintenance"
if [ "$(readlink "$APP_LINK" 2>/dev/null || true)" != "$WORKSPACE" ]; then
  rm -rf "$APP_LINK"
  ln -s "$WORKSPACE" "$APP_LINK"
fi
if ! "$BENCH_DIR/env/bin/python" -c "import cb_maintenance" >/dev/null 2>&1; then
  "$BENCH_DIR/env/bin/pip" install -q -e "$APP_LINK"
fi
APPS_TXT="$BENCH_DIR/sites/apps.txt"
sed -i 's/frappecb_maintenance/frappe\ncb_maintenance/g' "$APPS_TXT"
if ! grep -qx "cb_maintenance" "$APPS_TXT"; then
  printf "\ncb_maintenance\n" >> "$APPS_TXT"
fi
echo "  ✓ App linked"

echo "\nStep 3: Creating site..."
cd "$BENCH_DIR" || { echo "ERROR: Cannot cd to $BENCH_DIR"; exit 1; }
echo "  Current dir: $(pwd)"
if [ -d "$BENCH_DIR/sites/$SITE_NAME" ] && bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
  echo "  ✓ Existing site found"
else
  rm -rf "$BENCH_DIR/sites/$SITE_NAME"
  bench new-site "$SITE_NAME" \
    --db-host mariadb \
    --db-root-password root \
    --admin-password admin \
    --no-mariadb-socket \
    --force \
    --set-default
  echo "  ✓ Site created"
fi

echo "\nStep 4: Installing app..."
if bench --site "$SITE_NAME" list-apps | grep -qx "cb_maintenance"; then
  echo "  ✓ App already installed"
else
  bench --site "$SITE_NAME" install-app cb_maintenance
  echo "  ✓ App installed"
fi

echo "\n========== Starting Bench =========="
exec bench start --no-dev
