"""Content v2: Cards comparison, Markets 'what it means for you', sourcing folds."""
import json, html as H
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import os as _os; from pathlib import Path as _Path; DATA = _Path(_os.environ.get('MB_DATA') or ROOT / 'data')  # tests point MB_DATA at a frozen snapshot
def dj(n): return json.loads((DATA/n).read_text())
e = H.escape
CSS = '''<style>
.lead{font-size:17px;color:var(--muted);margin:6px 0 18px}.pagehead{padding:28px 0 4px}.pagehead h1{margin-bottom:8px!important}
.picks{display:grid;gap:10px;margin:18px 0}.pick{border:1px solid var(--line);border-radius:14px;background:#fff;padding:14px 16px;display:grid;grid-template-columns:1fr auto;gap:2px 12px;align-items:baseline}
.pick .who{font:600 12px var(--mono);letter-spacing:.8px;text-transform:uppercase;color:var(--gold);grid-column:1/-1}.pick h3{margin:0;font-size:17px}.pick .v{font:600 20px var(--serif);text-align:right}.pick p{grid-column:1/-1;margin:2px 0 0;font-size:14px;color:var(--muted)}
.ctable{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0}.ctable th{font:600 11px var(--mono);letter-spacing:.8px;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 6px;border-bottom:1px solid var(--line)}
.ctable td{padding:10px 6px;border-bottom:1px solid var(--line);vertical-align:top}.ctable td.n{text-align:right;font:600 16px var(--serif);white-space:nowrap}.ctable small{display:block;color:var(--muted);font-size:12.5px;line-height:1.45}.ctable tr.neg td.n{color:var(--orange)}
.calc{border:1px solid var(--line);border-radius:16px;background:#fff;padding:14px 16px;margin:14px 0}.calc .g{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.calc label{font-size:12px;color:var(--muted);display:flex;flex-direction:column;gap:3px}
.calc input{font:600 16px var(--serif);padding:6px 8px;border:1px solid var(--line);border-radius:9px;background:var(--paper);width:100%;box-sizing:border-box}.calc .tot{margin:10px 0 0;font-size:14px;color:var(--muted)}
.mrow{border-bottom:1px solid var(--line);padding:14px 0;display:grid;grid-template-columns:1fr auto;gap:2px 12px}.mrow h3{margin:0;font-size:16px}.mrow .v{font:600 20px var(--serif);text-align:right}.mrow .ch{grid-column:2;text-align:right;font:12px var(--mono);color:var(--muted)}
.mrow p{grid-column:1/-1;margin:4px 0 0;font-size:15px}.mrow .src{grid-column:1/-1;font:11px var(--mono);color:var(--muted)}
.ev{list-style:none;padding:0;margin:8px 0}.ev li{border-bottom:1px solid var(--line);padding:10px 0;display:grid;grid-template-columns:7.5em 1fr;gap:10px}.ev b{font:600 13px var(--mono);color:var(--gold)}
.srcs{font-size:13px}.srcs td{padding:6px 4px}
@media(max-width:560px){.calc .g{grid-template-columns:1fr 1fr}.ctable .hide{display:none}}
</style>'''

# ---------- cards ----------
CATS = [('dining','Dining'),('groceries','Groceries'),('gas','Gas'),('travel','Travel'),('streaming','Streaming'),('other','Everything else')]
def card_rewards(c, prof, cpp=1.0):
    """Yearly rewards in dollars. prof = monthly spend per category; cpp = cents per point for points cards."""
    tot = 0
    for k, _ in CATS:
        amt = prof.get(k, 0)*12; r = c['earn'].get(k, c['earn']['other'])
        cap = (c.get('cap') or {}).get(k)
        tot += cap*r/100 + (amt-cap)*c['earn']['other']/100 if cap and amt > cap else amt*r/100
    return tot * (cpp if c.get('points') else 1.0)
