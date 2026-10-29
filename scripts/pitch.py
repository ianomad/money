"""Agent home (Oct 29 2026): 'Opportunities for you' feed + public prediction record.
No invented numbers: every figure is computed from data/ files the rest of the site already shows.
These are GENERAL opportunities from public data; Money Beast does not see accounts or send alerts."""
import json, re, datetime
from pathlib import Path
from html import escape as e
import feed as F
ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / 'data'
X_URL = 'https://x.com/MoneyBeastHQ'
EXCLUDE = re.compile(r'\b(block|\$?xyz|cash ?app|square|afterpay)\b', re.I)
def dj(n): return json.loads((DATA / n).read_text())
def money(x): return f'${x:,.0f}'
def fd(s): d = datetime.date.fromisoformat(s); return f'{d:%b} {d.day}, {d.year}'
def neg(s): return s.replace('-', '−')
TAG = '<span class="otag">General · not personal advice</span>'

def pay(P, rate, n=360):
    r = rate / 1200; return P * r / (1 - (1 + r) ** -n)

def nat(): return dj('insights.json')['inputs']['fdicNational']

def opp(title, big, unit, line, viz, why, catch, foot, href, act, open_=''):
    return (f'<article class="fc opp"><p class="fc-k">{title}</p>{TAG}<p class="fc-big">{big}<small>{unit}</small></p><p class="fc-line">{line}</p>{viz}'
            f'<p class="why"><b>Why it matters:</b> {why}</p><div class="fc-catch"><span>{catch}</span></div><p class="fc-foot">{foot}</p>'
            f'<div class="fc-act"><a class="btn pri" href="{href}"{f" data-open={open_}" if open_ else ""}>{act} →</a></div></article>')

def feed(top, world_hero, amount=10000):
    n = nat(); rj = dj('rates.json'); tb = float(top['base'])
    wf = next((p for p in rj['providers'] if p['id'] == 'wellsfargo'), None)
    items = [(e(top['name']), tb, f'{tb:.2f}%', True), ('US average', n['savings'], f'{n["savings"]:.2f}%', False)]
    if wf: items.append((e(wf['name']), float(wf['base']), f'{float(wf["base"]):.2f}%', False))
    c1 = opp('Earn more on cash', f'{tb / n["savings"]:.0f}×', ' the US average', f'{tb:.2f}% at {e(top["name"])}, no conditions, vs {n["savings"]:.2f}% average',
             F.bars(items, 'APY, no conditions'), (f'Big-bank savings like {e(wf["name"])}’s pay {float(wf["base"]):.2f}%: about {money(amount * float(wf["base"]) / 100)} a year on {money(amount)}, vs about {money(amount * tb / 100)} at {e(top["name"])}.' if wf else f'{money(amount)} at the average rate earns about {money(amount * n["savings"] / 100)} a year; at {e(top["name"])}, about {money(amount * tb / 100)}.'),
             'Variable rate, can change anytime. Higher headline rates exist but need direct deposit, promos or memberships.',
             f'FDIC national rate as of {fd(n["asOf"])} · {e(top["name"])} checked {fd(top.get("verifiedAt") or rj["checkedAt"])}', '#sv-all', 'See every account, ranked', 'sv-all')
    import pages2, facts
    d = dj('cards.json'); prof = d['profile']; pv = d['pointValue']; sp = sum(prof.values())
    for x in d['cards']: x['val'] = pages2.card_value(x, prof, pv)
    best = max(d['cards'], key=lambda x: x['val'])
    plain = max((x for x in d['cards'] if x['fee'] == 0), key=lambda x: x['val'])
    same = [x['name'] for x in d['cards'] if x['fee'] == 0 and x['val'] == plain['val']]
    cost = facts.card_cost(best) if best['fee'] else 'No annual fee'
    c2 = opp('Get more from your spending', money(best['val']), '/yr', f'from {e(best["name"])} on {money(sp)}/mo of example spending',
             F.bars([(e(best['name']), best['val'], money(best['val']), True), (e(plain['name']) + (f' +{len(same) - 1} more' if len(same) > 1 else ''), plain['val'], money(plain['val']), False)], 'Rewards minus yearly costs, points at 1¢'),
             f'At this spending it’s worth {money(best["val"] - plain["val"])} a year more than the best no-fee card.' if best['val'] > plain['val'] else 'The right card for your spending adds up every year.',
             (f'After the {e(cost)}. Your spending changes the answer.' if best['fee'] else 'Your spending changes the answer.'),
             f'Example spending, not yours · cards checked {fd(d["checkedAt"])}', '/cards', 'Try your spending')
    mk = dj('markets.json')['series']['mortgage']; dpay = pay(400000, mk['value']) - pay(400000, mk['y1'])
    c3 = opp('See what changed in markets', f'{mk["value"]:.2f}%', ' 30-yr mortgage', f'{"up" if mk["value"] >= mk["y1"] else "down"} from {mk["y1"]:.2f}% a year ago',
             F.bars([('A year ago', mk['y1'], f'{mk["y1"]:.2f}%', False), ('A month ago', mk['m1'], f'{mk["m1"]:.2f}%', False), ('Now', mk['value'], f'{mk["value"]:.2f}%', True)], 'Weekly average, 30-year fixed'),
             f'On a $400,000 loan that’s about {money(abs(dpay))} {"more" if dpay > 0 else "less"} a month than a year ago (principal and interest).',
             'An average: your quote depends on credit, down payment and points.',
             f'Freddie Mac via FRED, week of {fd(mk["date"])}', '/markets', 'See today’s market moves')
    m = re.search(r'<p class="fc-big">([^<:]+): ([\d.]+)%</p><p class="fc-line">([^<]*)</p>', world_hero)
    bars = re.findall(r'<li class="[^"]*"><span class="l">([^<]+)</span><span class="b"><i[^>]*></i></span><b>([^<]+)</b></li>', world_hero.split('</ul>')[0])
    cat = re.search(r'<div class="fc-catch"><span>([^<]+)</span>', world_hero); chk = re.search(r'<p class="fc-foot">([^<]+)</p>', world_hero)
    pick = [b for b in bars if b[0] in ('Currency flat', 'Falls 30%', 'US savings')]
    num = lambda s: float(s.replace('−', '-').replace('%', '').replace('+', ''))
    c4 = opp('Explore opportunities abroad', f'{m.group(2)}%', f' in {e(m.group(1))}', e(m.group(3)),
             F.bars([(e(l), num(v), e(v), l == 'Currency flat') for l, v in pick], 'Return in US dollars over 12 months. Scenarios, not forecasts'),
             'High local rates can beat US savings, but only if the currency holds up.',
             e(cat.group(1)) if cat else 'Paid in local currency: currency risk.',
             e(chk.group(1)) if chk else '', '/#world', 'See currency risk') if m and pick else ''
    out = (f'<section class="opps" id="opportunities" aria-labelledby="opp-h"><h2 class="fh" id="opp-h">Opportunities <em>for you</em></h2>'
           f'<p class="hint">General opportunities from public data, checked by hand. Money Beast doesn’t see your accounts.</p>'
           f'<div class="opp-grid">{c1}{c2}{c3}{c4}</div></section>' + proof())
    assert not EXCLUDE.search(re.sub(r'<[^>]+>', ' ', out)), 'excluded name in agent home'
    return out

