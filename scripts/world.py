"""World deposits view: 10 tracked countries sorted by headline rate or estimated USD result, plus a USD-return / FX break-even calculator.
Math mirrors scripts/world_calc.js (tests/test_calcs.py cross-checks)."""
import json
from datetime import date
from pathlib import Path
from html import escape as e
ROOT = Path(__file__).resolve().parents[1]
import os as _os; from pathlib import Path as _Path; DATA = _Path(_os.environ.get('MB_DATA') or ROOT / 'data')  # tests point MB_DATA at a frozen snapshot

def calc(a, r, t, fx, c, us):
    conv = (1 - c / 100) ** 2; g = 1 + r / 100 * t / 12; u = 1 + us / 100 * t / 12
    end = lambda m: a * conv * g * (1 + m / 100)
    return {'termReturn': (g - 1) * 100, 'end': end(fx), 'gain': end(fx) - a, 'usEnd': a * u, 'beZero': (1 / (conv * g) - 1) * 100, 'beUS': (u / (conv * g) - 1) * 100, 'scen': end}
def yearly_move(start, now, years): return ((start / now) ** (1 / years) - 1) * 100
def est12(r, move): return ((1 + r / 100) * (1 + move / 100) - 1) * 100

def fd(s): return date.fromisoformat(s[:10]).strftime('%b %-d, %Y')
def term_months(term):
    import re
    m = re.search(r'(\d+)\s*(?:–|-)?\s*(\d+)?\s*(mo|month|days?)', term or '')
    if not m: return 12
    n = int(m.group(1)) if m.group(3).startswith('mo') else max(1, round(int(m.group(1)) / 30.4))
    return min(n, 36) if m.group(3).startswith('mo') else n

def dataset():
    yd = json.loads((DATA / 'yields.json').read_text()); fx = json.loads((DATA / 'fx.json').read_text())
    today = fx['fetched']; rows = []
    for c in yd['countries']:
        p = max(c['products'], key=lambda x: x['rate']); now = fx['rates'].get(c['currency'])
        s = c.get('fxStart'); mv = tot = None
        if s and now and c['currency'] != 'USD':
            yrs = (date.fromisoformat(today) - date.fromisoformat(s['date'])).days / 365.25
            tot = (s['rate'] / now - 1) * 100; mv = yearly_move(s['rate'], now, yrs)
        elif c['currency'] == 'USD': mv = tot = 0.0
        lim = c.get('insuranceLimit')
        rows.append({'code': c['code'], 'name': c['name'], 'cur': c['currency'], 'featured': bool(c.get('featured')), 'banks': len(c['products']),
                     'fxd': (fx.get('detail') or {}).get(c['currency']), 'rate': p['rate'], 'bank': p['bank'], 'product': p['product'], 'term': p['term'], 'months': term_months(p['term']),
                     'verified': p.get('verified') or yd['checkedAt'], 'src': p.get('source'), 'fxNow': now, 'fxStart': s, 'fxTotal': tot, 'move': mv,
                     'est': est12(p['rate'], mv) if mv is not None else None, 'ins': c['insurance'],
                     'insLocal': lim, 'insUSD': (lim['amount'] / now if lim and now else None)})
    return {'today': today, 'checkedAt': yd['checkedAt'], 'rows': rows}

