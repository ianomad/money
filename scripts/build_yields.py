"""Build docs/world.html (international bank deposits) from data/yields.json + data/fx.json.

  python3 scripts/build_yields.py          # rebuild from saved data
  python3 scripts/build_yields.py --fetch  # refresh today's FX (open.er-api.com) first

Bank rates are hand-verified (see 'verified' per product); nothing here is estimated.
"""
import json, subprocess, sys, hashlib
from datetime import date
from html import escape as e
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA, FX, OUT = ROOT/'data/yields.json', ROOT/'data/fx.json', ROOT/'docs/world.html'
FX_API = 'https://open.er-api.com/v6/latest/USD'

if '--fetch' in sys.argv:
    raw = json.loads(subprocess.run(['curl','-sSfL','--max-time','60',FX_API],check=True,capture_output=True).stdout)
    codes = [c['currency'] for c in json.loads(DATA.read_text())['countries']]
    FX.write_text(json.dumps({'source':FX_API,'updated':raw['time_last_update_utc'],'fetched':date.today().isoformat(),
                              'rates':{c: raw['rates'][c] for c in codes if c in raw['rates']}}, indent=1)+'\n')
d, fx = json.loads(DATA.read_text()), json.loads(FX.read_text())

def money(x, cur='$'): return f'{cur}{x:,.0f}'
def calc(rate, start_fx, now_fx, usd=500_000, years=3):
    local0 = usd*start_fx; local = local0*(1+rate/100)**years
    return local0, local, local/now_fx

kg = next(c for c in d['countries'] if c['code']=='KG')
kgnow = fx['rates']['KGS']; kg0 = kg['fxStart']['rate']
top_kg = max(p['rate'] for p in kg['products'] if p['currency']=='KGS')
scen = []
for r,label in ((15.0,'Caller’s “up to 15%” scenario'),(top_kg,f'Best KGS rate on the table today ({top_kg:g}%)')):
    l0,l,u = calc(r,kg0,kgnow)
    scen.append(f'<tr><td>{e(label)}</td><td>{r:g}%</td><td>{money(l0,"")} KGS</td><td>{money(l,"")} KGS</td><td><b>{money(u)}</b></td><td>{u/500000-1:+.1%}</td></tr>')
us = calc(4.27,1,1)[2]
fxmove = kgnow/kg0-1

def country(c):
    rows=''.join(f'''<tr><td><b>{e(p['bank'])}</b><br><small>{e(p['product'])}</small></td><td>{e(p['currency'])}</td><td><b>{p['rate']:g}%</b>{'<br><small>'+e(p['rateNote'])+'</small>' if p.get('rateNote') else ''}</td><td>{e(p['term'])}</td><td>{e(p['min'])}</td><td>{e(p.get('usdOption','—'))}</td><td>{e(p['access'])}</td><td><a href="{e(p['source'])}" target="_blank" rel="noopener">source ↗</a><br><small>verified {e(p['verified'])}</small></td></tr>''' for p in sorted(c['products'],key=lambda p:-p['rate']))
    now = fx['rates'].get(c['currency'])
    fxline = f'Today 1 USD = {now:,.4g} {c["currency"]}' if now else ''
    if c.get('fxStart') and now:
        fxline += f' · {c["fxStart"]["date"]}: {c["fxStart"]["rate"]:,.4g} (<a href="{e(c["fxStart"]["source"])}" target="_blank" rel="noopener">{e(c["fxStart"]["label"])}</a>) · local currency {"lost" if now>c["fxStart"]["rate"] else "gained"} {abs(1-c["fxStart"]["rate"]/now):.0%} vs USD'
    best=max(c['products'],key=lambda p:p['rate'])
    return f'''<details class="yc" id="{c['code'].lower()}"><summary><b>{e(c['name'])}</b> · best {best['rate']:g}% ({e(best['bank'])}, {e(best['currency'])}) · {len(c['products'])} product{'s' if len(c['products'])>1 else ''}</summary><p class="fx">{fxline}</p><div class="tw"><table><thead><tr><th>Bank / product</th><th>Cur.</th><th>Rate</th><th>Term</th><th>Minimum</th><th>USD/EUR option</th><th>Foreigners / how to open</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div><p class="ins"><b>Deposit insurance:</b> {e(c['insurance'])}</p></details>'''


def summary_row(c):
    best=max(c['products'],key=lambda p:p['rate']); now=fx['rates'].get(c['currency'])
    move=f"{('−' if now>c['fxStart']['rate'] else '+')}{abs(1-c['fxStart']['rate']/now):.0%}" if c.get('fxStart') and now else '—'
    ins=c['insurance'].split('.')[0]
    if len(ins)>70: ins=ins[:67].rsplit(' ',1)[0]+'…'
    return f'<tr><td><a href="#{c["code"].lower()}">{e(c["name"])}</a></td><td><b>{best["rate"]:g}%</b></td><td>{e(best["bank"])}</td><td>{e(best["currency"])}</td><td>{move}</td><td><small>{e(ins)}</small></td></tr>'
