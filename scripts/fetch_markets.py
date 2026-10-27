"""Pull everyday-money market numbers from FRED (free CSV, no key) + crypto.json -> data/markets.json"""
import json, csv, io, urllib.request, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
S = {'mortgage':'MORTGAGE30US','t10':'DGS10','sp500':'SP500','dollar':'DTWEXBGS','oil':'DCOILWTICO','gas':'GASREGW','fed':'DFF'}
start = (datetime.date.today()-datetime.timedelta(days=5*366+10)).isoformat()  # 5 years: also feeds the charts
out = {'checkedAt': datetime.date.today().isoformat(), 'series': {}}
old = json.loads((ROOT/'data/markets.json').read_text()) if (ROOT/'data/markets.json').exists() else {'series':{}}
HP = ROOT/'data/markets-history.json'
hist_old = json.loads(HP.read_text()) if HP.exists() else {}
hist = {}
for k, sid in S.items():
    try:
        t = urllib.request.urlopen(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}', timeout=30).read().decode()
        rows = [(r[0], float(r[1])) for r in list(csv.reader(io.StringIO(t)))[1:] if r[1] not in ('.', '')]
        d, v = rows[-1]
        def ago(days):
            tgt = (datetime.date.fromisoformat(d)-datetime.timedelta(days=days)).isoformat()
            return next((x for x in reversed(rows) if x[0] <= tgt), rows[0])[1]
        out['series'][k] = {'id': sid, 'date': d, 'value': v, 'w1': ago(7), 'm1': ago(30), 'y1': ago(365)}
        wk = {}  # one point per ISO week (last observation) keeps the file small; the last 100 days stay daily for the 3-month view
        cut = (datetime.date.fromisoformat(d)-datetime.timedelta(days=100)).isoformat()
        for dt, val in rows:
            key = dt if dt >= cut else datetime.date.fromisoformat(dt).isocalendar()[:2]
            wk[str(key)] = (dt, val)
        hist[k] = sorted(wk.values())
    except Exception as e:
        print('fail', k, e); out['series'][k] = old['series'].get(k); hist[k] = hist_old.get(k, [])
(ROOT/'data/markets.json').write_text(json.dumps(out, indent=1)); HP.write_text(json.dumps(hist, separators=(',', ':'))); print(out['series'])
