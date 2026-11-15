#!/bin/sh
# Build the site on a snapshot that the API origin serves, and publish it to Cloudflare Pages.
#   scripts/deploy.sh 2026.11.3
# Needs the Cloudflare global key (~/.config/cloudflare/credentials on the Mini).
set -e
cd "$(dirname "$0")/.."
id="${1:?snapshot id}"
API=https://lectern-api.restorationcommons.org
curl -fsS "$API/data/$id/manifest.json" -o /dev/null 2>/dev/null || curl -fsS "$API/data/$id/docs/jod/06.json" -o /dev/null
rm -rf .snap && scripts/fetch_data.sh "$id"
SAFETYPAGE_PUBLIC_DIR=.snap/public SAFETYPAGE_API=$API SITE_URL=https://lectern.restorationcommons.org \
  PUBLIC_API_BASE=$API npx astro build
. ~/.config/cloudflare/credentials
export CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_API_KEY CLOUDFLARE_EMAIL
npx -y wrangler@4.156.0 pages deploy dist --project-name lectern --branch main --commit-dirty=true
