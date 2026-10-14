#!/bin/sh
# Daily data refresh: FX, live stablecoin yields, new-account scan, then rebuild pages.
cd "$(dirname "$0")/.." || exit 1
timeout 90 python3 scripts/build_yields.py --fetch || echo "fx failed"
timeout 90 python3 scripts/fetch_defi.py || echo "defi failed"
timeout 90 python3 scripts/scan_new_yields.py || echo "scan failed"
timeout 90 python3 scripts/fetch_markets.py || echo "markets failed"
python3 scripts/build.py   # rebuilds savings + runs compose.py