def card_bonus(c, prof, cpp=1.0):
    """First-year bonus counted only when its spend requirement is known and met by this spending."""
    b = c.get('bonusTerms')
    if not b or 'spend' not in b: return 0
    if sum(prof.values()) * b['months'] < b['spend']: return 0
    return b.get('usd', 0) + b.get('pts', 0) * (cpp if c.get('points') else 1.0) / 100
def card_value(c, prof, pv=0.01, first_year=False):
    cpp = pv*100
    return round(card_rewards(c, prof, cpp) - c['fee'] + (card_bonus(c, prof, cpp) if first_year else 0))
def fdate(s):
    import datetime as _d
    return _d.date.fromisoformat(s).strftime('%b %-d, %Y')
def cards_body():
    d = dj('cards.json'); prof = d['profile']; cs = d['cards']; pv = d['pointValue']
    for c in cs: c['val'] = card_value(c, prof, pv); c['rw'] = round(card_rewards(c, prof))
    rk = sorted(cs, key=lambda c: -c['val'])
    by = {c['id']: c for c in cs}
    rules = [('top', 'Highest value for this spending', 'Yearly rewards minus the annual fee, for the spending below. Changes as you type.'),
             ('nofee', 'Highest with no annual fee', 'The best card here that costs nothing to keep.'),
             ('travel', 'Highest-value travel card', 'Of the travel cards, the one worth the most on rewards alone. Credits and perks are not counted; lounge access only comes with the pricier cards.'),
             ('bcp', 'Big on groceries', 'Our pick: 6% at US supermarkets on the first $6,000 a year. Pair it with a 2% card for everything else.'),
             ('sv', 'Eat out a lot', 'Our pick: 3% on dining, groceries and streaming with no annual fee.'),
             ('bb', 'Pay rent by card', 'Our pick: earns on rent with no transaction fee and no annual fee. Rent is not in the numbers below.')]
    def pick_for(r):
        if r == 'top': return rk[0]
        if r == 'nofee': return max((c for c in cs if c['fee'] == 0), key=lambda c: c['val'])
        if r == 'travel': return max((c for c in cs if c['type'] == 'travel'), key=lambda c: c['val'])
        return by[r]
    import feed as F
    total = sum(prof.values())
    calc = ('<div class="calc" id="card-calc"><b>Monthly spending</b> <span class="tot">(<span id="calc-tot"></span>, no rent)</span><div class="g">'
        + ''.join(f'<label>{l}<input name="{k}" inputmode="decimal" value="{prof[k]}"></label>' for k, l in CATS) + '</div>'
        + f'<div class="g g2"><label>Points value (¢)<input id="cpp" inputmode="decimal" value="{pv*100:g}"></label>'
        + '<label class="tg"><input type="checkbox" id="fy"> Add signup bonus (year 1)</label></div>'
        + '<p class="tot" id="calc-note">Showing an ongoing year: rewards minus the annual fee. Points are counted at 1¢ unless you change it.</p></div>')
    fee_s = lambda c: f'${c["fee"]:,} annual fee, counted' if c['fee'] else 'No annual fee'
    short = {'top': None, 'nofee': 'Costs nothing to keep', 'travel': 'Rewards only; credits and lounges not counted',
             'bcp': '6% groceries on the first $6,000/yr; pair with a 2% card', 'sv': '3% dining, groceries, streaming', 'bb': 'Earns on rent with no fee; rent not in the numbers'}
    t0 = pick_for('top')
    hero = (f'<article class="fc dark hero" data-pick="top"><p class="fc-k">Your best card · <span data-tot>${total:,}</span>/mo spending</p>'
            f'<p class="fc-big"><span class="v">${t0["val"]:,}/yr</span></p><h3 class="fc-line">{e(t0["name"])}</h3>'
            f'<p class="fc-catch"><span><span class="fee">{fee_s(t0)}</span> · points at <span data-cpp>{pv*100:g}</span>¢ · no signup bonus</span></p>'
            f'<p class="fc-foot">Terms checked {fdate(d["checkedAt"])}</p>'
            f'<div class="cc-bars" id="cc-bars">' + F.bars([(e(c['name']), c['val'], f'${c["val"]:,}', i == 0) for i, c in enumerate(rk[:5])], 'Top 5 for this spending, $ a year after fees') + '</div>'
            f'<details class="i act" id="cc-adjust"><summary>Adjust spending</summary><div class="dbody">{calc}</div></details>'
            f'<div class="fc-act"><a class="btn" href="#cc-all" data-open="cc-all">All {len(cs)} cards ranked</a></div></article>')
    alts = [F.card(e(w), f'<span class="v">${pick_for(r)["val"]:,}/yr</span>', '', catch=f'<span class="fee">{fee_s(pick_for(r))}</span> · {e(short[r])}',
                   attrs=f' data-pick="{r}"').replace('<p class="fc-big">', f'<h3 class="fc-line nm">{e(pick_for(r)["name"])}</h3><p class="fc-big">', 1)
            for r, w, t in rules if r != 'top']
    how_picks = ''.join(f'<p><b>{e(w)}:</b> {e(t)}</p>' for r, w, t in rules)
    def bon_txt(c):
        b = c.get('bonusTerms')
        if not c.get('bonus'): return ''
        if not b or 'spend' not in b: return f'<small>Bonus: {e(c["bonus"])} (not counted: terms not modelled)</small>'
        return f'<small>Bonus: {e(c["bonus"])}</small>'
    def chk(c):
        v = c.get('verifiedAt')
        return f'<small class="chk">{"Re-checked" if v else "List checked"} {fdate(v or d["checkedAt"])} · <a href="{e(c["url"])}" rel="nofollow noopener">Issuer page ↗</a></small>'
    rows = ''.join(f'<tr class="{"neg" if c["val"]<0 else ""}" data-id="{c["id"]}"><td><b>{e(c["name"])}</b>{" <span class=\"chip\">points</span>" if c.get("points") else ""}<small>{e(c["earnText"])}</small>'
        + f'<small class="math" data-m>Rewards ${c["rw"]:,} − fee ${c["fee"]:,} = ${c["val"]:,}/yr</small>'
        + '<details class="i"><summary>Details</summary><div class="dbody">' + bon_txt(c) + (f'<small>Perks (not counted): {e(c["perks"])}</small>' if c.get('perks') else '') + (f'<small>{e(c["note"])}</small>' if c.get('note') else '') + chk(c) + '</div></details>'
        + f'</td><td class="hide">{"$0" if not c["fee"] else "$"+str(c["fee"])}<small>{e(c.get("feeNote",""))}</small></td><td class="n" data-v>${c["val"]:,}</td></tr>' for c in rk)
    js = 'const CARDS=' + json.dumps([{k: c.get(k) for k in ('id','name','type','earn','cap','fee','points','bonusTerms')} for c in cs]) + ';'
    js += (ROOT/'scripts'/'cards_calc.js').read_text() + (ROOT/'scripts'/'cards_ui.js').read_text()
    return (CSS + F.head('Which card pays you <em>the most?</em>', 'Yearly value after fees, for your spending.')
        + f'<div class="feed">{hero}</div>' + F.swipe(alts, 'Alternatives for different spending', 'If you spend <em>differently</em>')
        + f'<details class="i big" id="cc-all"><summary>All {len(cs)} cards, ranked</summary><div class="dbody">'
        f'<table class="ctable cards-t"><thead><tr><th>Card · how it earns</th><th class="hide">Fee</th><th style="text-align:right">Value/yr</th></tr></thead><tbody>{rows}</tbody></table></div></details>'
        f'<details class="i big"><summary>How it works</summary><div class="dbody"><p>{e(d["assumption"])}</p><p>Default spending: ' + ', '.join(f'{l.lower()} ${prof[k]}' for k, l in CATS)
        + '. An ongoing year leaves signup bonuses out, since they pay once. Turn on the first-year switch to add a bonus, counted only if your spending over its window meets the requirement. Caps are applied (Amex Gold, Blue Cash Preferred and Everyday, Altitude Go). Rotating 5% categories (Discover) and portal-only rates (5x Chase Travel and similar) are not counted. Rent cards are compared on everyday spend.</p>'
        + f'<p>Card terms were checked against issuer pages on {fdate(d["checkedAt"])}; cards marked "Re-checked" were checked again later. Terms change often, so confirm on the issuer page before you apply.</p>{how_picks}</div></details>'
        + f'<script>{js}</script>' + F.JS)

