"""Write docs/tbills-vs-savings-california.html: T-bills vs high-yield savings after CA state tax.

Data only from data/tbills.json (Treasury daily bill rates), data/ca_tax.json (FTB 2025 rate schedule)
and data/rates.json (top plain savings APY). Called from compose.py (same write() signature).
"""
import json
from datetime import date
from digest import topcard, e
import pages2

TRUST_CSS = '<style>.trust{font:12px/1.5 var(--mono);color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px}.trust b{color:#2f6b45;font-weight:600}</style>'
PATH = '/tbills-vs-savings-california'
FILE = 'tbills-vs-savings-california.html'
AMTS = (10000, 50000)
MAIN = 9.3  # most common CA bracket for savers with real balances; shown alongside all others


def _nice(iso):
    return date.fromisoformat(iso).strftime('%b %-d, %Y')


def _usd(v):
    return ('-$' if v < 0 else '$') + f'{abs(round(v)):,.0f}'


def _sgn(v):
    return ('+' if v >= 0 else '') + _usd(v)


def _p(v):
    return f'{v:.2f}%'


def build(root):
    tb = json.loads((root / 'data' / 'tbills.json').read_text())
    tx = json.loads((root / 'data' / 'ca_tax.json').read_text())
    rj = json.loads((root / 'data' / 'rates.json').read_text())
    cash = [p for p in rj['providers'] if p.get('category') == 'cash' and p.get('base') is not None]
    plain = sorted([p for p in cash if p.get('boost') is None and (p.get('fdic') or {}).get('status') == 'bank'
                    and 'paused' not in (p.get('rateLabel') or '').lower()], key=lambda p: -p['base'])
    top = plain[0]
    sav = top['base']
    terms = tb['terms']
    bterm = '26 Weeks' if '26 Weeks' in terms else max(terms, key=terms.get)
    bill = terms[bterm]
    bdate = _nice(tb['date'])
    s = MAIN / 100
    kept = sav * (1 - s)
    gap = bill - kept
    need = bill / (1 - s)
    nice_term = bterm.lower().replace('weeks', 'week')

    win = gap > 0
    lead = (f'Treasury bill interest is exempt from California income tax; savings interest is not. '
            f'In the {MAIN:g}% bracket, the best plain savings rate we track ({_p(sav)}, {e(top["name"])}) keeps {_p(kept)} after state tax, '
            f'while a {nice_term} T-bill at {_p(bill)} keeps all of it. '
            + (f'That is {_usd(AMTS[0] * gap / 100)} a year more per {_usd(AMTS[0])}, and a savings account would need about {_p(need)} to match.'
               if win else f'Savings still edges ahead by {_usd(-AMTS[0] * gap / 100)} a year per {_usd(AMTS[0])}.'))
    head = ('<section class="pagehead"><p class="eyebrow">T-BILLS VS SAVINGS / CALIFORNIA / ' + e(bdate.upper()) + '</p>'
            '<h1>T-bills vs high-yield savings in California: <em>the state tax decides it.</em></h1>'
            f'<p class="lead">{lead}</p></section>')

    bars = [(f'{c["rate"]:g}% bracket', round(bill - sav * (1 - c['rate'] / 100), 2), _p(bill - sav * (1 - c['rate'] / 100)) + ' pts', '#brackets')
            for c in tx['brackets']]
    card = topcard('In the ' + f'{MAIN:g}% bracket', 'T-bill' if win else 'Savings',
                   f'{nice_term} bill {_p(bill)} vs savings {_p(sav)} → {_p(kept)} after CA tax',
                   f'Need a savings rate of {_p(need)} to tie. Federal tax hits both the same, so it drops out.',
                   f'Treasury {bdate}', [('Bill keeps', _p(bill)), ('Savings keeps', _p(kept))],
                   ('Every bracket', '#brackets'), bars, 'T-bill advantage after CA tax, by bracket')

    rows = ''.join(
        f'<tr><td>{c["rate"]:g}%<small>single {e(c["single"])}; joint {e(c["joint"])}</small></td>'
        f'<td class="n">{_p(sav * (1 - c["rate"] / 100))}</td><td class="n">{_p(bill / (1 - c["rate"] / 100))}</td>'
        + ''.join(f'<td class="n">{_sgn(a * (bill - sav * (1 - c["rate"] / 100)) / 100)}</td>' for a in AMTS) + '</tr>'
        for c in tx['brackets'])
    br = ('<section class="digest" id="brackets"><p class="eyebrow"><span class="dot"></span> BY CALIFORNIA TAX BRACKET</p>'
          f'<h2 class="takeaway">Compared with a {_p(bill)} {nice_term} bill and {_p(sav)} savings. The higher your bracket, the bigger the bill’s edge.</h2>'
          '<table class="ctable"><thead><tr><th>CA bracket · taxable income</th><th style="text-align:right">Savings keeps</th>'
          '<th style="text-align:right">Savings rate to tie</th>'
          + ''.join(f'<th style="text-align:right">Bill edge / yr on {_usd(a)}</th>' for a in AMTS) + '</tr></thead>'
          f'<tbody>{rows}</tbody></table>'
          f'<p>Brackets are from the FTB’s {tx["year"]} rate schedules (<a href="{e(tx["source"])}" rel="nofollow noopener" target="_blank">PDF</a>). '
          'Your bracket is the rate on your last dollar of California taxable income, not your average rate. Below about $26k single / $52k joint (1–2% brackets) the difference is a few dollars.</p></section>')

    trows = ''.join(f'<tr><td>{e(k.lower())}</td><td class="n">{_p(v)}</td><td class="n">{_p(v - kept)}</td></tr>' for k, v in terms.items())
    tm = ('<section class="digest" id="terms"><p class="eyebrow"><span class="dot"></span> WHICH BILL</p>'
          f'<h2 class="takeaway">Every bill term beats {_p(kept)} right now; longer terms pay a little more but lock the cash longer.</h2>'
          f'<table class="ctable"><thead><tr><th>Bill term</th><th style="text-align:right">Yield</th><th style="text-align:right">vs savings after {MAIN:g}% CA tax</th></tr></thead>'
          f'<tbody>{trows}</tbody></table>'
          f'<p>Yields are Treasury’s coupon-equivalent rates for {bdate} (<a href="{e(tb["source"])}" rel="nofollow noopener" target="_blank">source</a>). '
          'Savings rates are APYs, which already include compounding; a bill yield does not, so rolling bills over earns slightly more than the yield shown. If anything, this table understates the bill.</p></section>')

    catch = ('<section class="digest" id="catches"><p class="eyebrow"><span class="dot"></span> THE CATCHES</p>'
             '<h2 class="takeaway">Bills win on rate, savings wins on access. Split by when you need the money.</h2><ul>'
             '<li><b>Access:</b> savings is same-day. A bill is locked until it matures unless you sell it at a brokerage (at market price); at TreasuryDirect you wait.</li>'
             '<li><b>Rate moves:</b> a bill locks today’s yield for its term; a savings rate can change any day, in either direction.</li>'
             '<li><b>Itemizers:</b> state tax you pay on savings interest can be deducted federally if you are under the SALT cap, which shaves a bit off the bill’s edge.</li>'
             '<li><b>Teaser savings rates:</b> a temporary promo rate can still beat a bill while it lasts. See <a href="/best-hysa">best no-strings savings</a> for the plain rates and the catches.</li>'
             '</ul><p>Keep your emergency fund in savings; put cash you will not touch for 1–6 months into bills.</p></section>')

    foot = ('<section class="digest" id="more"><p class="eyebrow"><span class="dot"></span> SOURCES</p>'
            f'<p>T-bill yields: U.S. Treasury daily bill rates ({bdate}, refreshed daily). Savings rate: our Rates data (checked {_nice(rj["checkedAt"])}). '
            f'California brackets: FTB {tx["year"]} rate schedules. Treasury interest is exempt from state income tax under federal law (31 U.S.C. 3124); bank savings interest is taxed by California.</p>'
            '<p><a href="/best-hysa">Best no-strings savings</a> · <a href="/pay-property-tax-credit-card">Property tax by card</a> · <a href="/disclosure">How this site makes money</a>. '
            'No links on this page pay us. General information, not tax or financial advice.</p></section>')

    body = ('<p class="trust"><span><b>●</b> Treasury yields ' + e(bdate) + '</span><span>FTB brackets</span>'
            '<span>No sponsored rankings</span></p>' + head + card + br + tm + catch + foot)
    title = f'T-bills vs high-yield savings in California after state tax ({date.fromisoformat(tb["date"]).strftime("%b %Y")})'
    desc = (f'T-bill interest skips California tax. In the {MAIN:g}% bracket a {_p(sav)} savings account keeps {_p(kept)}; '
            f'a {_p(bill)} {nice_term} bill keeps it all. Bracket-by-bracket math from Treasury and FTB data.')
    return title, desc, body


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    title, desc, body = build(D.parent)
    (D / FILE).write_text(
        finalize(lazyimg(page(title, desc, PATH, 'x', body, pages2.CSS + TRUST_CSS + DIGEST_CSS + UI_CSS))))
