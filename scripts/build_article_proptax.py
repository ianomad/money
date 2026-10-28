"""Write docs/pay-property-tax-credit-card.html: is paying CA property tax by card worth it?

Data only from data/proptax_fees.json (county fees, each with its source URL), data/cards.json
(earn rates, bonuses, pointValue) and data/rates.json (top plain savings APY for the float math).
Called from compose.py after build_article_nofee_cards (same write() signature).
"""
import json
import re
from datetime import date
from digest import topcard, e
import pages2

TRUST_CSS = '<style>.trust{font:12px/1.5 var(--mono);color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px}.trust b{color:#2f6b45;font-weight:600}</style>'
PATH = '/pay-property-tax-credit-card'
FILE = 'pay-property-tax-credit-card.html'
BILL = 10000  # example installment, labeled as an example on the page
FLOAT_DAYS = (25, 50)  # roughly: paid right before statement close vs right after it


def _nice(iso):
    return date.fromisoformat(iso).strftime('%b %-d, %Y')


def _usd(v, cents=False):
    v = round(v, 2) if cents else round(v)
    s = f'{abs(v):,.2f}' if cents else f'{abs(v):,.0f}'
    return ('-$' if v < 0 else '$') + s


def _sgn(v):
    return ('+' if v >= 0 else '') + _usd(v)


def _pct(v):
    return f'{v:g}%'


def _name(c):
    u = c.get('url')
    return f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">{e(c["name"])}</a>' if u else e(c['name'])


def _bonus(card, point_value):
    """(bonus $, min spend $) parsed from cards.json text; None if not a simple spend bonus."""
    b = card.get('bonus') or ''
    m = re.match(r'^\$([\d,]+) after \$([\d,]+)', b)
    if m:
        return float(m.group(1).replace(',', '')), float(m.group(2).replace(',', ''))
    m = re.match(r'^([\d,]+) points.*?after \$([\d,]+)', b)
    if m and card.get('type') != 'rent':
        return float(m.group(1).replace(',', '')) * point_value, float(m.group(2).replace(',', ''))
    return None