summary=f'''<section class="calc" id="world-table"><p class="eyebrow">BEST RATE BY COUNTRY</p><div class="tw"><table><thead><tr><th>Country</th><th>Best rate</th><th>Bank</th><th>Currency</th><th>Currency vs USD since start date</th><th>Deposit insurance</th></tr></thead><tbody>{''.join(summary_row(c) for c in sorted(d['countries'],key=lambda c:-max(p['rate'] for p in c['products'])))}</tbody></table></div><p><small>Local-currency rates. Tap a country below for every bank, terms, how foreigners open accounts and sources.</small></p></section>'''
css='''<style>.yc{margin:.6rem 0;border:1px solid rgba(127,127,127,.3);border-radius:.8rem;padding:.7rem 1rem}.yc summary{cursor:pointer;font-size:1.05rem}.yc[open] summary{margin-bottom:.6rem}.tag{font-size:.8rem;background:#f3d36b;color:#222;padding:.15rem .5rem;border-radius:1rem;vertical-align:middle}.tw{overflow-x:auto}.yc table,.calc table{width:100%;border-collapse:collapse;font-size:.92rem}.yc th,.yc td,.calc th,.calc td{padding:.55rem .5rem;border-bottom:1px solid rgba(127,127,127,.25);text-align:left;vertical-align:top}.fx,.ins{font-size:.9rem;opacity:.85}.calc{margin:2rem 0;padding:1.5rem;border:1px solid rgba(127,127,127,.3);border-radius:1rem}.wrap{max-width:1150px;margin:0 auto;padding:0 1.2rem}</style>'''
nav = '<nav aria-label="Main navigation"><a class="nav-switch" href="index.html">Savings</a><a class="nav-switch" href="world.html" aria-current="page">World</a><a class="nav-switch" href="cards.html">Cards</a><a class="nav-switch" href="economy.html">Economy</a><a class="nav-switch" href="crypto.html">Crypto</a><a class="nav-switch" href="insights.html">Insights</a><a class="nav-switch" href="daily.html">Daily</a></nav>'
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>World deposit rates — Money</title><meta name="description" content="Bank-by-bank deposit rates abroad: Kyrgyzstan, Uzbekistan, Kazakhstan, Turkey and more, with sources, insurance limits and FX."><link rel="canonical" href="https://money.ilyusha.xyz/world.html"><link rel="icon" href="favicon.ico?v=2" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png?v=2"><link rel="apple-touch-icon" href="apple-touch-icon.png?v=2"><link rel="stylesheet" href="styles.css"><script src="analytics.js" defer></script>{css}</head>
<body><header><a class="brand" href="index.html"><img class="brand-mark" src="favicon.svg" alt="">money<span class="brand-by">/ by ilyusha</span></a>{nav}<a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main class="wrap"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> WORLD DEPOSITS / BANK BY BANK</p><h1>Where cash <em>earns more.</em></h1><p>Deposit accounts you open directly at a bank in another country, bank by bank, with the source for every rate. Checked {e(d['checkedAt'])}; FX refreshed daily ({e(fx['fetched'])}, <a href="{FX_API}" target="_blank" rel="noopener">open.er-api.com</a>).</p><p><small>{e(d['note'])}</small></p></div></section>
<section class="calc" id="kg-calc"><p class="eyebrow">MISSED OPPORTUNITY · KYRGYZSTAN</p><h2>$500,000 in a som deposit, October 2023 → today</h2><p>Converted at the NBKR rate of {kg0} KGS/USD on {kg['fxStart']['date']}, compounded yearly for 3 years, converted back at today’s {kgnow:.2f}. The som moved {fxmove:+.1%} against the dollar, so the currency barely hurt. We don’t have a verified 2023 rate sheet yet, so these are scenarios, not what a bank actually paid then. Kyrgyz rates on the table today top out at {top_kg:g}% (14.66% effective at ABank). The US baseline is 4.27% for 3 years = {money(us)}.</p><div class="tw"><table><thead><tr><th>Scenario</th><th>Rate</th><th>Start (KGS)</th><th>After 3 yrs (KGS)</th><th>In USD today</th><th>Gain</th></tr></thead><tbody>{''.join(scen)}</tbody></table></div><p><small>Before tax. Most products don’t compound inside one deposit; this assumes you roll it over each year at the same rate. The insurance cap is 1M som (about {money(1_000_000/kgnow)}), so $500k is almost all uninsured unless you spread it over many banks. Other risks: devaluation, rules on moving money out of the country, and AML checks on large inbound wires. US taxpayers owe US tax on foreign interest and must file FBAR/FATCA reports.</small></p></section>
{summary}<section class="countries"><p class="eyebrow">BANK BY BANK</p>{''.join(country(c) for c in d['countries'])}</section>
</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="mailto:dev@ilyusha.xyz?subject=World%20deposits%20correction">Suggest a bank or correction ↗</a></footer></body></html>'''
for asset in ('styles.css','analytics.js','favicon.svg'):
    v=hashlib.sha256((ROOT/'docs'/asset).read_bytes()).hexdigest()[:10]; page=page.replace(f'"{asset}"',f'"{asset}?v={v}"')
OUT.write_text(page); print('Built world.html;', ' | '.join(s for s in scen))
import subprocess as _sp, sys as _sys
_sp.run([_sys.executable, str(ROOT/'scripts/compose.py')], check=True)
