"""Scan public HYSA lists for US accounts paying more than our current top cash rate and not yet in data/rates.json.
Writes data/yield-candidates.json for human review (never edits rates.json)."""
import json, re, html, urllib.request, datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
rates = json.loads((ROOT/'data/rates.json').read_text())['providers']
cash = [p for p in rates if p['category']=='cash']
top = max((p['boost'] or p['base'] or 0) for p in cash)
floor = sorted((p['boost'] or p['base'] or 0) for p in cash)[-5]  # flag anything that would make our top 5
known = {re.sub(r'[^a-z]', '', p['name'].lower()) for p in rates}
def get(u):
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}); return urllib.request.urlopen(r, timeout=25).read().decode('utf-8', 'ignore')
found = []
try:
    s = get('https://yieldfinder.app/').replace('\\"', '"')
    for n, a in re.findall(r'"account_name":"([^"]{2,60})","current_apy":([\d.]+)', s): found.append((n, float(a), 'yieldfinder.app'))
except Exception as ex: print('yieldfinder failed', ex)
try:
    s = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', get('https://www.doctorofcredit.com/high-interest-savings-to-get/'))))
    for n, a in re.findall(r"([A-Z][\w&.' ]{2,35}?) [–-] (\d\.\d{2})%", s): found.append((n.strip(), float(a), 'doctorofcredit.com'))
except Exception as ex: print('doctorofcredit failed', ex)
cands = {}
for n, a, src in found:
    k = re.sub(r'[^a-z]', '', n.lower())
    if a < floor or a > 12 or any(k.startswith(x) or x.startswith(k) for x in known if x): continue
    if k not in cands or cands[k]['apy'] < a: cands[k] = {'name': n, 'apy': a, 'source': src, 'beatsTop': a > top}
out = {'checkedAt': datetime.date.today().isoformat(), 'ourTop': top, 'threshold': floor,
       'candidates': sorted(cands.values(), key=lambda c: -c['apy'])}
(ROOT/'data/yield-candidates.json').write_text(json.dumps(out, indent=1))
print(f"scan: {len(found)} listings, {len(cands)} candidates >= {floor}% not tracked (top {top}%)")
