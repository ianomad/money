"""US savings first-year earnings calculator: data model + math + markup.
Math mirrors scripts/savings_calc.js (tests/test_calcs.py cross-checks both)."""
import json, hashlib, math
from datetime import date
from pathlib import Path
from html import escape as e
ROOT = Path(__file__).resolve().parents[1]
STALE_DAYS = 30
NEEDS = [('new', 'I’m opening a new account', True), ('dd', 'I can set up direct deposit', False),
         ('fee', 'I’d pay a membership fee', False), ('referral', 'I have a referral link', False),
         ('activity', 'I’ll make set deposits every month', False)]
FILTERS = [('bankOnly', 'FDIC-insured bank deposits only'), ('noPromo', 'Skip promo rates (rate that lasts)')]
INS = {'bank': ('FDIC bank deposit', 'ok'), 'conditional': ('Pass-through FDIC, conditions apply', 'warn'),
       'mixed': ('Partly bank-swept, partly not', 'warn'), 'none': ('Not FDIC insured', 'bad')}
NEED_TXT = {'new': 'new customers', 'dd': 'direct deposit', 'fee': 'paid membership', 'referral': 'referral link', 'activity': 'monthly deposits'}

def text_hash(p): return hashlib.sha1((p.get('requirements', '') + '|' + p.get('details', '')).encode()).hexdigest()[:10]

def yearly(spec, b):
    if isinstance(spec, (int, float)): return b * spec / 100
    lo, s = 0, 0.0
    if spec['split']:
        for up, r in spec['tiers']:
            up = math.inf if up is None else up
            if b > lo: s += (min(b, up) - lo) * r / 100
            lo = up
        return None if b > lo else s
    for up, r in spec['tiers']:
        if up is None or b <= up: return b * r / 100
    return None

def months_until(today, until):
    d = (date.fromisoformat(until) - date.fromisoformat(today)).days
    return max(0, min(12, d / 30.4375))

def path(p, b, today):
    fee = p.get('feeYr', 0); then = yearly(p['rate'], b)
    if then is None: return {'err': 'terms above this balance are not published'}
    pm, promo, pr = 0, 0.0, p.get('promo')
    if pr:
        if pr.get('openBy') and pr['openBy'] < today: return {'err': 'offer ended ' + pr['openBy']}
        if pr.get('maxBal') and b > pr['maxBal']: return {'err': 'promo not available above this balance'}
        pm = months_until(today, pr['until']) if pr.get('until') else min(12, pr['months'])
        promo = yearly(pr['rate'], b)
        if promo is None: return {'err': 'terms above this balance are not published'}
    gross = promo * pm / 12 + then * (12 - pm) / 12
    return {'gross': gross, 'net': gross - fee, 'fee': fee, 'promoMonths': pm, 'ongoing': then, 'label': p['label'], 'needs': p['needs']}

def run(D, b, opt, today):
    out, skipped = [], []
    for v in D['providers']:
        T = v['terms']
        if opt.get('bankOnly') and v['fdic'] != 'bank': continue
        if T.get('status') == 'paused': skipped.append({'id': v['id'], 'why': 'not taking new applications'}); continue
        if T.get('minOpen') and b < T['minOpen']: skipped.append({'id': v['id'], 'why': f"needs ${T['minOpen']} to open"}); continue
        best, errs = None, []
        for p in T['paths']:
            if any(not opt.get(n) for n in p['needs']): continue
            if opt.get('noPromo') and p.get('promo'): continue
            r = path(p, b, today)
            if 'err' in r: errs.append(p['label'] + ': ' + r['err']); continue
            if best is None or r['net'] > best['net'] + 1e-9 or (abs(r['net'] - best['net']) < 1e-9 and len(r['needs']) < len(best['needs'])): best = r
        if best is None: skipped.append({'id': v['id'], 'why': errs[0] if errs else 'needs ' + ' or '.join(', '.join(NEED_TXT[n] for n in p['needs']) for p in T['paths'])}); continue
        best.update(id=v['id'], flags=v.get('flags', []), rankable=not v.get('flags')); out.append(best)
    out.sort(key=lambda r: (-r['net'], len(r['needs'])))
    return {'rows': out, 'skipped': skipped}

def spec_rates(spec):
    return [spec] if isinstance(spec, (int, float)) else [r for _, r in spec['tiers']]

def dataset(today=None):
    rj = json.loads((ROOT / 'data/rates.json').read_text()); tj = json.loads((ROOT / 'data/rate-terms.json').read_text())['terms']
    today = today or date.today().isoformat(); provs = []; problems = []
    for p in rj['providers']:
        if p['category'] != 'cash': continue
        T = tj.get(p['id'])
        if not T: problems.append(f"{p['id']}: no structured terms in rate-terms.json"); continue
        flags = []
        va = p.get('verifiedAt')
        if not va: flags.append(['nodate', 'Check date not recorded'])
        elif (date.fromisoformat(today) - date.fromisoformat(va)).days > STALE_DAYS: flags.append(['stale', f'Last checked {va}, may be out of date'])
        if T.get('textHash') and T['textHash'] != text_hash(p):
            flags.append(['drift', 'Terms changed since this math was set up; recheck']); problems.append(f"{p['id']}: rates.json terms text changed; update rate-terms.json")
        rates = {r for pa in T['paths'] for s in [pa['rate']] + ([pa['promo']['rate']] if pa.get('promo') else []) for r in spec_rates(s)}
        for k in ('base', 'boost'):
            if p.get(k) is not None and p[k] not in rates and not (k == 'boost' and T.get('note', '').find(f"{p[k]:.2f}%") >= 0):
                flags.append(['mismatch', f'Calculator terms don’t match the listed {k} rate; recheck']); problems.append(f"{p['id']}: {k} {p[k]} not in rate-terms paths")
        src = p['sources'][0] if p['sources'] else None
        provs.append({'id': p['id'], 'name': p['name'], 'product': p['product'], 'fdic': p['fdic']['status'], 'verifiedAt': va,
                      'effective': p.get('effective'), 'src': src['url'] if src else None, 'srcLabel': src['label'] if src else None,
                      'terms': T, 'flags': flags, 'note': T.get('note')})
    return {'today': today, 'checkedAt': rj['checkedAt'], 'providers': provs}, problems

