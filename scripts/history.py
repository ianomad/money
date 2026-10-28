"""Dated data snapshots (data/history.json) and the real changes between them.
Each daily build stores one snapshot of the hand-checked numbers; "what changed" is
only ever a diff between two stored snapshots. Nothing here is estimated or forecast."""
import json, os, re, subprocess, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / 'data'; HIST = DATA / 'history.json'
KEEP_DAYS = 180
BANNED = re.compile(r'cash ?app|square|afterpay|\bblock\b|\$?xyz', re.I)  # never shown on the site

def snap(rates, yields=None, cards=None, tbills=None):
    s = {'savings': {}, 'world': {}, 'cards': {}}
    for p in rates.get('providers', []):
        if p.get('category') != 'cash' or BANNED.search(p['id'] + ' ' + p['name']): continue
        src = (p.get('sources') or [{}])[0].get('url', '')
        s['savings'][p['id']] = [p['name'], p.get('base'), p.get('boost'), src]
    for c in (yields or {}).get('countries', []):
        if c.get('code') == 'US' or not c.get('products'): continue
        b = max(c['products'], key=lambda x: x['rate'])
        s['world'][c['code']] = [c['name'], b['rate'], b['bank'], b.get('term', ''), b.get('source', '')]
    for c in (cards or {}).get('cards', []):
        if BANNED.search(c['id'] + ' ' + c['name']): continue
        s['cards'][c['id']] = [c['name'], c.get('fee'), c.get('earnText', ''), c.get('url', '')]
    if tbills and tbills.get('terms'):
        s['tbill'] = [tbills['terms'].get('13 Weeks'), tbills.get('date'), tbills.get('source', '')]
    return s

def pct(x): return f'{x:.2f}%' if x is not None else 'none'

def diff(a, b, date):
    """Events between snapshot a (older) and b (newer). Only real field changes."""
    ev = []
    plain = sorted(((v[1], k) for k, v in b['savings'].items() if v[1] is not None and v[2] is None), reverse=True)
    top = plain[0][1] if plain else None
    for k, v in b['savings'].items():
        o = a['savings'].get(k)
        if not a['savings']: break
        name, base, boost, src = v
        if o is None: continue  # newly covered, not a change
        for lab, i in (('rate', 1), ('boosted rate', 2)):
            if o[i] != v[i] and not (o[i] is None and v[i] is None):
                up = (v[i] or 0) > (o[i] or 0)
                ev.append(dict(t='savings', d=up, h=f'{name} {"raised" if up else "cut"} its {lab}: {pct(o[i])} → {pct(v[i])}', a=src))
    if a['world'] and b['world']:
        for k, v in b['world'].items():
            o = a['world'].get(k)
            if o and o[1] != v[1]:
                up = v[1] > o[1]
                ev.append(dict(t='world', d=up, h=f'{v[0]}: top deposit rate {pct(o[1])} → {pct(v[1])} ({v[2]})', a=v[4]))
    if a['cards'] and b['cards']:
        for k, v in b['cards'].items():
            o = a['cards'].get(k)
            if o is None: continue
            if o[1] != v[1]: ev.append(dict(t='cards', h=f'{v[0]} fee changed: ${o[1] or 0}/yr → ${v[1] or 0}/yr', a=v[3]))
            if o[2] != v[2]: ev.append(dict(t='cards', h=f'{v[0]} changed its rewards', w='Now: ' + (v[2] if len(v[2]) < 90 else v[2][:v[2].rfind(' ', 0, 88)] + '…'), a=v[3]))
    if a.get('tbill') and b.get('tbill') and a['tbill'][0] is not None and b['tbill'][0] is not None:
        ch = round(b['tbill'][0] - a['tbill'][0], 2)
        if abs(ch) >= 0.10:
            ev.append(dict(t='tbills', d=ch > 0, h=f'3-month T-bill yield {pct(a["tbill"][0])} → {pct(b["tbill"][0])}', a=b['tbill'][2]))
    for x in ev:
        x['date'] = date
        if x['t'] == 'savings' and top and 'w' not in x: x['w'] = f'Top plain rate now: {b["savings"][top][0]} at {pct(b["savings"][top][1])}'
    return ev

def _load(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return None

def current():
    return snap(_load(DATA/'rates.json') or {}, _load(DATA/'yields.json'), _load(DATA/'cards.json'), _load(DATA/'tbills.json'))

def update(today=None):
    """Store today's snapshot (replacing an earlier one from today). Skipped when MB_DATA points elsewhere (tests)."""
    if os.environ.get('MB_DATA'): return _load(HIST) or {'snapshots': []}
    today = today or datetime.date.today().isoformat()
    h = _load(HIST) or {'snapshots': []}
    s = [x for x in h['snapshots'] if x['date'] != today] + [dict(date=today, **current())]
    s.sort(key=lambda x: x['date'])
    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    h['snapshots'] = [x for x in s if x['date'] >= cut]
    h['note'] = 'One snapshot per build day of the hand-checked data. Changes are diffs between consecutive snapshots.'
    HIST.write_text(json.dumps(h, separators=(',', ':')) + '\n')
    return h

def events(h, days=60):
    s = h.get('snapshots', []); out = []
    for a, b in zip(s, s[1:]): out += diff(a, b, b['date'])
    if s:
        cut = (datetime.date.fromisoformat(s[-1]['date']) - datetime.timedelta(days=days)).isoformat()
        out = [x for x in out if x['date'] >= cut]
    return sorted(out, key=lambda x: x['date'], reverse=True)

def backfill():
    """Rebuild snapshots from the repo's own git history of the data files (last commit per day)."""
    def git(*a): return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True).stdout
    days = {}
    for f in ('rates', 'yields', 'cards', 'tbills'):
        for line in git('log', '--format=%H %ad', '--date=short', '--', f'data/{f}.json').splitlines():
            sha, d = line.split(); days.setdefault(d, {}).setdefault(f, sha)  # newest first → last commit of that day
    last = {}; snaps = []
    for d in sorted(days):
        for f, sha in days[d].items():
            try: last[f] = json.loads(git('show', f'{sha}:data/{f}.json'))
            except Exception: pass
        if 'rates' in last: snaps.append(dict(date=d, **snap(last['rates'], last.get('yields'), last.get('cards'), last.get('tbills'))))
    HIST.write_text(json.dumps({'snapshots': snaps}, separators=(',', ':')) + '\n')
    return update()

if __name__ == '__main__':
    h = backfill(); ev = events(h)
    print(len(h['snapshots']), 'snapshots;', len(ev), 'events')
    for x in ev[:25]: print(x['date'], x['t'], x['h'])
