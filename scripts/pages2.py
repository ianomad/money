"""Content v2: Cards comparison, Markets 'what it means for you', sourcing folds."""
import json, html as H
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def dj(n): return json.loads((ROOT/'data'/n).read_text())
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
    ph = ''.join(f'<div class="pick" data-pick="{r}"><span class="who">{e(w)}</span><h3>{e(pick_for(r)["name"])}</h3><span class="v">${pick_for(r)["val"]:,}/yr</span><p>{e(t)}</p></div>' for r, w, t in rules)
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
        + bon_txt(c) + (f'<small>Perks (not counted): {e(c["perks"])}</small>' if c.get('perks') else '') + (f'<small>{e(c["note"])}</small>' if c.get('note') else '') + chk(c)
        + f'</td><td class="hide">{"$0" if not c["fee"] else "$"+str(c["fee"])}<small>{e(c.get("feeNote",""))}</small></td><td class="n" data-v>${c["val"]:,}</td></tr>' for c in rk)
    js = 'const CARDS=' + json.dumps([{k: c.get(k) for k in ('id','name','type','earn','cap','fee','points','bonusTerms')} for c in cs]) + ';'
    js += (ROOT/'scripts'/'cards_calc.js').read_text() + (ROOT/'scripts'/'cards_ui.js').read_text()
    calc = ('<div class="calc" id="card-calc"><b>Your monthly spending</b> <span class="tot">(total <span id="calc-tot"></span>, not counting rent)</span><div class="g">'
        + ''.join(f'<label>{l}<input name="{k}" inputmode="decimal" value="{prof[k]}"></label>' for k, l in CATS) + '</div>'
        + f'<div class="g g2"><label>Points worth (¢ each)<input id="cpp" inputmode="decimal" value="{pv*100:g}"></label>'
        + '<label class="tg"><input type="checkbox" id="fy"> Include first-year signup bonus</label></div>'
        + '<p class="tot" id="calc-note">Showing an ongoing year: rewards minus the annual fee. Points are counted at 1¢ unless you change it.</p></div>')
    total = sum(prof.values())
    return (CSS + '<section class="pagehead"><p class="eyebrow">CARDS · COMPARED BY THE MATH</p><h1>Which card pays you <em>the most?</em></h1>'
        f'<p class="lead">For someone spending ${total:,} a month, here is what each card is worth in a year after its fee. Change the numbers to match your spending; every row shows its math.</p></section>'
        f'{calc}<h2 class="sec-h">Picks</h2><div class="picks">{ph}</div>'
        f'<h2 class="sec-h">All {len(cs)} cards, ranked</h2>'
        f'<table class="ctable cards-t"><thead><tr><th>Card · how it earns</th><th class="hide">Fee</th><th style="text-align:right">Value/yr</th></tr></thead><tbody>{rows}</tbody></table>'
        f'<details class="tuck" open><summary>How we count the value</summary><p>{e(d["assumption"])}</p><p>Default spending: ' + ', '.join(f'{l.lower()} ${prof[k]}' for k, l in CATS)
        + '. An ongoing year leaves signup bonuses out, since they pay once. Turn on the first-year switch to add a bonus, counted only if your spending over its window meets the requirement. Caps are applied (Amex Gold, Blue Cash Preferred and Everyday, Altitude Go). Rotating 5% categories (Discover) and portal-only rates (5x Chase Travel and similar) are not counted. Rent cards are compared on everyday spend.</p>'
        + f'<p>Card terms were checked against issuer pages on {fdate(d["checkedAt"])}; cards marked "Re-checked" were checked again later. Terms change often, so confirm on the issuer page before you apply.</p></details>'
        + f'<script>{js}</script>')

# ---------- markets ----------
def fmt_ch(v, prev, unit, nd=2):
    d = v - prev
    return f"{'+' if d>=0 else '−'}{abs(d):.{nd}f}{unit}"
