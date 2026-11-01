"""Page feeds built from data files (Oct 27 2026). Home extras + teasers. Every number read from data/*.json at build time."""
import json, re
from datetime import date
from pathlib import Path
from html import escape as e
import feed as F
ROOT = Path(__file__).resolve().parents[1]
def dj(n): return json.loads((ROOT / 'data' / n).read_text())
def fd(s): return date.fromisoformat(s[:10]).strftime('%b %-d, %Y')
def m(x): return ('−' if x < 0 else '') + f'${abs(x):,.0f}'
def first_clause(t, n=120):
    t = re.split(r'(?<=[.;])\s', t.strip())[0].rstrip('.;')
    if len(t) <= n: return t
    return t[:n].rsplit(' ', 1)[0] + '…'

def plain_top():
    rj = dj('rates.json')
    cash = [p for p in rj['providers'] if p.get('category') == 'cash' and p.get('base') is not None]
    return sorted([p for p in cash if p.get('boost') is None and p['fdic']['status'] == 'bank' and 'paused' not in (p.get('rateLabel') or '').lower()
                   and 'paused' not in (p.get('requirements') or '').lower()], key=lambda p: -float(p['base']))[0]

def home_extras(amount=10000):
    rj = dj('rates.json'); top = plain_top(); tb = float(top['base'])
    nat = dj('insights.json')['inputs']['fdicNational']
    wf = next((p for p in rj['providers'] if p['id'] == 'wellsfargo'), None)
    items = [(e(top["name"]), tb, f'{tb:.2f}%', True), ('US average', nat['savings'], f'{nat["savings"]:.2f}%', False)]
    if wf: items.append((e(wf["name"]), float(wf['base']), f'{float(wf["base"]):.2f}%', False))
    c1 = F.card('Plain savings vs the US average', f'{tb / nat["savings"]:.0f}×', f'{tb:.2f}% at {e(top["name"])} vs {nat["savings"]:.2f}% average', unit=' the average rate', viz=F.bars(items, 'APY, no conditions'),
                catch=f'{e(top["name"])} has no promo or membership; its rate can change anytime',
                foot=f'US average: <a href="{e(nat["url"])}" target="_blank" rel="noopener">FDIC national rate</a>, as of {fd(nat["asOf"])} · {e(top["name"])} checked {fd(top.get("verifiedAt") or rj["checkedAt"])}')
    boosted = sorted([p for p in rj['providers'] if p.get('category') == 'cash' and p.get('boost') and 'paused' not in (p.get('requirements') or '').lower()],
                     key=lambda p: -float(p['boost']))[:6]
    cs = []
    for p in boosted:
        src = p['sources'][0]['url'] if p.get('sources') else None
        cs.append(F.card(e(p['name']), f'{float(p["boost"]):.2f}%', (f'otherwise {float(p["base"]):.2f}%' if p.get('base') else 'headline rate') + f' · {e(p["fdic"]["label"])}',
                         catch=('<ul class="cl">' + ''.join(f'<li>{e(c)}</li>' for c in p['catches']) + '</ul>') if p.get('catches') else e(p.get('requirements') or 'Conditions apply'),
                         foot=(f'Checked {fd(p["verifiedAt"])}' if p.get('verifiedAt') else 'Check date not recorded')
                         + (f' · <a href="{e(src)}" target="_blank" rel="noopener">Source ↗</a>' if src else '')))
    sw = F.swipe(cs, 'Higher headline rates and their catches', 'Higher rates come with <em>catches</em>')
    return c1, sw

def teasers():
    yd = dj('yields.json'); fx = dj('fx.json')
    best = max(((c, max(c['products'], key=lambda x: x['rate'])) for c in yd['countries'] if c['currency'] != 'USD'), key=lambda t: t[1]['rate'])
    c, p = best; s = c.get('fxStart'); now = fx['rates'].get(c['currency'])
    mv = f'{(s["rate"] / now - 1) * 100:+.0f}%'.replace('-', '−') if s and now else None
    w = F.card(f'Abroad · {e(c["name"])}', f'{p["rate"]:g}%', f'{e(p["bank"])} · {e(p["term"])} · paid in {e(c["currency"])}',
               catch=(f'The {e(c["currency"])} moved {mv} vs the dollar since {fd(s["date"])}' if mv else 'Paid in local currency: currency risk'),
               actions='<div class="fc-act"><a class="btn" href="/#world">See currency risk →</a></div>')
    import pages2
    d = dj('cards.json'); prof = d['profile']; pv = d['pointValue']
    for x in d['cards']: x['val'] = pages2.card_value(x, prof, pv)
    b = max(d['cards'], key=lambda x: x['val']); sp = sum(v for k, v in prof.items() if isinstance(v, (int, float)) and k != 'rent')
    import facts
    cc = F.card(f'Top card at ${sp:,}/mo of spending', f'${b["val"]:,}', f'a year from {e(b["name"])}', unit='/yr',
                catch=f'After the {e(facts.card_cost(b))}' if b.get('fee') else 'No annual fee',
                actions='<div class="fc-act"><a class="btn" href="/cards">Adjust spending →</a></div>')
    mk = dj('markets.json')['series']['mortgage']; ch = mk['value'] - mk['m1']
    mc = F.card('30-year mortgage', f'{mk["value"]:.2f}%', f'{"+" if ch >= 0 else "−"}{abs(ch):.2f} pts in a month', catch=f'Weekly average as of {fd(mk["date"])}',
                actions='<div class="fc-act"><a class="btn" href="/markets">Today in 30 seconds →</a></div>')
    return F.swipe([w, cc, mc], 'More from Money Beast', 'More in <em>30 seconds</em>')