def fmt_date(s): return date.fromisoformat(s).strftime('%b %-d, %Y') if s else ''
def money(x): return f"${x:,.0f}"

def card(r, P, b, i):
    v = P[r['id']]; ins, cls = INS[v['fdic']]
    pm = r['promoMonths']; how = e(r['label'])
    math_ = f"{money(r['gross'])} interest" + (f" − {money(r['fee'])} fees = <b>{money(r['net'])}</b>" if r['fee'] else '')
    after = f"After the promo ends: about {money(r['ongoing'] - r['fee'])}/yr at today’s rate." if pm else ''
    chips = ''.join(f'<span class="chip warn">{e(t)}</span>' for _, t in v['flags'])
    needs = ', '.join(NEED_TXT[n] for n in r['needs'])
    src = f' · <a href="{e(v["src"])}" target="_blank" rel="noopener">Source ↗</a>' if v['src'] else ''
    chk = f"Checked {fmt_date(v['verifiedAt'])}" if v['verifiedAt'] else 'Check date not recorded'
    return (f'<li class="res{" stale" if v["flags"] else ""}"><div class="rtop"><span class="rk">{i}</span><div><b class="nm">{e(v["name"])}</b>'
            f'<span class="pd">{e(v["product"])}</span></div><div class="amt"><b>{money(r["net"])}</b><span>first year</span></div></div>'
            f'<p class="how">{how}{(" · needs " + needs) if needs else ""}</p><p class="how">{math_} on {money(b)} ≈ {r["net"] / b * 100:.2f}% over 12 months.{(" " + after) if after else ""}</p>'
            f'<p class="meta"><span class="chip {cls}">{ins}</span>{chips}<span>{chk}{src}</span></p></li>')

def render(D, b=10000):
    opt = {k: d for k, _, d in NEEDS}; res = run(D, b, opt, D['today']); P = {v['id']: v for v in D['providers']}
    top = [r for r in res['rows'] if r['rankable']]
    tb = ''.join(f'<label><input type="checkbox" name="{k}"{" checked" if d else ""}> {t}</label>' for k, t, d in NEEDS)
    fb = ''.join(f'<label><input type="checkbox" name="{k}"> {t}</label>' for k, t in FILTERS)
    lead = top[0] if top else None
    pick = (f'<p class="pick-line" id="sv-pick">For {money(b)} with these choices, <b>{e(P[lead["id"]]["name"])}</b> pays the most over a year: about <b>{money(lead["net"])}</b>.</p>' if lead else '<p class="pick-line" id="sv-pick">No account matches these choices.</p>')
    rows = ''.join(card(r, P, b, i + 1) for i, r in enumerate(res['rows']))
    data = json.dumps({'today': D['today'], 'providers': D['providers']}, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    js = (ROOT / 'scripts/savings_calc.js').read_text() + (ROOT / 'scripts/savings_ui.js').read_text()
    return (f'<section class="tool" id="calc" aria-labelledby="calc-h"><p class="eyebrow">Earnings calculator</p><h2 id="calc-h">What would you actually earn?</h2>'
            f'<p class="hint">A first-year estimate for your balance. Short promos count only for the months they last, then the regular rate. Fees come off the top.</p>'
            f'<form class="sv-form" id="sv-form" onsubmit="return false"><label class="bal">Your balance<span class="dollar"><input id="sv-bal" name="bal" inputmode="decimal" autocomplete="off" value="{b:,}" aria-describedby="sv-bal-err"></span></label>'
            f'<p class="err" id="sv-bal-err" hidden>Enter an amount between $1 and $10,000,000.</p>'
            f'<fieldset class="toggles"><legend>What you’re willing to do</legend>{tb}</fieldset><fieldset class="toggles"><legend>Filters</legend>{fb}</fieldset></form>'
            f'<div class="results" id="sv-out" aria-live="polite">{pick}<ol class="res-list collapsed" id="sv-list">{rows}</ol>'
            f'<button class="show-all" id="sv-more" type="button">Show all {len(res["rows"])}</button><p class="note" id="sv-skip">{skipped_txt(res, P)}</p></div>'
            f'<p class="assume"><b>How this is worked out.</b> Balance stays the same for 12 months; rates stay where providers publish them today (they are variable); each rate is APY spread evenly by month; before tax. '
            f'Promos that end on a set date count only until that date. Accounts with an unrecorded or old check date are shown but never put first. Rates checked against provider pages; list checked {fmt_date(D["checkedAt"])}.</p>'
            f'<script id="sv-data" type="application/json">{data}</script><script>{js}</script></section>')

def skipped_txt(res, P):
    if not res['skipped']: return ''
    return 'Not counted: ' + '; '.join(f"{e(P[s['id']]['name'])} ({e(s['why'])})" for s in res['skipped']) + '.'
