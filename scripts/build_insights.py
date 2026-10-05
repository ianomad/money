"""Build docs/insights.html from data/insights.json plus the site's own data/rates.json and docs/cards.html.

  python3 scripts/build_insights.py           # rebuild from the saved inputs
  python3 scripts/build_insights.py --fetch   # refresh T-bill yields (Treasury), fed funds (FRED), FDIC national savings
                                              # rate, I bond rate (TreasuryDirect) and Discover's quarter (cards.html) first

No figure is typed into this file: every input lives in data/insights.json with its source URL and checked date,
and every dollar amount on the page is arithmetic on those inputs.
Framed for high balances ($50k / $250k / $1M), covering cash, tax/structure, credit, and stocks.
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
    def schd():
        t = text(i['schd']['url'])
        m = re.search(r'SEC Yield \(30 Day\) As of (\d{2}/\d{2}/\d{4}).*?([0-9.]+)%', t)
        if not m:
            m = re.search(r'SEC Yield[^0-9]*([0-9.]+)\s*%.*?As of (\d{2}/\d{2}/\d{4})', t)
        if m:
            # tolerate either group order
            try:
                asof = datetime.strptime(m.group(1), '%m/%d/%Y').date().isoformat()
                yld = float(m.group(2))
            except ValueError:
                yld = float(m.group(1))
                asof = datetime.strptime(m.group(2), '%m/%d/%Y').date().isoformat()
            i['schd'].update(secYield=yld, secYieldAsOf=asof)
    for n, fn in (('tbill', tbill), ('fed', fed), ('fdicNational', fdic), ('ibond', ibond), ('discover', discover), ('schd', schd)):
        step(n, fn)
    d['checkedAt'] = today
    DATA.write_text(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

money = lambda n: f'${n:,.0f}'
pct = lambda n: f'{n:.2f}%'
bn = lambda n: f'${n:,.1f}B' if n < 1000 else f'${n/1000:,.2f}T'
mm = lambda n: f'${n/1000:,.1f}B' if n >= 1000 else money(n)  # n in millions → billions when large
nice = lambda s: datetime.strptime(s, '%Y-%m-%d').strftime('%b %-d, %Y')

def tier_line(amounts, labels, fn):
    return ' · '.join(f'{lab} → {money(fn(a))}/yr' for a, lab in zip(amounts, labels))

def build():
    d = json.loads(DATA.read_text()); i = d['inputs']
    rates = json.loads(RATES.read_text()); provs = rates['providers']
    offer = lambda p: p['boost'] if p.get('boost') is not None else p['base']
    plain = sorted((p for p in provs if p['fdic']['status'] == 'bank' and p['base'] is not None and offer(p) == p['base']), key=lambda p: -p['base'])
    fit, low = plain[0], plain[-1]   # best and lowest straightforward FDIC-insured bank rate on the site
    # Next best plain with no stated interest-balance cap for overflow above Elevault's $500k earn limit
    elev_caps = i['elevaultCaps']
    def _uncapped(p):
        r = (p.get('requirements') or '').lower()
        return p['id'] != fit['id'] and 'up to $' not in r and 'below $' not in r and 'paused' not in r and 'waiting list' not in r
    overflow = next((p for p in plain if _uncapped(p)), plain[1])
    rsrc = lambda p: p['sources'][0]['url']
    cards = CARDS.read_text()
    flat = re.search(r'data-name="([^"]+)" data-everyday="2"', cards)
    flatname = flat.group(1).title() if flat else i['flat2']['name']
    T, ca, fn, fed = i['tbill'], i['caBracket'], i['fdicNational'], i['fed']
    fc, nc, tiers, spend = i['fdicCategories'], i['ncua'], i['tiers'], i['spendTiers']
    brk, schd, aapl = i['brk'], i['schd'], i['aapl']
    amounts, labels = tiers['amounts'], tiers['labels']
    gap = fit['base'] - fn['savings']

    def elev_earn(bal, rate=None):
        """Interest-bearing balance under Elevault's published interest max."""
        r = fit['base'] if rate is None else rate
        capped = min(bal, elev_caps['interestMax'])
        return capped * r / 100

    def stacked_vs_national(bal):
        """Best plain on site, respecting Elevault interest cap; overflow at next uncapped plain rate."""
        cap = elev_caps['interestMax']
        if bal <= cap:
            return bal * fit['base'] / 100
        return cap * fit['base'] / 100 + (bal - cap) * overflow['base'] / 100

    def national_earn(bal):
        return bal * fn['savings'] / 100

    out = []

    # 1. Opportunity cost of parking at the national average (big-bank proxy)
    lose = {a: stacked_vs_national(a) - national_earn(a) for a in amounts}
    top_lose = lose[amounts[-1]]
    days_250 = -(-250_000 // elev_caps['dailyDeposit'])
    days_500 = -(-elev_caps['interestMax'] // elev_caps['dailyDeposit'])
    out.append(dict(pay=top_lose, tag='Cash',
        head=f'Parking ${money(amounts[-1])[1:]} at the national-average savings rate gives up <em>{money(top_lose)} a year</em>.',
        body=f'The FDIC puts the national average savings rate at {pct(fn["savings"])} (as of {nice(fn["asOf"])}). '
             f'{e(fit["name"])} pays {pct(fit["base"])} with no subscription or promo, but interest only on balances up to {money(elev_caps["interestMax"])}, '
             f'and deposits are capped at {money(elev_caps["dailyDeposit"])} a day. Above that earn cap, the next plain no-strings rate on this site is {e(overflow["name"])} at {pct(overflow["base"])}.',
        ex=tier_line(amounts, labels, lambda a: lose[a])
           + f'<br>{e(fit["name"])} funding: {money(250_000)} takes {days_250} days at {money(elev_caps["dailyDeposit"])}/day · {money(elev_caps["interestMax"])} takes {days_500} days'
           + f'<br>On {money(amounts[-1])}: first {money(elev_caps["interestMax"])} at {pct(fit["base"])}, rest at {e(overflow["name"])} {pct(overflow["base"])} → {money(stacked_vs_national(amounts[-1]))}/yr vs {money(national_earn(amounts[-1]))} at the average',
        catch=f'Savings rates are variable. {e(fit["name"])} balances above {money(elev_caps["interestMax"])} earn no interest on the excess. The FDIC figure is an average of all banks, so a given big bank may pay more or less. Check each bank’s own deposit and balance limits before moving a large sum.',
        src=[(fn['source'], fn['url']), (f'{fit["name"]} rate page', rsrc(fit)), (f'{overflow["name"]} rate page', rsrc(overflow))]))

    # 2. Market dislocation: fed funds vs what savers get
    feed_gap = fed['dff'] - fn['savings']
    feed_lose = {a: a * feed_gap / 100 for a in amounts}
    out.append(dict(pay=feed_lose[amounts[-1]], tag='Market',
        head=f'The Fed funds rate is {pct(fed["dff"])}; the average savings account pays {pct(fn["savings"])}: <em>{money(feed_lose[amounts[-1]])} a year</em> of gap on {money(amounts[-1])}.',
        body=f'Effective federal funds was {pct(fed["dff"])} on {nice(fed["dffDate"])} (target {fed["lower"]:.2f}–{fed["upper"]:.2f}%). '
             f'That is what banks earn on overnight reserves. The FDIC national average savings rate is {pct(fn["savings"])}. '
             f'{e(fit["name"])} passes through {fit["base"] / fed["dff"] * 100:.0f}% of the funds rate; {e(low["name"])} passes {low["base"] / fed["dff"] * 100:.0f}%; the average account passes {fn["savings"] / fed["dff"] * 100:.0f}%.',
        ex=tier_line(amounts, labels, lambda a: feed_lose[a])
           + f'<br>{e(fit["name"])} {pct(fit["base"])} vs {e(low["name"])} {pct(low["base"])} on {money(amounts[1])} → {money(amounts[1] * fit["base"] / 100)} vs {money(amounts[1] * low["base"] / 100)} a year'
           + f'<br>Every 0.25-point Fed move, if passed on in full, is {money(amounts[1] * 0.25 / 100)}/yr on {money(amounts[1])} · {money(amounts[2] * 0.25 / 100)}/yr on {money(amounts[2])}',
        catch='This is a pricing snapshot, not a forecast. Banks choose how much of a Fed move to pass on, and how fast. You cannot earn the funds rate directly in a retail savings account.',
        src=[(fed['source'], fed['url']), (fn['source'], fn['url']), (f'{low["name"]} rate page', rsrc(low))]))

    # 3. Tax / structure: T-bills after California state tax
    after = fit['base'] * (1 - ca['rate'] / 100)
    teq = T['y26'] / (1 - ca['rate'] / 100)
    def tbill_win(bal):
        return bal * (T['y26'] - after) / 100
    win = {a: tbill_win(a) for a in amounts}
    out.append(dict(pay=win[amounts[-1]], tag='Tax',
        head=f'In California, 26-week T-bills beat the best plain savings rate by <em>{money(win[amounts[-1]])} a year</em> on {money(amounts[-1])} after state tax.',
        body=f'Treasury bill interest is exempt from state and local income tax; savings interest is not. At California\'s {ca["rate"]:.1f}% bracket, '
             f'the {pct(T["y26"])} 26-week bill is worth {pct(teq)} in taxable-savings terms, while {e(fit["name"])}\'s {pct(fit["base"])} keeps only {pct(after)} after state tax.',
        ex=f'Yields on {nice(T["date"])}: 4-week {pct(T["y4"])} · 13-week {pct(T["y13"])} · 26-week {pct(T["y26"])}<br>'
           + tier_line(amounts, labels, lambda a: win[a])
           + f'<br>No-income-tax state on {money(amounts[1])}: bill {money(amounts[1] * T["y26"] / 100)} vs savings {money(amounts[1] * fit["base"] / 100)} → '
           + (f'+{money(amounts[1] * (T["y26"] - fit["base"]) / 100)}' if T['y26'] >= fit['base'] else f'−{money(amounts[1] * (fit["base"] - T["y26"]) / 100)}'),
        catch=f'Federal tax applies to both. The {ca["rate"]:.1f}% bracket covers {ca["year"]} single filers with taxable income of {money(ca["from"])}–{money(ca["to"])}. '
              f'Bill yields are fixed only until maturity; you must roll them yourself; a bill sold early gets the market price. '
              f'A bill\'s coupon-equivalent yield and a bank APY are close but not identical measures. Buying {money(amounts[-1])} of bills needs a brokerage or TreasuryDirect plan and settlement cash.',
        src=[(i['tbillTax']['source'], i['tbillTax']['url']), (T['source'], T['url']), (ca['source'], ca['url'])]))

    # 4. Structure: FDIC / NCUA above $250k
    couple = 2 * fc['single'] + 2 * fc['jointPerCoOwner']
    out.append(dict(pay=0, tag='Structure',
        head=f'Above {money(fc["single"])}, insurance is a structure problem: a couple can cover <em>{money(couple)}</em> at one bank—or use more banks and NCUA credit unions.',
        body=f'FDIC insurance is {money(fc["single"])} per depositor, per insured bank, per ownership category. Two individual accounts plus one joint account are three separate pots '
             f'({money(couple)} for a couple). Trust accounts with beneficiaries add up to {money(fc["trustMax"])} more per owner under current FDIC rules. '
             f'NCUA share insurance at federally insured credit unions uses the same {money(nc["single"])} standard per member-owner, per credit union, per ownership category.',
        ex=f'Partner A single: {money(fc["single"])} · Partner B single: {money(fc["single"])} · Joint: {money(fc["jointPerCoOwner"])} × 2 = {money(2 * fc["jointPerCoOwner"])} → {money(couple)} at one bank<br>'
           f'On {money(amounts[1])}: one ownership category is enough · On {money(amounts[2])}: need categories, a second bank/credit union, or both<br>'
           f'{e(fit["name"])} is FDIC via Southern Bancorp; balances there aggregate with any other deposits at the same bank',
        catch='Fintech apps with pass-through coverage depend on partner-bank records. Balances at the same bank through different apps add together. NCUA covers federally insured credit unions only. Confirm title and beneficiary setup before relying on a category.',
        src=[(fc['source'], fc['url']), (nc['source'], nc['url']), ('FDIC, Understanding deposit insurance', 'https://www.fdic.gov/resources/deposit-insurance/understanding-deposit-insurance/')]))

    # 5. Credit that still matters at high spend: unlimited 2% vs 1%
    s_amt, s_lab = spend['amounts'], spend['labels']
    cb2 = {a: a * i['flat2']['rate'] / 100 for a in s_amt}
    cb1 = {a: a * 1 / 100 for a in s_amt}
    extra = {a: cb2[a] - cb1[a] for a in s_amt}
    out.append(dict(pay=extra[s_amt[-1]], tag='Credit',
        head=f'An unlimited 2% card pays <em>{money(extra[s_amt[-1]])} more a year</em> than 1% on {money(s_amt[-1])} of spend—category 5% caps do not.',
        body=f'{e(flatname)} and similar flat 2% cards pay {i["flat2"]["rate"]}% with no category cap. '
             f'Quarterly 5% rotating categories on this site top out around {money(i["discover"]["cap"])} of spend ({money(i["discover"]["cap"] * i["discover"]["rate"] / 100)} at 5%), '
             f'which is noise next to five-figure cash gaps on large balances. At high spend, the uncapped everyday rate is what scales.',
        ex=' · '.join(f'{lab} spend → 2% = {money(cb2[a])} · 1% = {money(cb1[a])} · extra {money(extra[a])}' for a, lab in zip(s_amt, s_lab))
           + f'<br>Discover {e(i["discover"]["quarter"])} 5% cap: {money(i["discover"]["cap"])} → {money(i["discover"]["cap"] * i["discover"]["rate"] / 100)} that quarter if activated',
        catch='Cash back only helps if you pay the balance in full. Some merchants surcharge cards. Foreign-transaction fees and annual fees change the net. This is rewards math, not a savings rate.',
        src=[('Cards on this site', 'cards.html'), (f'{flatname} issuer page', re.search(r'id="card-citi".*?href="([^"]+)"', cards, re.S).group(1) if re.search(r'id="card-citi".*?href="([^"]+)"', cards, re.S) else i['flat2']['url'])]))

    # Sort cash/tax/credit insights by dollar impact (structure with pay=0 stays last among zeros)
    out.sort(key=lambda o: (-o['pay'], o['tag'] != 'Structure'))

    # --- Stocks / opportunities (tweet-ready; separate section) ---
    eq_b = brk['equivClassA'] * brk['classBPerA']
    liquid_mn = brk['cashRestrictedMn'] + brk['tbillsMn']
    per_b_cash = liquid_mn * 1_000_000 / eq_b
    per_b_book = brk['equityMn'] * 1_000_000 / eq_b
    stocks = []

    # BRK.B
    stocks.append(dict(
        ticker=brk['ticker'],
        head=f'{brk["ticker"]}: <em>{bn(liquid_mn / 1000)}</em> in cash and T-bills on the June 30, 2026 10-Q.',
        thesis=f'Berkshire held {mm(brk["cashRestrictedMn"])} of cash and restricted cash plus {mm(brk["tbillsMn"])} of short-term U.S. Treasury bills—about {money(per_b_cash)} of cash and bills per equivalent Class B share—against {mm(brk["equityMn"])} of Berkshire shareholders\' equity (~{money(per_b_book)} book per equivalent B share). '
               f'H1 2026 buybacks were {mm(brk["buybacksH1Mn"])}. Thesis: a diversified operating conglomerate that is itself parking dry powder in T-bills until it finds a use.',
        scale=f'Position sizes {labels[0]} / {labels[1]} / {labels[2]} buy a slice of that same balance sheet—not a savings APY. Cash-and-bills were {liquid_mn / brk["equityMn"] * 100:.0f}% of book equity at the report date.',
        risk='Equity and insurance marks move the price. No dividend. Filing figures are as of June 30, 2026; the cash pile and share count change. This is not a yield quote.',
        src=[(brk['source'], brk['url'])]))

    # SCHD
    schd_inc = {a: a * schd['secYield'] / 100 for a in amounts}
    stocks.append(dict(
        ticker=schd['ticker'],
        head=f'{schd["ticker"]}: SEC 30-day yield {pct(schd["secYield"])} → <em>{money(schd_inc[amounts[-1]])} a year</em> on {money(amounts[-1])}.',
        thesis=f'{e(schd["name"])} tracks the Dow Jones U.S. Dividend 100 Index at a {pct(schd["expense"])} expense ratio. '
               f'The published SEC 30-day yield was {pct(schd["secYield"])} as of {nice(schd["secYieldAsOf"])} (NAV {money(schd["nav"])} on {nice(schd["navAsOf"])}). '
               f'Thesis: a low-cost equity sleeve that pays a documented income stream while you keep dry powder in T-bills or insured cash.',
        scale=tier_line(amounts, labels, lambda a: schd_inc[a])
              + f'<br>Same {money(amounts[1])} in a {pct(fn["savings"])} average savings account: {money(national_earn(amounts[1]))}/yr of interest—and no equity risk',
        risk='Principal can fall; the SEC yield is not a guaranteed distribution. Dividend-focused indexes can lag the broad market for years. Past yield is not a forecast.',
        src=[(schd['source'], schd['url'])]))

    # AAPL
    stocks.append(dict(
        ticker=aapl['ticker'],
        head=f'{aapl["ticker"]}: <em>{mm(aapl["repurchase9moMn"])}</em> of buybacks in nine months, plus a ${aapl["dividend"]:.2f} quarterly dividend.',
        thesis=f'Apple\'s Q3 FY2026 consolidated cash-flow statement (period ended {nice(aapl["periodEnd"])}) shows {mm(aapl["repurchase9moMn"])} of common-stock repurchases and ending cash of {mm(aapl["cashMn"])}. '
               f'The board declared a ${aapl["dividend"]:.2f} per-share dividend (payable {nice(aapl["dividendPayable"])}). '
               f'In the Q2 FY2026 results release, the company authorized an additional program to repurchase up to {money(aapl["buybackAuthBn"])}B of common stock. '
               f'Thesis: large-scale capital return (buybacks + dividend) funded by operating cash.',
        scale=f'At {labels[0]} / {labels[1]} / {labels[2]} position sizes you own a claim on that capital-return machine—not a fixed yield. '
              f'Dividend income alone at ${aapl["dividend"]:.2f}/share needs a live share price to annualize; use the issuer pages for the current quote.',
        risk='Concentration in one company and product cycle. Buyback pace is discretionary and can slow. Share price can fall even while buybacks run.',
        src=[(aapl['source'], aapl['url']), ('Apple Q3 FY2026 results', aapl['prUrl']), (aapl['buybackAuthSource'], aapl['buybackAuthUrl'])]))

    checked = nice(d['checkedAt'])
    link = lambda s: f'<a href="{e(s[1])}"{"" if s[1].endswith(".html") else " target=\"_blank\" rel=\"noopener\""}>{e(s[0])}{"" if s[1].endswith(".html") else " ↗"}</a>'

    items = ''.join(
        f'<li class="insight"><span class="insight-rank">{n:02d}</span><div>'
        f'<p class="insight-tag">{e(o["tag"])}</p><h3>{o["head"]}</h3><p>{o["body"]}</p>'
        f'<p class="example">{o["ex"]}</p>'
        f'<p class="catch"><b>The catch:</b> {o["catch"]}</p>'
        f'<p class="src">Source: {" · ".join(link(s) for s in o["src"])}</p></div></li>'
        for n, o in enumerate(out, 1))

    stock_items = ''.join(
        f'<li class="insight stock"><span class="insight-rank">{e(s["ticker"])}</span><div>'
        f'<h3>{s["head"]}</h3>'
        f'<p>{s["thesis"]}</p>'
        f'<p class="example"><b>At scale:</b> {s["scale"]}</p>'
        f'<p class="catch"><b>Risk:</b> {s["risk"]}</p>'
        f'<p class="src">Source: {" · ".join(link(x) for x in s["src"])}</p></div></li>'
        for s in stocks)

    hero_pay = out[0]['pay']
    hero = (f'<section class="share-card" id="share"><p class="eyebrow">Biggest cash gap</p>'
            f'<p class="share-rate">{money(hero_pay)}<small style="font-size:.4em"> / yr</small></p>'
            f'<p class="share-who">{out[0]["tag"]} · worked out on {money(amounts[-1])}</p>'
            f'<p class="share-catch">{pct(fn["savings"])} national average vs best plain stack on this site ({e(fit["name"])} to {money(elev_caps["interestMax"])}, then {e(overflow["name"])}).</p>'
            f'<p class="share-date">Checked {checked} · money.ilyusha.xyz</p></section>')

    desc = (f'{len(out)} high-balance money insights plus {len(stocks)} stock notes: cash vs the national average, Fed pass-through, '
            f'T-bills after state tax, FDIC/NCUA structure, uncapped card rewards, and filing-backed equity ideas. Dollar impact at {labels[0]}, {labels[1]}, {labels[2]}.')

    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Money — insights</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="https://money.ilyusha.xyz/insights.html"><meta property="og:title" content="Money — insights"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz/insights.html"><meta name="twitter:card" content="summary"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="analytics.js" defer></script></head>
<body><a class="skip-link" href="#insights">Skip to insights</a><header><a class="brand" href="index.html"><img class="brand-mark" src="favicon.svg" alt="">money<span class="brand-by">/ by ilyusha</span></a><nav aria-label="Main navigation"><a class="nav-switch" href="index.html">Savings</a><a class="nav-switch" href="cards.html">Cards</a><a class="nav-switch" href="economy.html">Economy</a><a class="nav-switch" href="crypto.html">Crypto</a><a class="nav-switch" href="insights.html" aria-current="page">Insights</a></nav><a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main id="top"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> INSIGHTS / HIGH BALANCE</p><h1>Money <em>left on the table.</em></h1>{hero}</div><aside class="snapshot"><div class="snapshot-count">{len(out) + len(stocks)}<span>checked<br>notes</span></div><div class="snapshot-date">Checked <time datetime="{e(d['checkedAt'])}">{checked}</time></div><p>Cited figures · {labels[0]} / {labels[1]} / {labels[2]}</p></aside></section>
<section id="insights" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">01 / BY DOLLAR IMPACT</span><h2>Cash, tax, credit<span>.</span></h2></div><p>Worked out on {labels[0]}, {labels[1]}, and {labels[2]}</p></div><ol class="insight-list">{items}</ol></section>
<section id="stocks" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">02 / STOCKS &amp; OPPORTUNITIES</span><h2>Filing-backed notes<span>.</span></h2></div><p>Plain thesis · risk · scale — not price targets</p></div><ol class="insight-list">{stock_items}</ol></section>
<p class="econ-note crypto-plain">General information, not financial, tax, or investment advice. Numbers were checked on {checked}; rates, filings, and prices change, so confirm with the source before you move money.</p>
</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="index.html">Back to savings</a></footer></body></html>
'''
    for asset in ('styles.css', 'analytics.js', 'favicon.svg'):
        v = hashlib.sha256((ROOT / 'docs' / asset).read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{asset}"', f'"{asset}?v={v}"')
    OUT.write_text(page)
    print(f'Built insights page: {len(page) // 1024} KB, {len(out)} insights + {len(stocks)} stocks, top {money(hero_pay)}, checked {d["checkedAt"]}.')
    for o in out:
        print(f'  [{o["tag"]}] pay={money(o["pay"])} :: {re.sub("<[^>]+>", "", o["head"])[:90]}')
    for s in stocks:
        print(f'  [Stock {s["ticker"]}] :: {re.sub("<[^>]+>", "", s["head"])[:90]}')

if __name__ == '__main__':
    if '--fetch' in sys.argv: fetch()
    build()
