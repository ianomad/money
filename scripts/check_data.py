"""Automated checks run at the end of the daily build (compose.py).
Hard failures (exit 1): calculator tests, broken internal links, banned topics, 'best in the world' wording.
Warnings only (site still deploys): stale or missing check dates, expired promos, terms drift, offers needing recheck."""
import json, re, subprocess, sys
from datetime import date, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
D = ROOT / 'docs'
def dj(n): return json.loads((ROOT / 'data' / n).read_text())
def main(today=None):
    today = today or date.today().isoformat(); warn = []; fail = []
    try: _soft(today, warn)
    except Exception as ex: warn.append(f'data checks crashed ({type(ex).__name__}: {ex}); data not checked today')
    _hard(fail)
    for w in warn: print('WARN check:', w)
    for f in fail: print('FAIL check:', f)
    print(f'checks: {len(fail)} failures, {len(warn)} warnings')
    return 1 if fail else 0
def _soft(today, warn):
    import savings
    _, probs = savings.dataset(today); warn += [f'savings: {p}' for p in probs]
    rates = {p['id']: p for p in dj('rates.json')['providers']}
    for pid, p in rates.items():
        v = p.get('verifiedAt')
        if not v: warn.append(f'savings: {pid} has no verifiedAt (shown as "Check date not recorded")')
        elif date.fromisoformat(v) < date.fromisoformat(today) - timedelta(days=30): warn.append(f'savings: {pid} last checked {v} (over 30 days)')
    for pid, t in dj('rate-terms.json')['terms'].items():
        if not isinstance(t, dict): continue
        for path in t.get('paths', []):
            pr = path.get('promo') or {}
            for k in ('openBy', 'until'):
                if pr.get(k) and pr[k] < today: warn.append(f'savings: {pid} promo {k} {pr[k]} has passed; remove or update it')
    cards = dj('cards.json')
    if date.fromisoformat(cards['checkedAt']) < date.fromisoformat(today) - timedelta(days=45): warn.append(f'cards: list last checked {cards["checkedAt"]}')
    for c in cards['cards']:
        if not c.get('url', '').startswith('https://'): warn.append(f'cards: {c["id"]} has no issuer link')
    y = dj('yields.json')
    for c in (y.get('countries') or []):
        if not c.get('fxStart') and c.get('code') != 'US': warn.append(f'world: {c.get("code") or c.get("country")} has no FX start rate')
    ev = dj('events.json')['events']
    if not [x for x in ev if x['date'] >= today]: warn.append('markets: no upcoming events in data/events.json; add the next BLS/Fed dates')
    elif not [x for x in ev if x['date'] >= today and x['date'] <= (date.fromisoformat(today) + timedelta(days=45)).isoformat()]: warn.append('markets: no events in the next 45 days; extend data/events.json')
    for k, s in dj('markets.json')['series'].items():
        if s and date.fromisoformat(s['date']) < date.fromisoformat(today) - timedelta(days=14): warn.append(f'markets: {k} last observation {s["date"]}')
    fx = dj('fx.json')
    for c, v in (fx.get('detail') or {}).items():
        if v.get('stale'): warn.append(f'fx: {c} using last good rate from {v["date"]}')
        if not v.get('official'): warn.append(f'fx: {c} from a market aggregate, not the central bank')
def _hard(fail):
    r = subprocess.run([sys.executable, str(ROOT / 'tests' / 'test_calcs.py')], capture_output=True, text=True)
    if r.returncode: fail.append('calculator tests failed:\n' + (r.stdout + r.stderr)[-1500:])
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'check_links.py')], capture_output=True, text=True)
    if r.returncode: fail.append('broken links:\n' + (r.stdout + r.stderr)[-1500:])
    served = [p for p in D.glob('*.html') if p.name not in {'cards-src.html', 'savings.html', 'world.html', 'daily.html', 'crypto.html', 'economy.html', 'insights.html'}]
    for p in served:
        txt = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', p.read_text(), flags=re.S))
        for pat in (r'\bCash App\b', r'\bAfterpay\b', r'\bSquare\b(?! ?(feet|foot|mile))', r'\$XYZ\b', r'\bBlock,? Inc'):
            if re.search(pat, txt): fail.append(f'{p.name}: banned topic matched {pat}')
        if re.search(r'best (rates? )?in the world', txt, re.I): fail.append(f'{p.name}: "best in the world" wording')
if __name__ == '__main__': sys.exit(main())
