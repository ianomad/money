"""Content v2: Cards comparison, Markets 'what it means for you', sourcing folds."""
import json, re, html as H
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
    def fee_s(c):
        if not c['fee']: return 'No annual fee'
        if re.search(r'membership|needs', c.get('feeNote') or '', re.I): return f'${c["fee"]:,}/yr membership (not a card fee), counted'
        return f'${c["fee"]:,} annual fee, counted'
    short = {'top': None, 'nofee': 'Suits you if you want nothing to pay or track',
             'travel': 'Suits frequent travellers; travel credits, lounges and perks not counted',
             'bcp': 'Suits big grocery spenders: 6% on the first $6,000/yr; pair with a 2% card', 'sv': 'Suits people who eat out: 3% dining, groceries, streaming',
             'bb': 'Suits renters: earns on rent with no fee; rent not in the numbers'}
    t0 = pick_for('top')
    hero = (f'<article class="fc dark hero" data-pick="top"><p class="fc-k"><span data-who>Best for</span> <span data-tot>${total:,}</span>/month</p>'
            f'<p class="fc-big"><span class="v">${t0["val"]:,}/yr</span></p><h3 class="fc-line">{e(t0["name"])}</h3>'
            f'<p class="fc-catch"><span><span class="fee">{fee_s(t0)}</span> · points at <span data-cpp>{pv*100:g}</span>¢ · no signup bonus</span></p>'
            f'<p class="fc-foot">Terms checked {fdate(d["checkedAt"])}</p>'
            f'<div class="cc-bars" id="cc-bars">' + F.bars([(e(c['name']), c['val'], f'${c["val"]:,}', i == 0) for i, c in enumerate(rk[:5])], 'Top 5 for this spending, $ a year after fees') + '</div>'
            f'<details class="i act" id="cc-adjust"><summary>Adjust spending</summary><div class="dbody">{calc}</div></details>'
            '</article>')
    alts = [F.card(e(w), f'<span class="v">${pick_for(r)["val"]:,}/yr</span>', line=e(short[r]), catch=f'<span class="fee">{fee_s(pick_for(r))}</span>' + (' · perks not counted' if pick_for(r).get('perks') and r != 'travel' else ''),
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
    js = 'const CARDS=' + json.dumps([{k: c.get(k) for k in ('id','name','type','earn','cap','fee','points','bonusTerms','feeNote')} for c in cs]) + ';'
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
    """Markets 'Today in 30 seconds' feed: one card per number (big figure, why it matters, the catch, date + source), sparkline, How it works.
    Every figure comes from data/markets.json, markets-history.json, rates.json, crypto.json, events.json."""
    import datetime as dt
    m = dj('markets.json')['series']; r = dj('rates.json'); cj = dj('crypto.json')
    try: H = dj('markets-history.json')
    except Exception: H = {}
    today_d = dt.date.today(); today = today_d.isoformat()
    top = max((p for p in r['providers'] if p.get('category') == 'cash'), key=lambda p: float(p.get('base') or 0), default=None)
    LOAN = 400000
    pay = lambda rate, amt=LOAN: amt*(rate/1200)/(1-(1+rate/1200)**-360)
    fd = lambda d: dt.date.fromisoformat(d).strftime('%b %-d, %Y')
    sf = lambda d, p: dt.date.fromisoformat(d).strftime('%b %-d' if p == '3m' else '%b %Y')
    stale = lambda k: dt.date.fromisoformat(m[k]['date']) < today_d - dt.timedelta(days=14)
    def chart(k, fmt, n=''):
        pts = H.get(k) or []
        if not pts: return ''
        end = dt.date.fromisoformat(pts[-1][0]); out = ''
        for p, days in (('3m', 92), ('1y', 366), ('5y', 1830)):
            sub = [(d, v) for d, v in pts if dt.date.fromisoformat(d) >= end - dt.timedelta(days=days)]
            if len(sub) < 3: continue
            lo, hi = min(v for _, v in sub), max(v for _, v in sub)
            out += (f'<figure class="spk" data-p="{p}"{"" if p == "1y" else " hidden"}>{spark(sub, label=f"{n}: {fmt(sub[0][1])} on {fd(sub[0][0])}, {fmt(sub[-1][1])} on {fd(sub[-1][0])}, range {fmt(lo)} to {fmt(hi)}")}<figcaption><span>{sf(sub[0][0], p)}</span>'
                    f'<span>{fmt(lo)} – {fmt(hi)}</span><span>{sf(sub[-1][0], p)}</span></figcaption></figure>')
        return out
    def move(k, pct=False, unit=' pts', nd=2, money=False):
        """30-day change pill: arrow + amount, relative to the m1 value in markets.json."""
        s = m[k]; v = (s['value']/s['m1']-1)*100 if pct else s['value']-s['m1']
        amt = f"{abs(v):.1f}%" if pct else (f"${abs(v):.{nd}f}" if money else f"{abs(v):.{nd}f}{unit}")
        d = 'up' if v > 0 else 'down' if v < 0 else 'flat'
        return f'<span class="mv {d}"><span aria-hidden="true">{"▲" if v > 0 else "▼" if v < 0 else "■"}</span> {"Up" if v > 0 else "Down" if v < 0 else "Flat"} {amt} in 30 days</span>', abs((s['value']/s['m1']-1)*100)
    def foot(k, freq, src):
        sid = m[k]['id']; st = stale(k)
        return ((f'<span class="chip warn">May be out of date</span> ' if st else '') + f'{e(freq)} · as of <b>{fd(m[k]["date"])}</b> · {e(src)} via '
                f'<a href="{FRED}{sid}" target="_blank" rel="noopener">FRED {sid} ↗</a>')
    METH = []
    def how(body):
        METH.append(body); return ''
    def card(k, kicker, big, unit, mv, line, catch, ft, viz='', extra='', cls=''):
        return (f'<article class="fc mk {cls}" id="m-{k}" tabindex="-1" aria-label="{e(kicker)}"><p class="fc-k">{kicker}</p><p class="fc-big">{big}{f"<small>{unit}</small>" if unit else ""}</p>{mv}'
                f'<p class="fc-line">{line}</p>{viz}<p class="fc-catch">{catch}</p><p class="fc-foot">{ft}</p>{extra}</article>')
    mo, t10, sp, dl, oil, gas, fed = (m[k] for k in ('mortgage','t10','sp500','dollar','oil','gas','fed'))
    btc = sorted(cj['coins'], key=lambda c: c['market_cap_rank'])[0]
    bt = dt.datetime.fromisoformat(cj['fetchedAt'].replace('Z', '+00:00')).astimezone(dt.timezone(dt.timedelta(hours=-7)))
    yoy = lambda s: (s['value']/s['y1']-1)*100
    cards = {}
    # mortgage: hero card, payment on a typical loan, change-amount tool
    mv, sz = move('mortgage')
    p_now, p_y1 = pay(mo['value']), pay(mo['y1'])
    tool = (f'<div class="mk-loan"><label for="mk-loan-amt">Your loan ($)</label><input id="mk-loan-amt" type="number" inputmode="numeric" min="10000" step="10000" value="{LOAN}" data-loan data-r="{mo["value"]}" data-r1="{mo["y1"]}" aria-describedby="mk-loan-out">'
            f'<p id="mk-loan-out" aria-live="polite" data-loan-out>About <b>${p_now:,.0f}/mo</b> at {mo["value"]:.2f}%, vs ${p_y1:,.0f} at {mo["y1"]:.2f}% a year ago.</p></div>')
    cards['mortgage'] = (card('mortgage', '30-year mortgage rate', f"{mo['value']:.2f}", '%', mv,
        f"About <b>${p_now:,.0f}/mo</b> on a ${LOAN:,} loan. That is ${p_now-p_y1:+,.0f} vs a year ago." .replace('$+', '+$').replace('$-', '−$'),
        f"Principal and interest only, 30 years fixed. Taxes, insurance and PMI add more, and your quote depends on credit and down payment.",
        foot('mortgage', 'Weekly average', 'Freddie Mac'), chart('mortgage', lambda v: f'{v:.2f}%', '30-year mortgage rate'),
        tool + how(f'<p>Freddie Mac’s weekly survey average for a 30-year fixed loan. The monthly figure is the standard amortization formula on ${LOAN:,} over 360 months at {mo["value"]:.2f}%; a year ago the survey read {mo["y1"]:.2f}%.</p>'), 'dark'), sz)
    mv, sz = move('gas', money=True)
    cards['gas'] = (card('gas', 'Gas, US average (regular)', f"${gas['value']:.2f}", '/gal', mv,
        f"A 15-gallon fill-up is about <b>${gas['value']*15:.0f}</b>, vs ${gas['y1']*15:.0f} a year ago.",
        'National average. Your state can be far above or below it.', foot('gas', 'Weekly average', 'EIA'), chart('gas', lambda v: f'${v:.2f}', 'Gas price'),
        how(f'<p>EIA weekly retail price for regular gasoline, all US formulations. Fill-up = 15 gallons × the average price ({fd(gas["date"])}) and × the price a year earlier (${gas["y1"]:.2f}).</p>')), sz)
    mv, sz = move('oil', pct=True)
    cards['oil'] = (card('oil', 'Oil (WTI crude)', f"${oil['value']:.0f}", '/barrel', mv,
        f"<b>{yoy(oil):+.0f}%</b> from a year ago. Pump prices often follow oil weeks later.",
        'Not one for one: refining, taxes and season move gas prices too. Published with a lag.', foot('oil', 'Daily', 'EIA'), chart('oil', lambda v: f'${v:.0f}', 'Oil price'),
        how(f'<p>West Texas Intermediate spot price, ${oil["value"]:.2f} a barrel on {fd(oil["date"])}, vs ${oil["y1"]:.2f} a year earlier.</p>')), sz)
    mv, sz = move('fed')
    cards['fed'] = (card('fed', 'Fed funds rate (effective)', f"{fed['value']:.2f}", '%', mv,
        'Savings rates usually follow it.' + (f" Top no-strings savings rate we track: <b>{top['base']:g}%</b> ({e(top['name'])})." if top else ''),
        'When the Fed cuts, savings rates tend to drop, often with a lag. Many top rates come with conditions.', foot('fed', 'Daily, prior business day', 'Federal Reserve'), chart('fed', lambda v: f'{v:.2f}%', 'Fed funds rate'),
        '<p class="fc-act"><a class="btn" href="/">Compare savings rates</a></p>' + how('<p>Effective federal funds rate from the New York Fed. The savings figure is the highest base rate among the cash accounts on our Savings page, from each provider’s own site.</p>')), sz)
    mv, sz = move('t10')
    cards['t10'] = (card('t10', '10-year Treasury yield', f"{t10['value']:.2f}", '%', mv,
        'Mortgage rates tend to move with this yield, so it hints where they head next.',
        'A signal, not a promise. The gap between the two changes over time.', foot('t10', 'Daily, market close', 'US Treasury'), chart('t10', lambda v: f'{v:.2f}%', '10-year Treasury yield'),
        how(f'<p>Market yield on 10-year US Treasury notes, constant maturity. A year ago it was {t10["y1"]:.2f}%.</p>')), sz)
    mv, sz = move('sp500', pct=True)
    cards['sp500'] = (card('sp500', 'S&P 500 index', f"{sp['value']:,.0f}", '', mv,
        f"<b>{yoy(sp):+.0f}%</b> over a year. Many 401(k) index funds track it.",
        'Excludes dividends. Past moves do not predict the next ones.', foot('sp500', 'Daily close', 'S&P Dow Jones Indices'), chart('sp500', lambda v: f'{v:,.0f}', 'S&P 500'),
        how(f'<p>Index level at the close on {fd(sp["date"])}, vs {sp["y1"]:,.0f} a year earlier. Price only, no dividends.</p>')), sz)
    mv, sz = move('dollar', pct=True)
    cards['dollar'] = (card('dollar', 'US dollar index', f"{dl['value']:.1f}", '', mv,
        f"<b>{yoy(dl):+.1f}%</b> in a year. A stronger dollar makes trips abroad and imports cheaper.",
        'Savings held in other currencies are worth fewer dollars when it rises.', foot('dollar', 'Daily, published weekly', 'Federal Reserve'), chart('dollar', lambda v: f'{v:.0f}', 'US dollar index'),
        '<p class="fc-act"><a class="btn" href="/#world">See currency risk abroad</a></p>' + how('<p>Nominal broad dollar index against major trade partners’ currencies (Jan 2006 = 100).</p>')), sz)
    b24 = btc['price_change_percentage_24h']
    cards['btc'] = (f'<article class="fc mk" id="m-btc" tabindex="-1" aria-label="Bitcoin"><p class="fc-k">Bitcoin</p><p class="fc-big">${btc["current_price"]:,.0f}</p>'
        f'<span class="mv {"up" if b24 > 0 else "down"}"><span aria-hidden="true">{"▲" if b24 > 0 else "▼"}</span> {"Up" if b24 > 0 else "Down"} {abs(b24):.1f}% in 24 hours</span>'
        '<p class="fc-line">The biggest crypto coin. Most others move with it.</p><p class="fc-catch">Prices swing widely, and it is not insured like a bank account.</p>'
        f'<p class="fc-foot">Snapshot, not live · taken <b>{bt:%b %-d, %-I:%M %p} PT</b> · <a href="https://www.coingecko.com/en/coins/bitcoin" target="_blank" rel="noopener">CoinGecko ↗</a></p>'
        '</article>', abs(b24))
    # consumer relevance, not size of move: borrowing, the pump, savings first; a series older than 14 days drops to the end
    PRI = ['mortgage', 'gas', 'fed', 'oil', 'sp500', 't10', 'dollar']
    order = sorted(PRI, key=lambda k: (stale(k), PRI.index(k))) + ['btc']
    short = lambda d: dt.date.fromisoformat(d).strftime('%b %-d')
    def mvtxt(k):
        s_ = m[k]; pct = k in ('oil', 'sp500', 'dollar'); v = (s_['value']/s_['m1']-1)*100 if pct else s_['value']-s_['m1']
        a = '▲' if v > 0 else '▼' if v < 0 else '■'
        return (f"{a} {abs(v):.1f}%" if pct else f"{a} ${abs(v):.2f}" if k == 'gas' else f"{a} {abs(v):.2f} pts"), ('up' if v > 0 else 'down' if v < 0 else 'flat')
    BR = {
     'mortgage': ('Mortgage rate', f"{mo['value']:.2f}%", f"About ${p_now:,.0f}/mo on a ${LOAN:,} loan, {'+' if p_now >= p_y1 else '−'}${abs(p_now-p_y1):,.0f} vs a year ago.", 'Freddie Mac'),
     'gas': ('Gas', f"${gas['value']:.2f}/gal", f"A 15-gallon fill-up is about ${gas['value']*15:.0f}, vs ${gas['y1']*15:.0f} a year ago.", 'EIA'),
     'fed': ('Fed funds rate', f"{fed['value']:.2f}%", 'Savings rates follow it.' + (f" Best no-strings savings we track: {top['base']:g}%." if top else ''), 'Federal Reserve'),
     'oil': ('Oil', f"${oil['value']:.0f}/bbl", f"{yoy(oil):+.0f}% in a year. Pump prices often follow weeks later.", 'EIA'),
     'sp500': ('S&P 500', f"{sp['value']:,.0f}", f"{yoy(sp):+.0f}% in a year, the index many 401(k) funds track.", 'S&P DJI'),
     't10': ('10-year Treasury', f"{t10['value']:.2f}%", 'Mortgage rates tend to follow it.', 'US Treasury'),
     'dollar': ('US dollar', f"{dl['value']:.1f}", 'A stronger dollar makes trips abroad cheaper.', 'Federal Reserve'),
    }
    def brow(n, k):
        lab, val, why, src = BR[k]; mt, d = mvtxt(k)
        return (f'<li><a href="#m-{k}" class="mk-b"><span class="n" aria-hidden="true">{n}</span><span class="t"><span class="h"><b>{e(lab)}</b> <b class="v">{e(val)}</b></span>'
                f'<span class="w">{e(why)}</span><span class="s"><span class="mv {d}">{mt} in 30 days</span> {e(src)} · {short(m[k]["date"])}{" · may be out of date" if stale(k) else ""}</span></span>'
                '<span class="go" aria-hidden="true">›</span></a></li>')
    newest = max(m[k]['date'] for k in m)
    head = ('<section class="fhead mk-head"><p class="fc-k">Markets · today in 30 seconds</p><h1>What matters for <em>your money.</em></h1></section>'
            '<section class="mk-brief" aria-labelledby="mk-brief-h"><h2 id="mk-brief-h" class="sr">Top 3 for your wallet</h2><ol>'
            + ''.join(brow(i + 1, k) for i, k in enumerate(order[:3])) + '</ol>'
            f'<p class="mk-note">Ranked by how much they touch household budgets, not by size of move. Tap one for its chart and catch. Latest data {fd(newest)}.</p></section>')
    seg = ('<div class="seg mseg" role="group" aria-label="Chart period">' + ''.join(f'<button type="button" data-mp="{p}" aria-pressed="{str(p == "1y").lower()}">{l}</button>' for p, l in (('3m', '3M'), ('1y', '1Y'), ('5y', '5Y'))) + '</div>')
    ej = dj('events.json')
    def tm(t):
        h, mi = map(int, t.split(':')); a = dt.datetime(2000, 1, 1, h, mi); b = a - dt.timedelta(hours=3)
        return f"{a:%-I:%M %p} ET · {b:%-I:%M %p} PT"
    up = [x for x in ej['events'] if x['date'] >= today]
    ev = ''.join(f'<li><span class="d"><b>{dt.date.fromisoformat(x["date"]).strftime("%b")}</b>{dt.date.fromisoformat(x["date"]).day}</span><span><strong>{e(x["name"])}</strong> <small>{dt.date.fromisoformat(x["date"]).strftime("%a")} · {tm(x["time"])}</small><br>{e(x["why"])} '
                 f'<a href="{e(ej["calendars"][x["src"]])}" target="_blank" rel="noopener">{e(x["src"])} ↗</a></span></li>' for x in up[:6])
    if not ev: ev = '<li><span>No upcoming dates loaded. See the official calendars below.</span></li>'
    js = ("<script>(()=>{document.querySelectorAll('[data-mp]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-mp]').forEach(x=>x.setAttribute('aria-pressed',x===b));"
          "document.querySelectorAll('figure.spk').forEach(f=>f.hidden=f.dataset.p!==b.dataset.mp)});"
          "const i=document.querySelector('[data-loan]'),o=document.querySelector('[data-loan-out]');if(i&&o){const P=(r,a)=>a*(r/1200)/(1-Math.pow(1+r/1200,-360)),f=n=>'$'+Math.round(n).toLocaleString('en-US');"
          "i.addEventListener('input',()=>{const a=+i.value;if(!(a>0))return;const r=+i.dataset.r,r1=+i.dataset.r1;o.innerHTML='About <b>'+f(P(r,a))+'/mo</b> at '+r.toFixed(2)+'%, vs '+f(P(r1,a))+' at '+r1.toFixed(2)+'% a year ago.'})}"
          "document.querySelectorAll('.mk-b').forEach(a=>a.addEventListener('click',()=>{const t=document.querySelector(a.getAttribute('href'));t&&setTimeout(()=>t.focus({preventScroll:true}),0)}));document.querySelectorAll('[data-open]').forEach(a=>a.addEventListener('click',ev=>{const t=document.getElementById(a.dataset.open),d=t&&t.closest('details');if(t){ev.preventDefault();if(d)d.open=true;t.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}}))})()</script>")
    return (head + f'<div class="mhead"><h2 class="fh">All the numbers</h2><span class="sr">Chart period</span>{seg}</div>'
        + '<div class="feed mk-feed">' + ''.join(cards[k][0] for k in order) + '</div>'
        + '<section class="fc mk-watch" id="watch"><p class="fc-k">Coming up</p><h2 class="fh">Dates that can move these numbers</h2><ul class="ev mk-ev">' + ev + '</ul>'
        + f'<p class="fc-foot">{e(ej["note"])} Checked {fd(ej["checkedAt"])} · <a href="{ej["calendars"]["BLS"]}" target="_blank" rel="noopener">BLS calendar ↗</a> · <a href="{ej["calendars"]["Federal Reserve"]}" target="_blank" rel="noopener">Fed calendar ↗</a></p></section>'
        + '<details class="i big mk-how" id="how"><summary>How these numbers work</summary><div class="dbody">'
        + '<p>Figures refresh every morning from FRED (Federal Reserve Bank of St. Louis), which republishes Freddie Mac, EIA, Treasury, Federal Reserve and S&amp;P data. Most lag by a day or more; weekly series by up to a week. A number older than 14 days is marked “may be out of date”. The 30-day change compares the latest reading with the one about a month earlier. Bitcoin is a CoinGecko snapshot.</p>'
        + ''.join(METH) + '</div></details>' + js)

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
