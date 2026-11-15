#!/bin/sh
# Put a sealed snapshot on the API origin: its public files at /data/<id>/, and search and MCP
# on it. Run on VM 100 from /opt/lectern.   deploy/serve.sh 2026.11.2
set -e
id="${1:?snapshot id}"
dir="/data/lectern/snapshots/$id"
[ -f "$dir/manifest.json" ] || { echo "no sealed snapshot at $dir" >&2; exit 1; }
mkdir -p /data/lectern/served
ln -sfn "$dir/public" "/data/lectern/served/$id"
chown -R 65534 "$dir/lexical"
printf 'SNAPSHOT_DIR=%s\nSNAPSHOT_ID=%s\n' "$dir" "$id" > "$(dirname "$0")/.env"
docker compose -f "$(dirname "$0")/compose.yaml" up -d --build --wait
curl -fsS 127.0.0.1:8096/health
