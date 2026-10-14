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
def card_value(c, prof, pv):
    tot = 0
    for k, _ in CATS:
        amt = prof[k]*12; r = c['earn'].get(k, c['earn']['other'])
        cap = c.get('cap', {}).get(k)
        if cap and amt > cap: tot += cap*r/100 + (amt-cap)*c['earn']['other']/100
        else: tot += amt*r/100
    return round(tot - c['fee'])
def cards_body():
    d = dj('cards.json'); prof = d['profile']; cs = d['cards']; pv = d['pointValue']
    for c in cs: c['val'] = card_value(c, prof, pv)
    rk = sorted(cs, key=lambda c: -c['val'])
    by = {c['id']: c for c in cs}
    nofee = max((c for c in cs if c['fee'] == 0 and c['type'] == 'cash'), key=lambda c: c['val'])
    prem = max((c for c in cs if c['type'] == 'travel'), key=lambda c: c['val'])
    picks = [('Most cash back overall', by['rh'], 'If you already use Robinhood or are fine paying $5/mo for Gold, 3% on everything beats every other card here, even after the membership fee.'),
             ('Best simple card, no fees at all', nofee, f"Flat 2% on everything with no membership. Wells Fargo Active Cash is the same 2% and adds a $100 bonus and phone insurance."),
             ('Big on groceries', by['bcp'], '6% at US supermarkets on the first $6,000 a year. Pair it with a 2% card for everything else.'),
             ('Eat out a lot', by['sv'], '3% on dining, groceries and streaming with no annual fee.'),
             ('Travel and lounges', prem, 'Premium cards only beat 2–3% cash back if you actually use the credits and perks. On points alone they lose money at this spend.'),
             ('Pay rent by card', by['bb'], 'Earn points on rent with no transaction fee and no annual fee. Other cards charge about 3% to pay rent.')]
    ph = ''.join(f'<div class="pick"><span class="who">{e(w)}</span><h3>{e(c["name"])}</h3><span class="v">${c["val"]:,}/yr</span><p>{e(t)}</p></div>' for w, c, t in picks)
    rows = ''.join(f'<tr class="{"neg" if c["val"]<0 else ""}" data-id="{c["id"]}"><td><a href="{e(c["url"])}" rel="nofollow noopener">{e(c["name"])}</a><small>{e(c["earnText"])}</small>'
        + (f'<small>Bonus: {e(c["bonus"])}</small>' if c.get('bonus') else '') + (f'<small>Perks: {e(c["perks"])}</small>' if c.get('perks') else '') + (f'<small>{e(c["note"])}</small>' if c.get('note') else '')
        + f'</td><td class="hide">{"$0" if not c["fee"] else "$"+str(c["fee"])}<small>{e(c.get("feeNote",""))}</small></td><td class="n" data-v>${c["val"]:,}</td></tr>' for c in rk)
    js = 'const CARDS=' + json.dumps([{k: c.get(k) for k in ('id','earn','cap','fee')} for c in cs]) + ';'
    js += r'''const I=[...document.querySelectorAll('.calc input')],T=document.querySelector('.ctable tbody'),O=document.getElementById('calc-tot');
function val(c,p){let t=0;for(const k in p){const a=p[k]*12,r=(c.earn[k]??c.earn.other),cap=c.cap&&c.cap[k];t+=cap&&a>cap?cap*r/100+(a-cap)*c.earn.other/100:a*r/100}return Math.round(t-c.fee)}
function u(){const p={};I.forEach(i=>p[i.name]=+i.value.replace(/[^\d.]/g,'')||0);O.textContent='$'+Object.values(p).reduce((a,b)=>a+b,0).toLocaleString()+'/mo';
const rs=[...T.rows].map(r=>{const v=val(CARDS.find(c=>c.id===r.dataset.id),p);r.querySelector('[data-v]').textContent=(v<0?'-$':'$')+Math.abs(v).toLocaleString();r.className=v<0?'neg':'';return[v,r]});rs.sort((a,b)=>b[0]-a[0]).forEach(x=>T.appendChild(x[1]))}
I.forEach(i=>i.oninput=u);'''
    calc = ('<div class="calc"><b>Your monthly spending</b> <span class="tot">(total <span id="calc-tot"></span>, not counting rent)</span><div class="g">'
        + ''.join(f'<label>{l}<input name="{k}" inputmode="decimal" value="{prof[k]}"></label>' for k, l in CATS) + '</div>'
        + '<p class="tot">The table re-ranks as you type: yearly rewards minus the annual fee.</p></div>')
    total = sum(prof.values())
    return (CSS + '<section class="pagehead"><p class="eyebrow">CARDS / COMPARED HONESTLY</p><h1>Which card pays you <em>the most?</em></h1>'
        f'<p class="lead">For someone spending ${total:,} a month, here is what each popular card is worth in a year after its fee. Change the numbers to match your spending.</p></section>'
        f'<div class="picks">{ph}</div>{calc}'
        f'<table class="ctable"><thead><tr><th>Card · how it earns</th><th class="hide">Fee</th><th style="text-align:right">Value/yr</th></tr></thead><tbody>{rows}</tbody></table>'
        f'<details class="tuck"><summary>How we count the value</summary><p>{e(d["assumption"])}</p><p>Default spending: ' + ', '.join(f'{l.lower()} ${prof[k]}' for k, l in CATS)
        + '. Signup bonuses are listed but not counted, since they only pay once. Caps are applied (Amex Gold, Blue Cash Preferred). Rent cards are compared on everyday spend; their edge is earning on rent with no fee.</p></details>'
        + f'<script>{js}u()</script>')

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
