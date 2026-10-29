"""Overview home + /changes + /record (Oct 29 2026 product brief).
Every figure is read from data/*.json (or the World section markup built from it) at build time. Nothing invented.
General information from public data: Money Beast does not see accounts, know anyone's finances, or send alerts."""
import json, re, datetime
from pathlib import Path
from html import escape as e
import feed as F, savings as S, history as Hs, pages2, facts
ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / 'data'
X_URL = 'https://x.com/intent/follow?screen_name=MoneyBeastHQ'
XSVG = '<svg class="xlogo" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
EXCLUDE = re.compile(r'\b(block|\$?xyz|cash ?app|square|afterpay)\b', re.I)
AMT = 10000
def dj(n): return json.loads((DATA / n).read_text())
def money(x): return f'${x:,.0f}'
def fd(s): d = datetime.date.fromisoformat(s[:10]); return f'{d:%b} {d.day}, {d.year}'
def fds(s): d = datetime.date.fromisoformat(s[:10]); return f'{d:%b} {d.day}'
def nat(): return dj('insights.json')['inputs']['fdicNational']
def first(t, n=110):
    t = re.split(r'(?<=[.;])\s', (t or '').strip())[0].rstrip('.;')
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'

def savings_rows():
    D, _ = S.dataset(); opt = {k: d for k, _, d in S.NEEDS}; res = S.run(D, AMT, opt, D['today'])
    P = {v['id']: v for v in D['providers']}
    return D, P, [r for r in res['rows'] if r['rankable']]

# ---------- featured opportunity ----------
def featured():
    D, P, tops = savings_rows(); t = tops[0]; v = P[t['id']]; n = nat()['savings']
    rate = t['net'] / AMT * 100; yr1 = S._yr1(t)
    cond = S._cond(t, P); ins = S.INS[v['fdic']][0]
    chk = f'checked {fd(v["verifiedAt"])}' if v['verifiedAt'] else 'check date not recorded'
    return (f'<section class="feat" aria-labelledby="feat-k"><p class="fk" id="feat-k">Best savings rate right now</p>'
            f'<p class="fbig">{rate:.2f}%<small>{" first year" if yr1 else " APY"}</small></p>'
            f'<p class="fone"><b>{e(v["name"])}</b> pays {rate / n:.0f}× the US average ({n:.2f}%): about <b>{money(t["net"])}</b> a year on a {money(AMT)} example balance, before tax.</p>'
            f'<p class="fcond">{e(cond)} · {e(ins)} · variable rate · {chk}</p>'
            f'<a class="btn pri fact" href="/rates#calc" data-ev="feat">Compare savings, try your balance <span aria-hidden="true">→</span></a></section>')

# ---------- section previews ----------
def pv(sec, href, big, unit, line, viz, cond, label='Explore'):
    return (f'<a class="pv" href="{href}" data-ev="pv-{sec.lower()}"><p class="pk">{sec}</p><p class="pbig">{big}<small>{unit}</small></p>'
            f'<p class="pline">{line}</p>{viz}<p class="pcond">{cond}</p><span class="pgo">{label} {sec} <span aria-hidden="true">→</span></span></a>')

