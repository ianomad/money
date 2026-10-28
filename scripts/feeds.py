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
                         catch=e(first_clause(p.get('requirements') or 'Conditions apply')),
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
    cc = F.card('Best card for your spending', f'${b["val"]:,}', f'a year from {e(b["name"])}', unit='/yr',
                catch=f'After its ${b["fee"]:,} annual fee · assumes ${sp:,}/mo of spending',
                actions='<div class="fc-act"><a class="btn" href="/cards">Adjust spending →</a></div>')
    mk = dj('markets.json')['series']['mortgage']; ch = mk['value'] - mk['m1']
    mc = F.card('30-year mortgage', f'{mk["value"]:.2f}%', f'{"+" if ch >= 0 else "−"}{abs(ch):.2f} pts in a month', catch=f'Weekly average as of {fd(mk["date"])}',
                actions='<div class="fc-act"><a class="btn" href="/markets">Today in 30 seconds →</a></div>')
    return F.swipe([w, cc, mc], 'More from Money Beast', 'More in <em>30 seconds</em>')