def pct(x, sign=False): return ('−' if x < 0 else ('+' if sign and x > 0 else '')) + f'{abs(x):.1f}%'
def row(r):
    ins = (f"{r['insLocal']['amount']:,.0f} {r['insLocal']['currency']}" + (f" (≈${r['insUSD']:,.0f})" if r['cur'] != 'USD' else '')) if r['insLocal'] else '<span class="chip warn">Limit not verified</span>'
    fxs = (f"{pct(r['fxTotal'], True)} since {fd(r['fxStart']['date'])} <small>({pct(r['move'], True)}/yr)</small>" if r['fxStart'] else ('—' if r['cur'] == 'USD' else '<span class="chip warn">No FX history</span>'))
    est = pct(r['est'], True) if r['est'] is not None else '—'
    d = r.get('fxd')
    if d and r['cur'] != 'USD':
        lab = 'official' if d.get('official') else 'market rate, not official'
        fxs += f'<small>Today {r["fxNow"]:,.4g} per $ · <a href="{e(d["url"])}" target="_blank" rel="noopener">{lab}</a>{" · " + fd(d["date"]) if d.get("stale") else ""}</small>'
    src = f' · <a href="{e(r["src"])}" target="_blank" rel="noopener">Source ↗</a>' if r['src'] else ''
    return (f'<tr data-rate="{r["rate"]}" data-est="{r["est"] if r["est"] is not None else -999}"><th scope="row">{e(r["name"])}<small>{r["banks"]} bank{"s" if r["banks"] > 1 else ""} tracked</small></th>'
            f'<td data-l="Top rate we track"><b>{r["rate"]:g}%</b><small>{e(r["bank"])} · {e(r["term"])} · {r["cur"]}</small></td><td data-l="Currency vs $">{fxs}</td><td data-l="Est. 12-month USD result*"><b>{est}</b></td><td data-l="Deposit insurance">{ins}</td>'
            f'<td data-l="Checked"><small> {fd(r["verified"])}{src}</small></td></tr>')

def render(D, us_rate, us_name):
    R = D['rows']; by_rate = sorted(R, key=lambda r: -r['rate'])
    kg = next((r for r in R if r['featured']), None)
    top = by_rate[0]
    feat = ''
    if kg:
        feat = (f'<p class="note"><b>Why {e(kg["name"])} gets extra detail:</b> we track {kg["banks"]} of its banks, more than any other country here. It is not the highest rate on this list. '
                f'The {kg["cur"]} moved {pct(kg["fxTotal"], True)} against the dollar from {fd(kg["fxStart"]["date"])} (<a href="{e(kg["fxStart"]["source"])}" target="_blank" rel="noopener">{e(kg["fxStart"]["label"])}</a>) to {fd(D["today"])}; that says nothing about what it will do next.</p>')
    opts = ''.join(f'<option value="{r["code"]}"{" selected" if r is top else ""}>{e(r["name"])} · {r["rate"]:g}% ({e(r["term"])})</option>' for r in by_rate if r['cur'] != 'USD')
    t0 = top; c0 = calc(10000, t0['rate'], t0['months'], 0, 1, us_rate)
    data = json.dumps({'rows': [{k: r[k] for k in ('code', 'name', 'cur', 'rate', 'months', 'move', 'term')} for r in R], 'us': us_rate}, separators=(',', ':'), ensure_ascii=False)
    js = (ROOT / 'scripts/world_calc.js').read_text() + (ROOT / 'scripts/world_ui.js').read_text()
    table = ''.join(row(r) for r in by_rate)
    return (f'<section class="pagehead" id="world-top"><p class="eyebrow">Banks abroad · {len(R)} tracked countries</p><h2 class="h1like">Higher rates abroad come with <em>currency risk.</em></h2>'
            f'<p class="lead">Banks in some countries pay far more than US savings, but in their own currency. If that currency falls against the dollar, it can wipe out the extra interest, or more.</p>'
            f'<p class="hint">This covers the {len(R)} countries we track, not the whole world. The highest headline rate here is {e(top["name"])} at {top["rate"]:g}% ({e(top["term"])}).</p>{feat}</section>'
            f'<section class="tool" id="world-compare" aria-labelledby="wc-h"><h2 id="wc-h">Compare the {len(R)} countries</h2>'
            f'<div class="seg" role="group" aria-label="Sort by"><button type="button" data-wsort="rate" aria-pressed="true">Headline rate</button><button type="button" data-wsort="est" aria-pressed="false">Estimated USD result</button></div>'
            f'<p class="hint" id="wc-why">Sorted by the bank’s advertised rate in local money. Switch to see a dollar estimate that includes the currency.</p>'
            f'<div class="tw"><table class="wtable"><thead><tr><th scope="col">Country</th><th scope="col">Top rate we track</th><th scope="col">Currency vs $</th><th scope="col">Est. 12-month USD result*</th><th scope="col">Deposit insurance</th><th scope="col">Checked</th></tr></thead><tbody id="wc-body">{table}</tbody></table></div>'
            f'<p class="assume">*A what-if, not a forecast: the headline rate for 12 months (rolled over at the same rate), then converted at a rate that moved the same amount per year as it did since Oct 12, 2023. Before tax and conversion costs. Past currency moves don’t predict future ones, and a steady stretch doesn’t make a currency safe. '
            f'Start rates from each central bank (links per country below); today’s rates from each central bank where we can reach it (otherwise a market rate, labelled in the table), {fd(D["today"])}. Insurance limits in local money with an approximate dollar value at today’s rate; deposit rates checked {fd(D["checkedAt"])}.</p></section>'
            f'<section class="tool" id="world-calc" aria-labelledby="wcalc-h"><p class="eyebrow">Dollar calculator</p><h2 id="wcalc-h">What would you have in dollars?</h2>'
            f'<p class="hint">Change the currency move to see how much a fall can cost. The break-even tells you how far the currency can fall before you’d have done better keeping dollars.</p>'
            f'<form class="fields" id="wc-form" onsubmit="return false"><label>Country<select id="wc-c">{opts}</select></label>'
            f'<label>Amount in dollars<input id="wc-a" inputmode="decimal" value="10,000"></label><label>Local rate, % a year<input id="wc-r" inputmode="decimal" value="{t0["rate"]:g}"></label>'
            f'<label>Term, months<input id="wc-t" inputmode="numeric" value="{t0["months"]}"></label><label>Currency move over the term, %<input id="wc-fx" inputmode="decimal" value="0" aria-describedby="wc-fx-h"></label>'
            f'<label>Conversion cost each way, %<input id="wc-cost" inputmode="decimal" value="1"></label></form><p class="hint" id="wc-fx-h">Negative = the local currency falls against the dollar. The 1% conversion cost is our assumption; ask your bank for its real spread.</p>'
            f'<p class="err" id="wc-err" hidden>Check the numbers: amount above $0, rate 0–100%, term 1–60 months, move above −100%.</p>'
            f'<div class="results" id="wc-out" aria-live="polite">{wout(c0, 10000, t0, us_rate, us_name, 0)}</div>'
            f'<p class="assume"><b>Assumptions.</b> Simple interest paid at the end of the term (no compounding inside the deposit); the rate is annual, so a 3-month deposit earns a quarter of it. Money converted to local currency at the start and back to dollars at the end. US comparison: {e(us_name)} at {us_rate:g}%, held for the same term. Before tax; US taxpayers owe US tax on foreign interest and may need to file FBAR/FATCA reports.</p>'
            f'<script id="wc-data" type="application/json">{data}</script><script>{js}</script></section>')