def previews(world_hero):
    D, P, tops = savings_rows(); n = nat(); rj = dj('rates.json')
    plain = [r for r in tops if not any(x != 'new' for x in r['needs']) and not r['promoMonths'] and not r['fee']]
    four = [r for r in plain if r['net'] / AMT * 100 >= 4.0]
    wf = next((p for p in rj['providers'] if p['id'] == 'wellsfargo'), None)
    items = [(e(P[r['id']]['name']), r['net'] / AMT * 100, f'{r["net"] / AMT * 100:.2f}%', True) for r in plain[1:4]]
    items.append(('US average', n['savings'], f'{n["savings"]:.2f}%', False))
    if wf: items.append((e(wf['name']), float(wf['base']), f'{float(wf["base"]):.2f}%', False))
    p1 = pv('Savings', '/rates', str(len(four)), ' accounts', f'pay 4% or more with no conditions. The average bank pays {n["savings"]:.2f}%' + (f'; {e(wf["name"])} pays {float(wf["base"]):.2f}%.' if wf else '.'),
            F.bars(items, 'APY, no conditions · runners-up after the top pick'), f'FDIC bank deposits · variable rates · list checked {fd(rj["checkedAt"])}')
    d = dj('cards.json'); prof = d['profile']; pvv = d['pointValue']; sp = sum(prof.values())
    for x in d['cards']: x['val'] = pages2.card_value(x, prof, pvv)
    best = max(d['cards'], key=lambda x: x['val']); plain_c = max((x for x in d['cards'] if x['fee'] == 0), key=lambda x: x['val'])
    cost = facts.card_cost(best) if best['fee'] else 'No annual fee'
    p2 = pv('Cards', '/cards', money(best['val']), '/yr', f'from {e(best["name"])} on {money(sp)}/mo of example spending, {money(best["val"] - plain_c["val"])} more than the best no-fee card.',
            F.bars([(e(best['name']), best['val'], money(best['val']), True), (e(plain_c['name']), plain_c['val'], money(plain_c['val']), False)], 'Rewards minus yearly costs, points at 1¢'),
            f'After the {e(cost)} · example spending, editable · checked {fd(d["checkedAt"])}' if best['fee'] else f'Example spending, editable · checked {fd(d["checkedAt"])}')
    mk = dj('markets.json')['series']['mortgage']; dp = S_pay(400000, mk['value']) - S_pay(400000, mk['y1'])
    p3 = pv('Markets', '/markets', f'{mk["value"]:.2f}%', ' 30-yr mortgage', f'{"Up" if mk["value"] >= mk["y1"] else "Down"} from {mk["y1"]:.2f}% a year ago: about {money(abs(dp))} {"more" if dp > 0 else "less"} a month on a $400,000 loan.',
            F.bars([('A year ago', mk['y1'], f'{mk["y1"]:.2f}%', False), ('A month ago', mk['m1'], f'{mk["m1"]:.2f}%', False), ('Now', mk['value'], f'{mk["value"]:.2f}%', True)], 'Weekly average, 30-year fixed'),
            f'National average; quotes vary with credit and down payment · Freddie Mac, week of {fd(mk["date"])}')
    m = re.search(r'<p class="fc-big">([^<:]+): ([\d.]+)%</p><p class="fc-line">([^<]*)</p>', world_hero)
    bars = re.findall(r'<li class="[^"]*"><span class="l">([^<]+)</span><span class="b"><i[^>]*></i></span><b>([^<]+)</b></li>', world_hero.split('</ul>')[0])
    cat = re.search(r'<div class="fc-catch"><span>([^<]+)</span>', world_hero); chk = re.search(r'<p class="fc-foot">([^<]+)</p>', world_hero)
    pick = [b for b in bars if b[0] in ('Currency flat', 'Falls 30%', 'US savings')]
    num = lambda s: float(s.replace('−', '-').replace('%', '').replace('+', ''))
    p4 = pv('World', '/abroad', f'{m.group(2)}%', f' in {e(m.group(1))}', f'{e(m.group(3))}. High local rates beat US savings only if the currency holds up.',
            F.bars([(e(l), num(v), e(v), l == 'Currency flat') for l, v in pick], '12-month return in US dollars · scenarios, not forecasts'),
            (e(cat.group(1)) if cat else 'Paid in local currency: currency risk') + (f' · {e(chk.group(1))}' if chk else '')) if m and pick else ''
    return f'<section class="pvs" aria-labelledby="pvs-h"><h2 class="sh" id="pvs-h">Explore</h2><div class="pv-grid">{p1}{p2}{p3}{p4}</div></section>'

def S_pay(P, rate, n=360):
    r = rate / 1200; return P * r / (1 - (1 + r) ** -n)