def build(root):
    pj = json.loads((root / 'data' / 'proptax_fees.json').read_text())
    cj = json.loads((root / 'data' / 'cards.json').read_text())
    rj = json.loads((root / 'data' / 'rates.json').read_text())
    checked = _nice(pj['checkedAt'])
    counties = sorted(pj['counties'], key=lambda c: c['creditPct'])
    lo, hi = counties[0]['creditPct'], counties[-1]['creditPct']
    hi_c = counties[-1]
    pv = cj.get('pointValue', 0.01)

    flat = [c for c in cj['cards'] if c.get('type') == 'cash' and (c.get('fee') or 0) == 0
            and set((c.get('earn') or {}).keys()) == {'other'} and (c['earn']['other'] == 2)
            and 'Apple Pay' not in (c.get('earnText') or '')]
    flat_rate = 2
    rh = next((c for c in cj['cards'] if c['id'] == 'rh'), None)
    rh_rate = (rh['earn']['other'] if rh else None)

    cash = [p for p in rj['providers'] if p.get('category') == 'cash' and p.get('base') is not None]
    plain = sorted([p for p in cash if p.get('boost') is None and (p.get('fdic') or {}).get('status') == 'bank'
                    and 'paused' not in (p.get('rateLabel') or '').lower()], key=lambda p: -p['base'])
    top = plain[0] if plain else None

    fee_hi = BILL * hi / 100
    flat_net = BILL * flat_rate / 100 - fee_hi
    floats = [BILL * top['base'] / 100 * d / 365 for d in FLOAT_DAYS] if top else None

    # --- Head ---
    lead = (f'California counties charge {_pct(lo)}–{_pct(hi)} to pay property tax by card; eCheck is free. '
            f'A plain {_pct(flat_rate)} card loses money on that trade: on a {_usd(BILL)} installment in {e(hi_c["county"])} County, '
            f'the fee is {_usd(fee_hi)} and you get {_usd(BILL * flat_rate / 100)} back ({_sgn(flat_net)}). '
            'It only pays when the card earns more than the fee, when the bill unlocks a sign-up bonus, or when you are in a tight spot and need a few weeks.')
    head = ('<section class="pagehead"><p class="eyebrow">PROPERTY TAX / CHECKED ' + e(checked.upper()) + '</p>'
            '<h1>Paying property tax by credit card: <em>when the fee is worth it.</em></h1>'
            f'<p class="lead">{lead}</p></section>')

    bars = [(c['county'], c['creditPct'], _pct(c['creditPct']), '#fees') for c in counties]
    bars.append(('eCheck (all)', 0, '0%', '#fees'))
    card = topcard('Default answer', 'eCheck', 'Pay from checking, free in every county here',
                   f'A card only makes sense in the three cases below. Example bill: {_usd(BILL)} installment.',
                   f'Checked {checked}', [('Card fee range', f'{_pct(lo)}–{_pct(hi)}'), ('eCheck', '$0')],
                   ('County fee table', '#fees'), bars, 'Card convenience fee by county')

    # --- County fees ---
    rows = ''.join(
        f'<tr><td><a href="{e(c["source"])}" rel="nofollow noopener" target="_blank">{e(c["county"])} County</a>'
        f'<small>{e(c["debit"])}' + (f'; minimum {_usd(c["minFee"], True)}' if c.get('minFee') else '') + '</small></td>'
        f'<td class="n">{_pct(c["creditPct"])}</td><td class="n">{_usd(BILL * c["creditPct"] / 100)}</td><td class="n">$0</td></tr>'
        for c in counties)
    dd = pj.get('dueDates') or {}
    fees_s = ('<section class="digest" id="fees"><p class="eyebrow"><span class="dot"></span> WHAT EACH COUNTY CHARGES</p>'
              f'<h2 class="takeaway">The card fee goes to the payment processor, not to a perk for you. On {_usd(BILL)} it runs '
              f'{_usd(BILL * lo / 100)}–{_usd(BILL * hi / 100)}.</h2>'
              '<table class="ctable"><thead><tr><th>County · source</th><th style="text-align:right">Card fee</th>'
              f'<th style="text-align:right">On {_usd(BILL)}</th><th style="text-align:right">eCheck</th></tr></thead>'
              f'<tbody>{rows}</tbody></table>'
              + (f'<p>Installments are due {e(dd["first"])} and {e(dd["second"])}. Debit cards get charged the same percentage in most of these counties, '
                 'so paying by debit card is the worst option: you pay the fee and earn almost nothing.</p>' if dd else '')
              + '</section>')

    # --- Case 1: earn above the fee ---
    c1 = ''
    if rh:
        rows = ''.join(
            f'<tr><td>{e(c["county"])}</td><td class="n">{_sgn(BILL * flat_rate / 100 - BILL * c["creditPct"] / 100)}</td>'
            f'<td class="n">{_sgn(BILL * rh_rate / 100 - BILL * c["creditPct"] / 100)}</td></tr>' for c in counties)
        c1 = ('<section class="digest" id="earn"><p class="eyebrow"><span class="dot"></span> CASE 1 · THE CARD EARNS MORE THAN THE FEE</p>'
              f'<h2 class="takeaway">A {_pct(rh_rate)} card clears every county fee; a {_pct(flat_rate)} card clears none.</h2>'
              f'<p>{_name(rh)} pays {_pct(rh_rate)} on everything, but it needs a Robinhood Gold membership ({e(_usd(rh.get("fee") or 0))}/yr in our data). On a {_usd(BILL)} installment that is '
              f'{_usd(BILL * rh_rate / 100)} back against a {_usd(BILL * lo / 100)}–{_usd(BILL * hi / 100)} fee. Only count it as a win if you already pay for Gold; '
              'buying the membership just for this eats most of the gain on a single installment.</p>'
              '<table class="ctable"><thead><tr><th>County</th>'
              f'<th style="text-align:right">Flat {_pct(flat_rate)} net</th><th style="text-align:right">{_pct(rh_rate)} card net</th></tr></thead>'
              f'<tbody>{rows}</tbody></table>'
              + (f'<p>Flat {_pct(flat_rate)} cards in our data: {", ".join(_name(c) for c in flat)}. All lose a little here.</p>' if flat else '')
              + '</section>')

    # --- Case 2: sign-up bonus ---
    bcards = []
    for c in cj['cards']:
        b = _bonus(c, pv)
        if b:
            val, spend = b
            cost = spend * hi / 100
            bcards.append((c, val, spend, cost, val - cost))
    bcards.sort(key=lambda t: -t[4])
    brow = ''.join(
        f'<tr><td>{_name(c)}<small>{e(c["bonus"])}' + (f'; annual fee ${c["fee"]:,}' if c.get('fee') else '; no annual fee') + '</small></td>'
        f'<td class="n">{_usd(cost)}</td><td class="n">{_usd(val)}</td><td class="n">{_sgn(net)}</td></tr>'
        for c, val, spend, cost, net in bcards)
    c2 = ('<section class="digest" id="bonus"><p class="eyebrow"><span class="dot"></span> CASE 2 · THE BILL UNLOCKS A SIGN-UP BONUS</p>'
          '<h2 class="takeaway">This is where card payment really pays: a few dollars of fee can unlock a few hundred dollars of bonus.</h2>'
          f'<p>If a new card wants a minimum spend you would not hit with normal spending, putting just that much of the tax on it costs the fee on the minimum only. '
          f'Fee below uses the highest county rate ({_pct(hi)}); points valued at {round(pv * 100, 2):g}¢ each, as on our Cards page. '
          'Annual fees are not subtracted because they are a separate decision about keeping the card.</p>'
          '<table class="ctable"><thead><tr><th>Card · bonus terms</th><th style="text-align:right">Fee on min spend</th>'
          '<th style="text-align:right">Bonus worth</th><th style="text-align:right">Net</th></tr></thead>'
          f'<tbody>{brow}</tbody></table>'
          '<p>Pay only the minimum by card and the rest by eCheck. Check the issuer’s terms that tax payments count toward the bonus before you rely on it.</p></section>') if bcards else ''

    # --- Case 3: float ---
    c3 = ''
    if top and floats:
        c3 = ('<section class="digest" id="float"><p class="eyebrow"><span class="dot"></span> CASE 3 · YOUR CASH EARNS INTEREST A FEW WEEKS LONGER</p>'
              f'<h2 class="takeaway">The float is real but small: {_usd(floats[0])}–{_usd(floats[1])} on {_usd(BILL)}, enough to turn a {_pct(flat_rate)} card from a small loss into about break-even.</h2>'
              f'<p>Paying by card on the due date means the cash leaves your account at the statement due date instead, roughly {FLOAT_DAYS[0]}–{FLOAT_DAYS[1]} days later depending on when your statement closes. '
              f'At the highest plain savings rate we track ({_pct(top["base"])}, {e(top["name"])}), that is {_usd(floats[0])}–{_usd(floats[1])} of extra interest. '
              f'Added to a flat {_pct(flat_rate)} card in {e(hi_c["county"])} ({_sgn(flat_net)}), you land around {_sgn(flat_net + floats[0])} to {_sgn(flat_net + floats[1])}: basically a wash for the hassle. '
              'If you would carry the balance even one month, card interest wipes out every case on this page.</p></section>')

    pick_s = ('<section class="digest" id="pick"><p class="eyebrow"><span class="dot"></span> HOW TO DECIDE</p>'
              '<h2 class="takeaway">Default to eCheck. Use a card only for a bonus minimum or a card that earns over the fee.</h2><ul>'
              '<li><b>Opening a new card soon:</b> put exactly the bonus minimum on it, eCheck the rest.</li>'
              + (f'<li><b>Already pay for {e(rh["name"].replace(" Card", ""))}:</b> {_pct(rh_rate)} beats every county fee here.</li>' if rh else '')
              + f'<li><b>Flat {_pct(flat_rate)} card, no bonus in play:</b> skip it; you pay to use the card.</li>'
              '<li><b>Short on cash before the deadline:</b> a card avoids the late penalty, but only if you can pay the statement in full.</li>'
              '</ul></section>')

    foot = ('<section class="digest" id="more"><p class="eyebrow"><span class="dot"></span> SOURCES</p>'
            f'<p>County fees are from each tax collector’s site (linked in the table, checked {checked}). Card rates and bonuses are from our Cards data '
            f'(checked {_nice(cj["checkedAt"])}); the savings rate is from our Rates data (checked {_nice(rj["checkedAt"])}). Confirm on the county and issuer sites before you pay; fees and offers change.</p>'
            '<p><a href="/best-nofee-cards">Best no-fee cards</a> · <a href="/best-hysa">Best no-strings savings</a> · <a href="/disclosure">How this site makes money</a>. '
            'No links on this page pay us. This is general information, not tax or financial advice.</p></section>')

    body = ('<p class="trust"><span><b>●</b> Checked ' + e(checked) + '</span><span>County fees with sources</span>'
            '<span>No sponsored rankings</span></p>' + head + card + fees_s + c1 + c2 + c3 + pick_s + foot)
    title = f'Pay California property tax by credit card? Fees vs rewards ({date.fromisoformat(pj["checkedAt"]).strftime("%b %Y")})'
    desc = (f'CA counties charge {_pct(lo)}–{_pct(hi)} to pay property tax by card; eCheck is free. A 2% card loses money, '
            f'a {_pct(rh_rate) if rh else "3%"} card or a sign-up bonus minimum can win. County-by-county math with sources.')
    return title, desc, body


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    title, desc, body = build(D.parent)
    (D / FILE).write_text(
        finalize(lazyimg(page(title, desc, PATH, 'x', body, pages2.CSS + TRUST_CSS + DIGEST_CSS + UI_CSS))))
    h = rd('cards.html')
    if f'href="{PATH}"' not in h:
        old = '<a href="/sponsor">Sponsor</a> · '
        if old in h:
            (D / 'cards.html').write_text(h.replace(old, f'<a href="{PATH}">Property tax by card</a> · {old}', 1))