def proof():
    P = dj('predictions.json')['calls']; hits = sum(c['result'] == 'hit' for c in P); miss = len(P) - hits
    lis = ''.join(f'<li class="{c["result"]}"><span class="pk" aria-label="{"Right" if c["result"] == "hit" else "Wrong"}">{"✓" if c["result"] == "hit" else "✗"}</span>'
                  f'<span class="pc">{e(c["call"])}<small>Actual: {e(c["actual"])}</small></span>'
                  f'<a href="{e(c["grade"])}" target="_blank" rel="noopener" aria-label="Grade post: {e(c["call"])}">Grade ↗</a></li>' for c in P)
    return (f'<section class="fc proof" id="record" aria-labelledby="rec-h"><p class="fc-k" id="rec-h">Predictions, graded in public</p>'
            f'<p class="rec"><b>{hits} right, {miss} wrong</b> so far. Misses stay on the record.</p>'
            f'<details class="i"><summary>See all {len(P)} calls</summary><ol class="pl">{lis}</ol></details>'
            f'<div class="fc-act"><a class="btn pri" href="{X_URL}" target="_blank" rel="noopener" data-x-follow="record">Follow @MoneyBeastHQ on X ↗</a></div></section>')

def hero_pre(amount=10000):
    return (f'<div class="rng"><label for="sv-rng">Your balance <output id="sv-rng-o" for="sv-rng">{money(amount)}</output></label>'
            f'<input type="range" id="sv-rng" min="1000" max="100000" step="1000" value="{amount}" aria-describedby="sv-earn"></div>'
            f'<p class="ytag">Your estimate · based on your balance</p>')
def hero_extras(top_net_default, top_name, amount=10000):
    """Slider + 'your estimate vs US average' bars injected into the savings hero card (updated live by savings_ui.js)."""
    n = nat()['savings']; avg = amount * n / 100
    return (f'<div id="sv-vs" data-nat="{n}">' + F.bars([(e(top_name), top_net_default, money(top_net_default), True), ('US average', avg, money(avg), False)]) + '</div>')