# ---------- changes ----------
TOPIC = {'savings': ('Savings', '/rates'), 'world': ('World', '/abroad'), 'cards': ('Cards', '/cards'), 'tbills': ('Markets', '/markets'), 'markets': ('Markets', '/markets')}
MK = [('mortgage', '30-year mortgage rate', 0.05, 'pt'), ('t10', '10-year Treasury yield', 0.10, 'pt'), ('fed', 'Fed funds rate', 0.01, 'pt'),
      ('sp500', 'S&P 500', 2.0, 'pct'), ('oil', 'Oil (WTI)', 3.0, 'pct'), ('gas', 'US gas price', 2.0, 'pct'), ('dollar', 'US dollar index', 1.0, 'pct')]
def market_moves():
    s = dj('markets.json')['series']; out = []
    for k, lab, th, kind in MK:
        v = s.get(k)
        if not v or v.get('w1') in (None, 0): continue
        a, b = v['w1'], v['value']; ch = (b - a) if kind == 'pt' else (b - a) / a * 100
        if abs(ch) < th: continue
        fmt = (lambda x: f'{x:.2f}%') if kind == 'pt' else ((lambda x: f'${x:,.2f}') if k in ('oil', 'gas') else (lambda x: f'{x:,.0f}' if k == 'sp500' else f'{x:.1f}'))
        out.append(dict(t='markets', d=b > a, date=v['date'], h=f'{lab} {"rose" if b > a else "fell"}: {fmt(a)} → {fmt(b)} in a week',
                        w=(f'{ch:+.2f} points' if kind == 'pt' else f'{ch:+.1f}%') + ' vs a week earlier', a=f'https://fred.stlouisfed.org/series/{v["id"]}'))
    return out

def all_changes():
    h = Hs._load(Hs.HIST) or {'snapshots': []}; ev = Hs.events(h, 60)
    D, _ = S.dataset(); P = {v['id']: v for v in D['providers']}
    byname = {v['name']: v for v in P.values()}
    for x in ev:
        if x['t'] == 'savings':
            nm = x['h'].split(' raised')[0].split(' cut')[0]; v = byname.get(nm)
            if v and v.get('req'): x['w'] = first(v['req'])
    ev = [x for x in ev + market_moves() if not EXCLUDE.search(x['h'] + ' ' + x.get('w', ''))]
    return sorted(ev, key=lambda x: x['date'], reverse=True)

def latest3(ev):
    out, seen = [], set()
    for x in ev:  # newest first, one per topic so three different kinds of change show
        k = TOPIC[x['t']][0]
        if k in seen: continue
        seen.add(k); out.append(x)
        if len(out) == 3: return out
    return (out + [x for x in ev if x not in out])[:3]

def chg_li(x, full=False):
    lab, href = TOPIC[x['t']]
    arrow = '' if 'd' not in x else (f'<span class="cd {"up" if x["d"] else "dn"}" aria-hidden="true">{"▲" if x["d"] else "▼"}</span>')
    src = f' · <a href="{e(x["a"])}" target="_blank" rel="noopener">Source ↗</a>' if x.get('a') else ''
    return (f'<li><p class="cm"><time datetime="{x["date"]}">{fds(x["date"])}</time> · <a href="{href}">{lab}</a></p>'
            f'<p class="ch">{arrow}{e(x["h"])}</p>' + (f'<p class="cw">{e(x["w"])}{src}</p>' if x.get('w') else (f'<p class="cw">{src[3:]}</p>' if src else '')) + '</li>')

def changes_home(ev):
    return (f'<section class="chg" aria-labelledby="chg-h"><h2 class="sh" id="chg-h">Latest changes</h2><ol class="clist">{"".join(chg_li(x) for x in latest3(ev))}</ol>'
            f'<a class="more2" href="/changes">See all changes <span aria-hidden="true">→</span></a></section>')

