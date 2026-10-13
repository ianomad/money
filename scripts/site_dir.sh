#!/bin/sh
# Build the deploy dir: composed pages only. Builder source pages stay in docs/ but are not served (old URLs redirect via _redirects).
set -e
cd "$(dirname "$0")/.."
python3 scripts/compose.py
rm -rf _site && cp -r docs _site
rm -f _site/savings.html _site/world.html _site/daily.html _site/crypto.html _site/economy.html _site/insights.html
