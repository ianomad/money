"""Write docs/best-hysa.html: best no-strings US high-yield savings, from data/rates.json only.

Called from compose.py after build_sponsor/build_legal (same write() signature). Also adds a footer
link on cards.html (index/markets/sponsor/legal get it from compose.page()).
"""
import json, re
from datetime import date
from digest import topcard, e
import pages2

# ui3.ui4 skips its CSS when a page brings its own trust line, so carry the trust-line style here.
TRUST_CSS = '<style>.trust{font:12px/1.5 var(--mono);color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px}.trust b{color:#2f6b45;font-weight:600}</style>'
FALLBACK_FDIC = None  # never invent the national average; skip the comparison if insights.json lacks it


def _nice(iso):
    return date.fromisoformat(iso).strftime('%b %-d, %Y')


def _usd(v):
    return f'${v:,.0f}'


def _pct(v):
    return f'{v:.2f}%'


def _src(p):
    s = p.get('sources') or []
    return s[0]['url'] if s else None


def _name(p):
    u = _src(p)
    return f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">{e(p["name"])}</a>' if u else e(p['name'])


def _insurer(p):
    return (p.get('fdic') or {}).get('summary', '').split(';')[0].strip()


def _fee_per_year(p):
    """Membership cost stated in the provider's own text in rates.json, if any."""
    txt = ' '.join(str(p.get(k) or '') for k in ('requirements', 'details'))
    m = re.search(r'\$(\d+(?:\.\d+)?)/month', txt)
    if m:
        return float(m.group(1)) * 12
    m = re.search(r'\$(\d[\d,]*)/yr', txt)
    if m:
        return float(m.group(1).replace(',', ''))
    return None


def _cap(p):
    m = re.search(r'first \$([\d,]+)', p.get('requirements') or '')
    return float(m.group(1).replace(',', '')) if m else None