def changes_page(ev):
    days = {}
    for x in ev: days.setdefault(x['date'], []).append(x)
    lst = ''.join(f'<h2 class="cday">{fd(dd)}</h2><ol class="clist">' + ''.join(chg_li(x) for x in xs) + '</ol>' for dd, xs in days.items())
    return (f'<section class="fhead"><h1>What changed</h1><p class="sub">Every real change in the rates, cards and markets this site tracks, newest first.</p></section>'
            f'<p class="hint">{len(ev)} changes in the last 60 days. Savings, cards and world rates are diffs between daily snapshots of the hand-checked data; market moves compare the latest reading with a week earlier (FRED).</p>{lst}')

# ---------- record ----------
def record_page():
    Pj = dj('predictions.json'); C = Pj['calls']; hits = sum(c['result'] == 'hit' for c in C)
    lis = ''.join(f'<li class="{c["result"]}"><span class="pk" aria-label="{"Right" if c["result"] == "hit" else "Wrong"}">{"✓" if c["result"] == "hit" else "✗"}</span>'
                  f'<span class="pc">{e(c["call"])}<small>Called {fd(c["made"])} · actual: {e(c["actual"])}</small></span>'
                  f'<a href="{e(c["grade"])}" target="_blank" rel="noopener" aria-label="Grade post: {e(c["call"])}">Grade ↗</a></li>' for c in reversed(C))
    return (f'<section class="fhead"><h1>Prediction record</h1><p class="sub">Calls posted on X before the result, then graded in public.</p></section>'
            f'<section class="fc proof" id="record"><p class="rec"><b>{hits} right, {len(C) - hits} wrong</b> so far. Misses stay on the record.</p><ol class="pl">{lis}</ol>'
            f'<p class="fc-foot">Updated {fd(Pj["updated"])}. Each grade links to the post on X. Not investment advice.</p></section>' + follow('record'))

def follow(where):
    return (f'<section class="xsec"><p>New opportunities and graded market calls are posted on X first.</p>'
            f'<a class="btn xbtn2" href="{X_URL}" target="_blank" rel="noopener" data-x-follow="{where}">{XSVG}Follow @MoneyBeastHQ on X</a></section>')

HOME_JS = ('<script>(()=>{const K="mb.home.y";try{history.scrollRestoration="manual"}catch(e){}'
           'const nav=(performance.getEntriesByType("navigation")[0]||{}).type,ref=document.referrer,same=ref&&new URL(ref).origin===location.origin&&new URL(ref).pathname!=="/";'
           'const y=+sessionStorage.getItem(K);if(!location.hash&&y&&(nav==="back_forward"||same))requestAnimationFrame(()=>scrollTo(0,y));'
           'const save=()=>sessionStorage.setItem(K,String(scrollY));addEventListener("pagehide",save);document.addEventListener("click",ev=>{if(ev.target.closest("a"))save()});'
           'addEventListener("pageshow",ev=>{if(ev.persisted){const v=+sessionStorage.getItem(K);if(v)scrollTo(0,v)}})})()</script>')

def hash_redirect(world_ids, rates_ids):
    """Old one-page URLs (/#world, /#sv-all, /#calc...) now live on /abroad and /rates."""
    return ('<script>(()=>{const h=location.hash.slice(1);if(!h||document.getElementById(h))return;'
            f'const W={json.dumps(sorted(world_ids))},R={json.dumps(sorted(rates_ids))};'
            'if(h==="world")location.replace("/abroad");else if(W.includes(h))location.replace("/abroad#"+h);else if(R.includes(h))location.replace("/rates#"+h)})()</script>')

def home(world_hero, today):
    ev = all_changes()
    out = (f'<section class="fhead home-h"><h1>Your money could be doing <em>more.</em></h1><p class="sub">Your money agent for better rates, smarter spending, and opportunities worth catching.</p></section>'
           + featured() + previews(world_hero) + changes_home(ev) + follow('home')
           + f'<div class="hm"><p class="trust"><span><b>●</b> Updated {fd(today)}</span><span>General information from public data, checked by hand. Money Beast doesn’t connect to your accounts.</span></p></div>')
    assert not EXCLUDE.search(re.sub(r'<[^>]+>', ' ', out)), 'excluded name on home'
    return out, ev