# ---------- markets ----------
def fmt_ch(v, prev, unit, nd=2):
    d = v - prev
    return f"{'+' if d>=0 else '−'}{abs(d):.{nd}f}{unit}"
FRED = 'https://fred.stlouisfed.org/series/'
def spark(pts, w=320, h=64, label='chart'):
    """Inline SVG line for [(date, value)], with min/max labels. Returns '' if too few points."""
    if len(pts) < 3: return ''
    if len(pts) > 140: st = len(pts) / 140; pts = [pts[int(i * st)] for i in range(140)] + [pts[-1]]
    vs = [v for _, v in pts]; lo, hi = min(vs), max(vs); rg = (hi - lo) or 1
    xy = ' '.join(f'{i * w / (len(pts) - 1):.1f},{4 + (hi - v) / rg * (h - 8):.1f}' for i, (_, v) in enumerate(pts))
    return f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" role="img" aria-label="{e(label)}"><polyline fill="none" stroke="currentColor" stroke-width="1.6" vector-effect="non-scaling-stroke" points="{xy}"/></svg>'
def markets_top():
    import datetime as dt
    m = dj('markets.json')['series']; r = dj('rates.json'); cj = dj('crypto.json')
    try: H = dj('markets-history.json')
    except Exception: H = {}
    top = max((p for p in r['providers'] if p.get('category') == 'cash'), key=lambda p: float(p.get('base') or 0), default=None)
    pay = lambda rate: 400000*(rate/1200)/(1-(1+rate/1200)**-360)
    fd = lambda d: dt.date.fromisoformat(d).strftime('%b %-d, %Y')
    def chg(k, unit, pct=False, nd=2):
        s = m[k]; d0 = (dt.date.fromisoformat(s['date']) - dt.timedelta(days=30)).strftime('%b %-d')
        v = (s['value']/s['m1']-1)*100 if pct else s['value']-s['m1']
        return f"{'+' if v >= 0 else '−'}{abs(v):.{1 if pct else nd}f}{'%' if pct else unit} since {d0}"
    sf = lambda d, p: dt.date.fromisoformat(d).strftime('%b %-d' if p == '3m' else '%b %Y')
    def chart(k, fmt, n=''):
        pts = H.get(k) or []
        if not pts: return '<p class="nochart">No history available.</p>'
        end = dt.date.fromisoformat(pts[-1][0]); out = ''
        for p, days in (('3m', 92), ('1y', 366), ('5y', 1830)):
            sub = [(d, v) for d, v in pts if dt.date.fromisoformat(d) >= end - dt.timedelta(days=days)]
            if len(sub) < 3: continue
            lo, hi = min(v for _, v in sub), max(v for _, v in sub)
            out += (f'<figure class="spk" data-p="{p}"{"" if p == "1y" else " hidden"}>{spark(sub, label=f'{n}: {fmt(sub[0][1])} on {fd(sub[0][0])}, {fmt(sub[-1][1])} on {fd(sub[-1][0])}, range {fmt(lo)} to {fmt(hi)}')}<figcaption><span>{sf(sub[0][0], p)}</span>'
                    f'<span>{fmt(lo)} – {fmt(hi)}</span><span>{sf(sub[-1][0], p)}</span></figcaption></figure>')
        return out
    mo, t10, sp, dl, oil, gas, fed = (m[k] for k in ('mortgage','t10','sp500','dollar','oil','gas','fed'))
    btc = sorted(cj['coins'], key=lambda c: c['market_cap_rank'])[0]
    bt = dt.datetime.fromisoformat(cj['fetchedAt'].replace('Z', '+00:00')).astimezone(dt.timezone(dt.timedelta(hours=-7)))
    P = lambda nd, u='%': (lambda v: f'{v:.{nd}f}{u}')
    items = [
     ('mortgage', '30-year mortgage rate', f"{mo['value']:.2f}%", 'Weekly average', chg('mortgage', ' pts'),
      f"On a $400,000 loan that is about ${pay(mo['value']):,.0f}/mo in principal and interest, vs ${pay(mo['y1']):,.0f} at last year's {mo['y1']:.2f}%.", 'Freddie Mac survey', P(2)),
     ('t10', '10-year Treasury yield', f"{t10['value']:.2f}%", 'Daily, market close', chg('t10', ' pts'),
      'Mortgage rates tend to move with this yield, so it is an early sign of where they are heading.', 'US Treasury', P(2)),
     ('fed', 'Fed funds rate (effective)', f"{fed['value']:.2f}%", 'Daily, prior business day', chg('fed', ' pts'),
      'Online savings rates usually follow it, often with a lag.' + (f" The top no-strings savings rate we track is {top['base']:g}% ({top['name']})." if top else ''), 'Federal Reserve', P(2)),
     ('gas', 'Gas, US average (regular)', f"${gas['value']:.2f}/gal", 'Weekly average', chg('gas', '', nd=2).replace('+', '+$', 1).replace('−', '−$', 1),
      f"A 15-gallon fill-up is about ${gas['value']*15:.0f}, vs ${gas['y1']*15:.0f} a year ago.", 'EIA', lambda v: f'${v:.2f}'),
     ('oil', 'Oil (WTI crude)', f"${oil['value']:.2f}/barrel", 'Daily, published with a lag', chg('oil', '', pct=True),
      f"{(oil['value']/oil['y1']-1)*100:+.0f}% from a year ago. Pump prices often follow oil, usually weeks later and not one for one.", 'EIA', lambda v: f'${v:.0f}'),
     ('sp500', 'S&P 500 index', f"{sp['value']:,.0f}", 'Daily close', chg('sp500', '', pct=True),
      f"{(sp['value']/sp['y1']-1)*100:+.0f}% over a year, not counting dividends. Many 401(k) index funds track it.", 'S&P Dow Jones Indices', lambda v: f'{v:,.0f}'),
     ('dollar', 'US dollar index (vs. trade partners)', f"{dl['value']:.1f}", 'Daily, published weekly', chg('dollar', '', pct=True),
      'A stronger dollar makes trips abroad and imports cheaper, and savings held in other currencies worth fewer dollars.', 'Federal Reserve', lambda v: f'{v:.0f}'),
    ]
    rows = ''
    for k, n, v, freq, c, t, s, fmt in items:
        sid = m[k]['id']
        rows += (f'<article class="mrow"><h3>{e(n)}</h3><span class="v">{e(v)}</span><span class="ch">{e(c)}</span>'
                 f'<p>{e(t)}</p>{chart(k, fmt, n)}<p class="src"><span class="chip">{e(freq)}</span> As of {fd(m[k]["date"])} · {e(s)} via <a href="{FRED}{sid}" target="_blank" rel="noopener">FRED {sid} ↗</a></p></article>')
    rows += (f'<article class="mrow"><h3>Bitcoin</h3><span class="v">${btc["current_price"]:,.0f}</span><span class="ch">{btc["price_change_percentage_24h"]:+.1f}% in 24h</span>'
             '<p>Prices swing widely, and it is not insured like a bank account.</p>'
             f'<p class="src"><span class="chip">Snapshot, not live</span> Taken {bt:%b %-d, %-I:%M %p} PT · <a href="https://www.coingecko.com/en/coins/bitcoin" target="_blank" rel="noopener">CoinGecko ↗</a></p></article>')
    ej = dj('events.json'); today = dt.date.today().isoformat()
    def tm(t):
        h, mi = map(int, t.split(':')); a = dt.datetime(2000, 1, 1, h, mi); b = a - dt.timedelta(hours=3)
        return f"{a:%-I:%M %p} ET ({b:%-I:%M %p} PT)"
    ev = ''.join(f'<li><b>{dt.date.fromisoformat(x["date"]).strftime("%a %b %-d")}</b><span><strong>{e(x["name"])}</strong> <small>{tm(x["time"])}</small><br>{e(x["why"])} '
                 f'<a href="{e(ej["calendars"][x["src"]])}" target="_blank" rel="noopener">{e(x["src"])} calendar ↗</a></span></li>' for x in ej['events'] if x['date'] >= today)
    if not ev: ev = '<li><span>No upcoming dates loaded. See the official calendars below.</span></li>'
    seg = ('<div class="seg mseg" role="group" aria-label="Chart period">' + ''.join(f'<button type="button" data-mp="{p}" aria-pressed="{str(p == "1y").lower()}">{l}</button>' for p, l in (('3m', '3 months'), ('1y', '1 year'), ('5y', '5 years'))) + '</div>')
    js = ("<script>document.querySelectorAll('[data-mp]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-mp]').forEach(x=>x.setAttribute('aria-pressed',x===b));"
          "document.querySelectorAll('figure.spk').forEach(f=>f.hidden=f.dataset.p!==b.dataset.mp)})</script>")
    return (CSS + '<section class="pagehead"><p class="eyebrow">MARKETS · WHAT IT MEANS FOR YOU</p><h1>The numbers that hit <em>your wallet.</em></h1>'
        '<p class="lead">Loan rates, savings rates, gas and stocks, each with its date, source and how often it updates. Refreshed every morning; most figures lag by a day or more.</p></section>'
        + f'<div class="mhead"><span>Charts:</span>{seg}</div>' + rows
        + '<section class="digest" id="watch"><p class="eyebrow">WHAT TO WATCH</p><h2>Coming up</h2><ul class="ev">' + ev + '</ul>'
        + f'<p class="fine">{e(ej["note"])} Checked {fd(ej["checkedAt"])}. Official calendars: <a href="{ej["calendars"]["BLS"]}" target="_blank" rel="noopener">BLS ↗</a> · <a href="{ej["calendars"]["Federal Reserve"]}" target="_blank" rel="noopener">Federal Reserve ↗</a></p></section>' + js)