def ibond_card(amount=10000):
    """Series I bond card for /rates (Nov 1 2026). Rate, fixed part, inflation part and buying rules all come from
    data/insights.json -> inputs.ibond, which build_insights.py --fetch re-reads off TreasuryDirect every morning.
    A rule the fetcher could not read is simply left out of the card."""
    b = dj('insights.json')['inputs'].get('ibond') or {}
    if b.get('composite') is None or b.get('fixed') is None: return ''
    rj = dj('rates.json'); top = plain_top(); tb = float(top['base'])
    promo = max((p for p in rj['providers'] if p.get('category') == 'cash' and p.get('boost') and p['fdic']['status'] == 'bank'
                 and 'paused' not in (p.get('requirements') or '').lower()), key=lambda p: float(p['boost']), default=None)
    tbl = dj('insights.json')['inputs'].get('tbill') or {}
    c, fx = b['composite'], b['fixed']
    rel = lambda v: 'more than' if c > v else ('less than' if c < v else 'the same as')
    items = [('I bond', c, f'{c:.2f}%', True)]
    if promo: items.append((e(promo['name']) + ' promo', float(promo['boost']), f'{float(promo["boost"]):.2f}%', False))
    items.append((e(top['name']), tb, f'{tb:.2f}%', False))
    if tbl.get('y26'): items.append(('26-week T-bill', tbl['y26'], f'{tbl["y26"]:.2f}%', False))
    parts = ([(rel(float(promo['boost'])), f'the {float(promo["boost"]):.2f}% {e(promo["name"])} promo')] if promo else []) + [(rel(tb), f'the best plain savings rate ({tb:.2f}% at {e(top["name"])})')]
    cmp = ('Pays ' + parts[0][0] + ' ' + ' and '.join(x for _, x in parts)) if len({r for r, _ in parts}) == 1 else ('Pays ' + ', '.join(f'{r} {x}' for r, x in parts))
    per = b.get('period', ''); pshort = per
    try:
        import datetime as _d
        a_, z_ = per.split(' to '); f_ = lambda s: _d.datetime.strptime(s, '%B %d, %Y').strftime('%b %-d, %Y')
        pshort = f'{f_(a_)} – {f_(z_)}'
    except Exception: pass
    infl = b.get('inflationSemi')
    why = (f'A savings rate can be cut any day. The {fx:.2f}% fixed part of an I bond never changes for its 30-year life, and the rest '
           + (f'(now {infl:.2f}% per 6 months) ' if infl else '') + 'resets every May and November with inflation, so you keep earning above it.')
    rules = []
    if b.get('limit'): rules.append(f'Up to ${b["limit"]:,} a person per year, bought at TreasuryDirect')
    if b.get('minHoldMonths'): rules.append(f'Locked for the first {b["minHoldMonths"]} months')
    pen = b.get('penalty')
    if pen: rules.append(f'Cash out before {pen["years"]} years and you lose the last {pen["months"]} months of interest')
    prev = b.get('prev')
    foot = (f'For bonds bought {e(pshort)}' + (f' · was {prev["composite"]:.2f}% ({prev["fixed"]:.2f}% fixed)' if prev else '')
            + f' · checked {fd(b["checked"])} · <a href="{e(b["url"])}" target="_blank" rel="noopener">TreasuryDirect ↗</a>'
            + (f' · <a href="{e(b["ratesUrl"])}" target="_blank" rel="noopener">How the rate is set ↗</a>' if b.get('ratesUrl') else ''))
    half = amount * c / 200
    return ('<section class="ib" id="ibond" aria-labelledby="ib-h"><h2 class="fh" id="ib-h">Locked in above <em>inflation</em></h2>'
            + card('US Treasury Series I savings bond', f'{c:.2f}%', f'{cmp}. {money_s(amount)} earns about {money_s(half)} in the first 6 months.',
                   unit=' for 6 months', viz=bars(items, 'Rate now, %'),
                   catch=('<ul class="cl">' + ''.join(f'<li>{e(r)}</li>' for r in rules) + '</ul>') if rules else '',
                   foot=foot, attrs=' data-ev="ibond"').replace('<div class="fc-catch">', f'<p class="why"><b>Why it matters:</b> {e(why)}</p><div class="fc-catch">', 1)
            + '</section>')

def money_s(x): return f'${x:,.0f}'
def bars(items, lab): return F.bars(items, lab)
def card(*a, **k): return F.card(*a, **k)