def markets_top():
    m = dj('markets.json')['series']; r = dj('rates.json'); cj = dj('crypto.json')
    top = max((p for p in r['providers'] if p.get('category') == 'cash'), key=lambda p: float(p.get('base') or 0), default=None)
    def tr(k, a='m1'): s = m[k]; return s['value'] - s[a]
    mo, t10, sp, dl, oil, gas, fed = (m[k] for k in ('mortgage','t10','sp500','dollar','oil','gas','fed'))
    pay = lambda rate: 400000*(rate/1200)/(1-(1+rate/1200)**-360)
    btc = sorted(cj['coins'], key=lambda c: c['market_cap_rank'])[0]
    up = lambda k: tr(k) > 0
    items = [
     ('30-year mortgage rate', f"{mo['value']:.2f}%", f"{fmt_ch(mo['value'],mo['m1'],' pts')} in a month", f"On a $400,000 loan that's about ${pay(mo['value']):,.0f}/mo, vs ${pay(mo['y1']):,.0f} a year ago at {mo['y1']:.2f}%." + (" Rising rates make buying or refinancing pricier." if up('mortgage') else " Falling rates: worth checking a refinance."), f"Freddie Mac weekly survey · {mo['date']}"),
     ('10-year Treasury yield', f"{t10['value']:.2f}%", f"{fmt_ch(t10['value'],t10['m1'],' pts')} in a month", "This drives mortgage and car-loan rates. " + ("Higher means borrowing costs more, but bonds and CDs pay more." if up('t10') else "Lower means cheaper loans ahead and lower CD rates."), f"US Treasury via FRED · {t10['date']}"),
     ('Fed funds rate', f"{fed['value']:.2f}%", f"{fmt_ch(fed['value'],fed['m1'],' pts')} in a month", "Savings accounts track this closely. " + (f"The best no-strings savings rate we track is {top['base']:g}% ({top['name']}); see Rates." if top else ''), f"Federal Reserve via FRED · {fed['date']}"),
     ('Gas, US average', f"${gas['value']:.2f}/gal", f"{fmt_ch(gas['value'],gas['m1'],'',2)} in a month", f"A 15-gallon fill-up costs about ${gas['value']*15:.0f}, vs ${gas['y1']*15:.0f} a year ago.", f"EIA weekly · {gas['date']}"),
     ('Oil (WTI)', f"${oil['value']:.0f}", f"{(oil['value']/oil['m1']-1)*100:+.1f}% in a month", f"Oil is {(oil['value']/oil['y1']-1)*100:+.0f}% from a year ago. Gas prices usually follow within a few weeks.", f"EIA via FRED · {oil['date']}"),
     ('S&P 500', f"{sp['value']:,.0f}", f"{(sp['value']/sp['m1']-1)*100:+.1f}% in a month", f"Up {(sp['value']/sp['y1']-1)*100:.0f}% in a year. This is what most 401(k) and index funds hold; short swings matter less than staying invested." if sp['value']>sp['y1'] else "Down over a year. Most 401(k)s hold this; selling after a drop locks in the loss.", f"S&P Dow Jones via FRED · {sp['date']}"),
     ('US dollar (vs. trade partners)', f"{dl['value']:.1f}", f"{(dl['value']/dl['m1']-1)*100:+.1f}% in a month", "A stronger dollar makes trips abroad and imports cheaper, and foreign savings worth less in dollars." if up('dollar') else "A weaker dollar makes trips abroad pricier and foreign savings worth more in dollars.", f"Federal Reserve index via FRED · {dl['date']}"),
     ('Bitcoin', f"${btc['current_price']:,.0f}", f"{btc['price_change_percentage_24h']:+.1f}% in 24h", "Moves a lot. Treat it as money you can afford to see drop by half; it is not insured savings.", 'CoinGecko'),
    ]
    rows = ''.join(f'<div class="mrow"><h3>{e(n)}</h3><span class="v">{e(v)}</span><span class="ch">{e(c)}</span><p>{e(t)}</p><span class="src">{e(s)}</span></div>' for n, v, c, t, s in items)
    import datetime
    EV = [('2026-10-14','Inflation report (CPI, September)','If prices rose faster than expected, rate cuts get less likely: good for savers, bad for borrowers.','BLS'),
          ('2026-10-15','Producer prices (PPI)','Early hint of where store prices go next.','BLS'),
          ('2026-10-28','Fed rate decision','Sets the rate that savings accounts and credit card APRs follow.','Federal Reserve'),
          ('2026-10-30','Wage growth (Employment Cost Index)','Fast wage growth can keep inflation and rates higher.','BLS'),
          ('2026-11-10','Inflation report (CPI, October)','The last big inflation number before the December Fed meeting.','BLS'),
          ('2026-12-09','Fed rate decision','With new forecasts for next year.','Federal Reserve')]
    today = datetime.date.today().isoformat()
    ev = ''.join(f'<li><b>{datetime.date.fromisoformat(d).strftime("%a %b %-d")}</b><span><strong>{e(n)}</strong><br>{e(t)} <small>({s})</small></span></li>' for d, n, t, s in EV if d >= today)[:6000]
    return (CSS + '<section class="pagehead"><p class="eyebrow">MARKETS / WHAT IT MEANS FOR YOU</p><h1>The numbers that hit <em>your wallet.</em></h1>'
        '<p class="lead">Loan rates, savings rates, gas and your 401(k), each with one line on why it matters. Updated every morning.</p></section>'
        + rows + '<section class="digest" id="watch"><p class="eyebrow">WHAT TO WATCH</p><h2>Coming up</h2><ul class="ev">' + ev + '</ul><p class="fine">Dates from the BLS and Federal Reserve calendars.</p></section>')

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