def money(x): return f'${x:,.0f}'
def wout(c, a, r, us, us_name, fx):
    s = lambda m: c['scen'](m)
    return (f'<p class="pick-line">At {r["rate"]:g}% a year for {r["months"]} month{"s" if r["months"] != 1 else ""}, the deposit earns <b>{c["termReturn"]:.1f}%</b> in {e(r["cur"])} over the whole term (the annual rate is not what you get unless the term is 12 months).</p>'
            f'<div class="scen"><div><b>Currency rises 10%</b><strong>{money(s(10))}</strong><span>{money(s(10) - a)} vs your {money(a)}</span></div>'
            f'<div><b>Currency moves {fx:+g}%</b><strong>{money(s(fx))}</strong><span>{money(s(fx) - a)} vs your {money(a)}</span></div>'
            f'<div><b>Currency falls 10%</b><strong>{money(s(-10))}</strong><span>{money(s(-10) - a)} vs your {money(a)}</span></div>'
            f'<div><b>US savings instead</b><strong>{money(c["usEnd"])}</strong><span>{e(us_name)}, {us:g}%</span></div></div>'
            f'<p class="how"><b>Break-even:</b> {be_txt(c, r["cur"])}</p>')
def be_txt(c, cur):
    z, u = c['beZero'], c['beUS']
    a = f'you lose dollars if the {e(cur)} falls more than <b>{-z:.1f}%</b> over the term' if z < 0 else f'you lose dollars unless the {e(cur)} rises at least <b>{z:.1f}%</b>'
    b = f'you do worse than US savings if it falls more than <b>{-u:.1f}%</b>' if u < 0 else f'you do worse than US savings unless it rises at least <b>{u:.1f}%</b>'
    return a + ', and ' + b + '.'