# ---------- sourcing fold ----------
def sources_fold(kind):
    s = dj('sources.json'); rows = [x for x in s['sources'] if (x['kind'] == 'card') == (kind == 'cards') or kind == 'rates' and x['kind'] == 'savings']
    if kind == 'cards':
        d = dj('cards.json'); rows = [{'name': c['issuer'], 'product': c['name'], 'url': c['url'], 'status': 'read', 'checked': d['checkedAt']} for c in d['cards']]
    def st(x): return ('Checked' if x['status'] == 'read' else 'Not listed') + (': ' + x['note'] if x.get('note') else ('' if x['status'] == 'read' else ': could not verify'))
    t = ''.join(f'<tr><td><a href="{e(x["url"])}" rel="nofollow noopener">{e(x["name"])}</a></td><td>{e(x["product"])}</td><td>{e(st(x))}</td><td>{e(x["checked"])}</td></tr>' for x in rows)
    intro = ('Every rate and card term comes from the institution’s own website, not from comparison sites. Each row shows when we last checked. '
             'We cover the biggest US banks by assets, the major fintech apps, and newer startups. Nobody pays to be listed or ranked higher.')
    return (f'<details class="tuck" id="sourcing"><summary>How we source this</summary><p>{intro}</p>'
            f'<table class="ctable srcs"><thead><tr><th>Institution</th><th>Product</th><th>Status</th><th>Checked</th></tr></thead><tbody>{t}</tbody></table></details>')
