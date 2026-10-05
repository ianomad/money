"""Build docs/insights.html from data/insights.json plus the site's own data/rates.json and docs/cards.html.

  python3 scripts/build_insights.py           # rebuild from the saved inputs
  python3 scripts/build_insights.py --fetch   # refresh T-bill yields (Treasury), fed funds (FRED), FDIC national savings
                                              # rate, I bond rate (TreasuryDirect) and Discover's quarter (cards.html) first

No figure is typed into this file: every input lives in data/insights.json with its source URL and checked date,
and every dollar amount on the page is arithmetic on those inputs.
"""
import csv, hashlib, io, json, re, subprocess, sys
from datetime import date, datetime
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, RATES, CARDS, OUT = ROOT / 'data/insights.json', ROOT / 'data/rates.json', ROOT / 'docs/cards.html', ROOT / 'docs/insights.html'

def get(url):
    return subprocess.run(['curl', '-sSL', '--compressed', '--http1.1', '--max-time', '60', '-A', 'Mozilla/5.0', url], check=True, capture_output=True, text=True).stdout

def text(url):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', get(url)))

def fetch():
    d = json.loads(DATA.read_text()); i = d['inputs']; today = date.today().isoformat()
    def step(name, fn):
        try: fn(); i[name]['checked'] = today; print(f'{name}: refreshed')
        except Exception as err: print(f'{name}: kept saved value ({err})')
    def tbill():
        x = get(f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_bill_rates&field_tdr_date_value={date.today().year}')
        last = x.split('<entry>')[-1]
        f = lambda k: float(re.search(rf'<d:{k}[^>]*>([^<]+)<', last).group(1))
        i['tbill'].update(date=re.search(r'<d:INDEX_DATE[^>]*>([0-9-]{10})', last).group(1), y4=f('ROUND_B1_YIELD_4WK_2'), y13=f('ROUND_B1_YIELD_13WK_2'), y26=f('ROUND_B1_YIELD_26WK_2'))
    def fed():
        rows = [r for r in csv.reader(io.StringIO(get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF,DFEDTARL,DFEDTARU')))][1:]
        dff = [r for r in rows if r[1] not in ('', '.')][-1]; tgt = [r for r in rows if r[2] not in ('', '.')][-1]
        i['fed'].update(dff=float(dff[1]), dffDate=dff[0], lower=float(tgt[2]), upper=float(tgt[3]))
    def fdic():
        t = text(i['fdicNational']['url'])
        m = re.search(r'as of (\w+ \d+, \d{4}).*?Savings ([0-9.]+) ', t)
        i['fdicNational'].update(savings=float(m.group(2)), asOf=datetime.strptime(m.group(1), '%B %d, %Y').date().isoformat())
    def ibond():
        t = text(i['ibond']['url'])
        m = re.search(r'Series I Savings Bonds ([0-9.]+)% This includes a fixed rate of ([0-9.]+)% For I bonds issued (.+? to .+?\d{4})', t)
        i['ibond'].update(composite=float(m.group(1)), fixed=float(m.group(2)), period=m.group(3))
    def discover():
        t = re.sub(r'<[^>]+>', ' ', CARDS.read_text())
        m = re.search(r'(\w{3}–\w{3} \d{4}): ([^.]+?), on up to \$([0-9,]+)', t)
        i['discover'].update(quarter=m.group(1), categories=m.group(2), cap=int(m.group(3).replace(',', '')))
    for n, fn in (('tbill', tbill), ('fed', fed), ('fdicNational', fdic), ('ibond', ibond), ('discover', discover)): step(n, fn)
    d['checkedAt'] = today
    DATA.write_text(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

money = lambda n: f'${n:,.0f}'
pct = lambda n: f'{n:.2f}%'
nice = lambda s: datetime.strptime(s, '%Y-%m-%d').strftime('%b %-d, %Y')

def build():
    d = json.loads(DATA.read_text()); i = d['inputs']
    rates = json.loads(RATES.read_text()); provs = rates['providers']
    offer = lambda p: p['boost'] if p.get('boost') is not None else p['base']
    plain = sorted((p for p in provs if p['fdic']['status'] == 'bank' and p['base'] is not None and offer(p) == p['base']), key=lambda p: -p['base'])
    fit, low = plain[0], plain[-1]   # best and lowest straightforward FDIC-insured bank rate on the site
    rsrc = lambda p: p['sources'][0]['url']
    cards = CARDS.read_text()
    flat = re.search(r'data-name="([^"]+)" data-everyday="2"', cards)
    flatname = flat.group(1).title() if flat else i['flat2']['name']
    T, ca, fn, fed, ib, dc, fc = i['tbill'], i['caBracket'], i['fdicNational'], i['fed'], i['ibond'], i['discover'], i['fdicCategories']
    out = []
    # 1. Cash at a big bank
    gap = fit['base'] - fn['savings']
    out.append(dict(pay=50000 * gap / 100,
        head=f'Cash at the national-average rate gives up <em>{money(50000 * gap / 100)} a year</em> on $50,000.',
        body=f'The FDIC puts the national average savings rate at {pct(fn["savings"])}. {e(fit["name"])} pays {pct(fit["base"])} with no subscription, boost or promo. Moving the money takes one transfer.',
        ex=f'Gap: {pct(fit["base"])} − {pct(fn["savings"])} = {gap:.2f} points<br>$10,000 → {money(10000 * gap / 100)}/yr · $25,000 → {money(25000 * gap / 100)}/yr · $50,000 → {money(50000 * gap / 100)}/yr',
        catch=f'Savings rates are variable and can drop any time. The FDIC figure is an average of all banks as of {nice(fn["asOf"])}, so your own bank may pay more or less.',
        src=[(fn['source'], fn['url']), (f'{fit["name"]} rate page', rsrc(fit))]))
    # 2. Fed pass-through
    pf, pl, pa = fit['base'] / fed['dff'] * 100, low['base'] / fed['dff'] * 100, fn['savings'] / fed['dff'] * 100
    out.append(dict(pay=50000 * (fit['base'] - low['base']) / 100,
        head=f'Banks pass on very different shares of the Fed rate: <em>{money(50000 * (fit["base"] - low["base"]) / 100)} a year</em> on $50,000 between two no-strings accounts.',
        body=f'The effective federal funds rate was {pct(fed["dff"])} on {nice(fed["dffDate"])} (target range {fed["lower"]:.2f}–{fed["upper"]:.2f}%). {e(fit["name"])} pays {pf:.0f}% of that, {e(low["name"])} pays {pl:.0f}%, and the national average savings account pays {pa:.0f}%.',
        ex=f'{e(fit["name"])} {pct(fit["base"])} vs {e(low["name"])} {pct(low["base"])} on $50,000 → {money(50000 * fit["base"] / 100)} vs {money(50000 * low["base"] / 100)} a year<br>Every 0.25-point move, if passed on in full, is {money(50000 * .25 / 100)} a year on $50,000',
        catch='This is a snapshot, not a forecast. Banks choose how much of a Fed move to pass on, and how fast.',
        src=[(fed['source'], fed['url']), (f'{low["name"]} rate page', rsrc(low))]))
    # 3. T-bills after state tax
    after = fit['base'] * (1 - ca['rate'] / 100); teq = T['y26'] / (1 - ca['rate'] / 100)
    win = 50000 * (T['y26'] - after) / 100
    nt = 50000 * (T['y26'] - fit['base']) / 100
    out.append(dict(pay=win,
        head=f'In California, 26-week T-bills beat the best plain savings rate by <em>{money(win)} a year</em> on $50,000.',
        body=f'Treasury bill interest is exempt from state and local income tax; savings interest is not. At California\'s {ca["rate"]:.1f}% bracket, the {pct(T["y26"])} 26-week bill is worth {pct(teq)} in savings terms, while {e(fit["name"])}\'s {pct(fit["base"])} keeps only {pct(after)} after state tax.',
        ex=f'Yields on {nice(T["date"])}: 4-week {pct(T["y4"])} · 13-week {pct(T["y13"])} · 26-week {pct(T["y26"])}<br>California, $50,000: bill {money(50000 * T["y26"] / 100)} vs savings {money(50000 * after / 100)} after state tax → +{money(win)}<br>No-income-tax state: bill {money(50000 * T["y26"] / 100)} vs savings {money(50000 * fit["base"] / 100)} → {"+" if nt >= 0 else "−"}{money(abs(nt))}; the 13-week bill trails by {money(50000 * (fit["base"] - T["y13"]) / 100)}',
        catch=f'Federal tax applies to both. The {ca["rate"]:.1f}% bracket covers {ca["year"]} single filers with taxable income of {money(ca["from"])}–{money(ca["to"])}. Bill yields are fixed only until maturity, you must roll them yourself, and a bill sold early gets the market price. A bill\'s coupon-equivalent yield and a bank APY are close but not identical measures.',
        src=[(i['tbillTax']['source'], i['tbillTax']['url']), (T['source'], T['url']), (ca['source'], ca['url'])]))
    # 4. I bonds
    out.append(dict(pay=ib['limit'] * ib['fixed'] / 100,
        head=f'I bonds lock in <em>{pct(ib["fixed"])} above inflation for up to 30 years</em>: {money(ib["limit"] * ib["fixed"] / 100)} a year in real terms on {money(ib["limit"])}.',
        body=f'I bonds issued {e(ib["period"])} earn {pct(ib["composite"])}: a fixed {pct(ib["fixed"])} plus inflation, reset every six months. The fixed part never changes for the bond\'s life, so it is a guaranteed return above inflation. Like T-bills, the interest is free of state and local tax.',
        ex=f'{money(ib["limit"])} at {pct(ib["composite"])} → about {money(ib["limit"] * ib["composite"] / 100)} in the first year<br>Real (above-inflation) part: {money(ib["limit"])} × {pct(ib["fixed"])} = {money(ib["limit"] * ib["fixed"] / 100)} a year',
        catch=f'Limit {money(ib["limit"])} in electronic I bonds per person per calendar year. You can\'t cash them for 12 months, and cashing before 5 years costs the last 3 months of interest. The inflation part can fall.',
        src=[(ib['source'], ib['url'])]))
    # 5. Discover quarter
    q5 = dc['cap'] * dc['rate'] / 100; q1 = dc['cap'] * dc['base'] / 100; q2 = dc['cap'] * i['flat2']['rate'] / 100
    out.append(dict(pay=q5 - q1,
        head=f'Activate Discover\'s {e(dc["quarter"])} 5% and earn <em>{money(q5)} instead of {money(q1)}</em> on {money(dc["cap"])} of bills and dinners.',
        body=f'This quarter Discover it pays {dc["rate"]}% on {e(dc["categories"])}. Utilities are the overlooked part: a bill you pay anyway, so the extra cash back costs nothing in new spending. You have to activate it.',
        ex=f'{money(dc["cap"])} in the categories: {dc["rate"]}% = {money(q5)} vs {dc["base"]}% unactivated = {money(q1)} (+{money(q5 - q1)})<br>vs a flat 2% card like {e(flatname)}: {money(q2)} (+{money(q5 - q2)})',
        catch=f'5% stops at {money(dc["cap"])} of category spending for the quarter; after that it\'s 1%. Some utility companies charge a fee to pay by card, which can wipe out the gain. Pay the balance in full.',
        src=[('Discover cashback calendar', dc['url']), ('Cards on this site', 'cards.html')]))
    # 6. FDIC categories (protection, not yield)
    couple = 2 * fc['single'] + 2 * fc['jointPerCoOwner']
    out.append(dict(pay=0,
        head=f'A couple can insure <em>{money(couple)}</em> at one bank, not $250,000, by using ownership categories.',
        body=f'FDIC insurance is {money(fc["single"])} per depositor, per bank, per ownership category. Two individual accounts plus one joint account are three separate pots. Trust accounts with beneficiaries add up to {money(fc["trustMax"])} more per owner.',
        ex=f'Partner A single: {money(fc["single"])} · Partner B single: {money(fc["single"])} · Joint: {money(fc["jointPerCoOwner"])} × 2 co-owners = {money(2 * fc["jointPerCoOwner"])}<br>Total insured at one bank: {money(couple)}',
        catch='This applies to FDIC-insured banks only. Fintech apps with pass-through coverage depend on the partner bank keeping records correctly, and balances at the same bank through different apps add together.',
        src=[(fc['source'], fc['url']), ('FDIC, Understanding deposit insurance', 'https://www.fdic.gov/resources/deposit-insurance/understanding-deposit-insurance/')]))
    top = out[0]; checked = nice(d['checkedAt'])
    link = lambda s: f'<a href="{e(s[1])}"{"" if s[1].endswith(".html") else " target=\"_blank\" rel=\"noopener\""}>{e(s[0])}{"" if s[1].endswith(".html") else " ↗"}</a>'
    items = ''.join(f'<li class="insight"><span class="insight-rank">{n:02d}</span><div><h3>{o["head"]}</h3><p>{o["body"]}</p><p class="example">{o["ex"]}</p>'
                    f'<p class="catch"><b>The catch:</b> {o["catch"]}</p><p class="src">Source: {" · ".join(link(s) for s in o["src"])}</p></div></li>' for n, o in enumerate(out, 1))
    gap = fit['base'] - fn['savings']
    hero = (f'<section class="share-card" id="share"><p class="eyebrow">Biggest one</p><p class="share-rate">{money(50000 * gap / 100)}<small style="font-size:.4em"> / yr</small></p>'
            f'<p class="share-who">Lost on $50,000 at the {pct(fn["savings"])} national average vs {e(fit["name"])}\'s {pct(fit["base"])}</p><p class="share-catch">FDIC national average vs the best no-strings rate on this site.</p>'
            f'<p class="share-date">Checked {checked} · money.ilyusha.xyz</p></section>')
    desc = f'{len(out)} checked ways to keep more money: savings vs the national average, T-bills after state tax, I bonds, card categories and FDIC coverage. Every number cited.'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Money — insights</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="https://money.ilyusha.xyz/insights.html"><meta property="og:title" content="Money — insights"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz/insights.html"><meta name="twitter:card" content="summary"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="analytics.js" defer></script></head>
<body><a class="skip-link" href="#insights">Skip to insights</a><header><a class="brand" href="index.html"><img class="brand-mark" src="favicon.svg" alt="">money<span class="brand-by">/ by ilyusha</span></a><nav aria-label="Main navigation"><a class="nav-switch" href="index.html">Savings</a><a class="nav-switch" href="cards.html">Cards</a><a class="nav-switch" href="economy.html">Economy</a><a class="nav-switch" href="crypto.html">Crypto</a><a class="nav-switch" href="insights.html" aria-current="page">Insights</a></nav><a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main id="top"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> INSIGHTS / USD</p><h1>Money <em>left on the table.</em></h1>{hero}</div><aside class="snapshot"><div class="snapshot-count">{len(out)}<span>checked<br>insights</span></div><div class="snapshot-date">Checked <time datetime="{e(d['checkedAt'])}">{checked}</time></div><p>Every figure is cited · Biggest first</p></aside></section>
<section id="insights" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">01 / BY DOLLAR IMPACT</span><h2>Worth doing<span>.</span></h2></div><p>Worked out on example amounts</p></div><ol class="insight-list">{items}</ol></section>
<p class="econ-note crypto-plain">General information, not financial or tax advice. Numbers were checked on {checked}; rates change, so confirm with the source before you move money.</p>
</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="index.html">Back to savings</a></footer></body></html>
'''
    for asset in ('styles.css', 'analytics.js', 'favicon.svg'):
        v = hashlib.sha256((ROOT / 'docs' / asset).read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{asset}"', f'"{asset}?v={v}"')
    OUT.write_text(page)
    print(f'Built insights page: {len(page) // 1024} KB, {len(out)} insights, top {money(top["pay"])}, checked {d["checkedAt"]}.')

if __name__ == '__main__':
    if '--fetch' in sys.argv: fetch()
    build()