def build(root):
    rj = json.loads((root / 'data' / 'rates.json').read_text())
    try:
        fn = json.loads((root / 'data' / 'insights.json').read_text())['inputs']['fdicNational']
    except Exception:
        fn = FALLBACK_FDIC
    checked = _nice(rj['checkedAt'])
    cash = [p for p in rj['providers'] if p.get('category') == 'cash' and p.get('base') is not None]
    paused = [p for p in cash if 'paused' in (p.get('rateLabel') or '').lower()]
    # Plain = one published rate for everyone who opens: insured bank deposit, no boost / tier / promo / membership.
    plain = sorted([p for p in cash if p.get('boost') is None and (p.get('fdic') or {}).get('status') == 'bank' and p not in paused],
                   key=lambda p: -p['base'])
    top = plain[0]
    short = [p for p in plain if p['base'] >= 4.0] or plain[:4]
    brands = [p for p in plain if p not in short]
    # Headline-with-catches = any cash product whose best rate beats the top plain rate only with conditions.
    catches = sorted([p for p in cash if (p.get('boost') or 0) > top['base']], key=lambda p: -p['boost'])

    nat = fn['savings'] if fn else None
    lead_math = ''
    if nat is not None:
        lead_math = (f' On $10,000 that is {_usd(10000 * top["base"] / 100)} a year instead of {_usd(10000 * nat / 100)}.')
    head = ('<section class="pagehead"><p class="eyebrow">SAVINGS / CHECKED ' + e(checked.upper()) + '</p>'
            '<h1>The best savings rates <em>with no strings.</em></h1>'
            '<p class="lead">' + (f'The average US savings account pays {_pct(nat)}. ' if nat is not None else '')
            + f'The best plain account we checked pays {_pct(top["base"])}, with no promo clock, no membership, and no direct deposit.{lead_math}</p></section>')

    bars = [(p['name'], p['base'], _pct(p['base']), '#plain') for p in (short + brands[:2])]
    if nat is not None:
        bars.append(('US average', nat, _pct(nat), '#gap'))
    bars += [(p['name'], p['base'], _pct(p['base']), '#plain') for p in brands if p['base'] < 1][:1]
    card = topcard('Top no-strings rate', _pct(top['base']), f'{top["name"]} · {top["product"]}', top['requirements'],
                   f'Checked {checked}', [('Insured', 'FDIC · ' + _insurer(top))], ('Full rate table', '/rates'), bars,
                   'Plain savings APY, no conditions')

    gap = ''
    if nat is not None:
        rows = ''
        for bal in (10000, 50000):
            a, b = bal * top['base'] / 100, bal * nat / 100
            rows += (f'<tr><td>{_usd(bal)}<small>{e(top["name"])} {_pct(top["base"])} vs {_pct(nat)} average</small></td>'
                     f'<td class="n">{_usd(a)}/yr</td><td class="n">{_usd(b)}/yr</td><td class="n">+{_usd(a - b)}</td></tr>')
        low = min(plain, key=lambda p: p['base'])
        gap = ('<section class="digest" id="gap"><p class="eyebrow"><span class="dot"></span> THE GAP</p>'
               f'<h2 class="takeaway">Same FDIC insurance, about {top["base"] / nat:.0f}× the interest.</h2>'
               f'<p>The FDIC puts the national average savings rate at {_pct(nat)} (as of {_nice(fn["asOf"])}). That is an average across all banks, so a given bank may pay more or less. '
               f'Big branch banks sit near the bottom: {e(low["name"])} {e(low["product"])} pays {_pct(low["base"])}.</p>'
               '<table class="ctable"><thead><tr><th>Balance</th><th style="text-align:right">Top plain</th><th style="text-align:right">US average</th><th style="text-align:right">Extra</th></tr></thead>'
               f'<tbody>{rows}</tbody></table>'
               '<p><small>One year of interest at today’s APY. Rates are variable and can change any time.</small></p>'
               f'<p class="src"><small>Source: <a href="{e(fn["url"])}" rel="noopener" target="_blank">{e(fn["source"])} ↗</a></small></p></section>')

    prow = ''.join(
        f'<tr><td>{_name(p)}<small>{e(p["product"])} · {e(p.get("baseLabel") or p.get("rateLabel") or "")}</small>'
        f'<small>{e(p["requirements"])}</small><small>FDIC · {e(_insurer(p))}</small></td><td class="n">{_pct(p["base"])}</td></tr>'
        for p in short)
    brand_txt = ', '.join(f'{e(p["name"])} {_pct(p["base"])}' for p in brands)
    paused_txt = ''.join(f' {e(p["name"])} publishes {_pct(p["base"])} but is not taking new applications, so it is left out.' for p in paused)
    plain_s = ('<section class="digest" id="plain"><p class="eyebrow"><span class="dot"></span> NO STRINGS</p>'
               f'<h2 class="takeaway">{len(short)} accounts pay {_pct(short[-1]["base"])} or more just for holding cash.</h2>'
               '<p>No referral, no subscription, no direct deposit, no promo that expires. Open, fund, earn.</p>'
               '<table class="ctable"><thead><tr><th>Account · what to know</th><th style="text-align:right">APY</th></tr></thead>'
               f'<tbody>{prow}</tbody></table>'
               + (f'<p>The names you know pay less: {brand_txt}.{paused_txt}</p>' if brands else (f'<p>{paused_txt.strip()}</p>' if paused_txt else ''))
               + '</section>')

    def worth(p):
        fee, b = _fee_per_year(p), p['boost']
        if p['id'] == 'x-money' and fee and b > top['base']:
            be = fee / ((b - top['base']) / 100)
            ny = ' No interest at all for New York residents.' if 'New York' in (p.get('details') or '') else ''
            return (f'Free if your paycheck already lands there. Paying about {_usd(fee)}/yr for Premium+ just for the rate only beats '
                    f'{e(top["name"])}’s plain {_pct(top["base"])} above roughly {_usd(round(be, -2))}.{ny}')
        cap = _cap(p)
        if fee and cap:
            net = (cap * b / 100 - fee) / cap * 100
            return (f'The membership costs {_usd(fee)}/yr. On {_usd(cap)} that nets about {_pct(net)}, '
                    + ('below' if net < top['base'] else 'above') + f' the plain {_pct(top["base"])}.')
        if re.search(r'\b(3|three|six|6)[- ]month|six statement cycles|for six months|for 3 months', (p.get('requirements') or '') + ' ' + (p.get('rateLabel') or ''), re.I):
            q = re.search(r'qualifying savings earns ([\d.]+)%', p.get('details') or '')
            return (f'Temporary. After the boost it drops toward {_pct(p["base"])}'
                    + (f', or {_pct(float(q.group(1)))} if you keep qualifying' if q else (' (a bit more if you keep the recurring deposits)' if p['id'] == 'wealthfront' else ''))
                    + f', under the plain {_pct(top["base"])}.')
        return f'Falls to {_pct(p["base"])} if you miss the conditions.'

    crow = ''.join(
        f'<tr><td>{_name(p)}<small>{e(p["product"])} · {e(p.get("rateLabel") or "")}</small><small>{e(p["requirements"])}</small>'
        f'<small><b>What it is worth:</b> {worth(p)}</small><small>{e(p["fdic"]["label"])}</small></td>'
        f'<td class="n">{_pct(p["boost"])}<small>base {_pct(p["base"])}</small></td></tr>'
        for p in catches)
    catch_s = ('<section class="digest" id="catches"><p class="eyebrow"><span class="dot"></span> HEADLINE RATES, WITH CATCHES</p>'
               f'<h2 class="takeaway">Rates above {_pct(top["base"])} exist, but each one wants something from you.</h2>'
               '<p>A paycheck, a referral, a monthly fee, or a promo clock. Worth it if you already meet the condition. Not worth it if you have to change your life for it.</p>'
               '<table class="ctable"><thead><tr><th>Account · the catch</th><th style="text-align:right">Up to</th></tr></thead>'
               f'<tbody>{crow}</tbody></table></section>') if catches else ''

    cap_notes = [p for p in short if re.search(r'\$500,000', (p.get('requirements') or '') + (p.get('details') or ''))]
    pick_s = ('<section class="digest" id="pick"><p class="eyebrow"><span class="dot"></span> HOW TO PICK</p>'
              '<h2 class="takeaway">Most people need one boring account at the top of the plain list.</h2><ul>'
              f'<li><b>Want zero homework:</b> take the top plain rate. Rates are variable, so check again in a few months.</li>'
              '<li><b>Already have direct deposit you can point anywhere:</b> a conditional rate can be free money. Check the catches table above first.</li>'
              + (f'<li><b>Big balance:</b> {" and ".join(e(p["name"]) for p in cap_notes)} change{"s" if len(cap_notes) == 1 else ""} terms at $500,000 (see each row). '
                 'Above $250,000, spread money across banks to stay inside FDIC limits.</li>' if cap_notes else
                 '<li><b>Big balance:</b> above $250,000, spread money across banks to stay inside FDIC limits.</li>')
              + '</ul></section>')

    foot = ('<section class="digest" id="more"><p class="eyebrow"><span class="dot"></span> MORE</p>'
            f'<p>Every rate here was checked by hand against the bank’s own page; data last checked {checked}. Confirm on the provider’s site before you move money.</p>'
            '<p><a href="/">See the full Rates table →</a> · <a href="/disclosure">How this site makes money</a>. No links on this page pay us, and rankings are by rate, never by payout.</p></section>')
    body = ('<p class="trust"><span><b>●</b> Checked ' + e(checked) + '</span><span>Plain rates vs catches</span><span>No sponsored rankings</span></p>'
            + head + card + gap + plain_s + catch_s + pick_s + foot)
    title = f'Best no-strings high-yield savings rates ({date.fromisoformat(rj["checkedAt"]).strftime("%b %Y")}) — getmoneybeast.com'
    desc = (f'{top["name"]} pays {_pct(top["base"])} with no conditions'
            + (f' vs the {_pct(nat)} national average' if nat is not None else '')
            + '. Hand-checked US savings rates with no strings, and the catches behind 5%+ headlines.')
    return title, desc, body


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    title, desc, body = build(D.parent)
    (D / 'best-hysa.html').write_text(finalize(lazyimg(page(title, desc, '/best-hysa', 'x', body, pages2.CSS + TRUST_CSS + DIGEST_CSS + UI_CSS))))
    h = rd('cards.html')
    if 'href="/best-hysa"' not in h and '<a href="/sponsor">Sponsor</a> · ' in h:
        (D / 'cards.html').write_text(h.replace('<a href="/sponsor">Sponsor</a> · ',
                                                '<a href="/best-hysa">Best no-strings savings</a> · <a href="/sponsor">Sponsor</a> · ', 1))
