"""Write docs/best-nofee-cards.html: best no-fee cash-back cards, from data/cards.json only.

Called from compose.py after build_article_hysa (same write() signature). Also adds a footer
link on cards.html (index/markets/sponsor/legal get it from compose.page()).
"""
import json
from datetime import date
from digest import topcard, e
import pages2

TRUST_CSS = '<style>.trust{font:12px/1.5 var(--mono);color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px}.trust b{color:#2f6b45;font-weight:600}</style>'

CATS = ('dining', 'groceries', 'gas', 'travel', 'streaming', 'other')


def _nice(iso):
    return date.fromisoformat(iso).strftime('%b %-d, %Y')


def _usd(v):
    if v < 0:
        return f'-${abs(v):,.0f}'
    return f'${v:,.0f}'


def _pct(v):
    # Trim trailing zeros: 2 → 2%, 1.5 → 1.5%
    s = f'{v:g}'
    return s + '%'


def _name(c):
    u = c.get('url')
    return f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">{e(c["name"])}</a>' if u else e(c['name'])


def _annual_reward(card, profile):
    """Cash-back $ per year from earn rates (percent) and caps in cards.json. No invented rates."""
    earn = card.get('earn') or {}
    caps = card.get('cap') or {}
    reward = 0.0
    for cat in CATS:
        monthly = profile.get(cat, 0)
        if not monthly:
            continue
        rate = earn.get(cat, earn.get('other', 0) or 0)
        annual = monthly * 12
        if cat in caps:
            capped = min(annual, caps[cat])
            over = annual - capped
            other = earn.get('other', 0) or 0
            reward += capped * rate / 100 + over * other / 100
        else:
            reward += annual * rate / 100
    return reward


def _net(card, profile):
    return _annual_reward(card, profile) - (card.get('fee') or 0)


def _is_true_flat_2(c):
    """True flat 2% no-fee: earn is only other=2, fee 0, not Apple Pay / physical-card split."""
    if c.get('type') != 'cash' or (c.get('fee') or 0) != 0:
        return False
    earn = c.get('earn') or {}
    if set(earn.keys()) - {'other'} or earn.get('other') != 2:
        return False
    text = (c.get('earnText') or '') + ' ' + (c.get('note') or '')
    if 'Apple Pay' in text or 'physical card' in text.lower():
        return False
    return True


def _is_conditional_flatish(c):
    """No-fee cash card that looks like ~2% but needs Apple Pay / PayPal checkout / etc."""
    if c.get('type') != 'cash' or (c.get('fee') or 0) != 0:
        return False
    text = (c.get('earnText') or '') + ' ' + (c.get('note') or '')
    return 'Apple Pay' in text or 'PayPal' in text


def build(root):
    cj = json.loads((root / 'data' / 'cards.json').read_text())
    checked = _nice(cj['checkedAt'])
    profile = cj['profile']
    monthly_total = sum(profile.get(c, 0) for c in CATS)
    annual_spend = monthly_total * 12
    cash = [c for c in cj['cards'] if c.get('type') == 'cash']

    flat = sorted([c for c in cash if _is_true_flat_2(c)], key=lambda c: (-_net(c, profile), c['name']))
    top = flat[0]
    flat_net = _net(top, profile)
    flat_rate = (top.get('earn') or {}).get('other', 2)

    # Category / base no-fee cash cards that are not true flat 2% (and not the Apple/PayPal conditionals we call out separately)
    conditional = [c for c in cash if _is_conditional_flatish(c)]
    cat_cards = sorted(
        [c for c in cash if (c.get('fee') or 0) == 0 and c not in flat and c not in conditional],
        key=lambda c: -_net(c, profile),
    )
    # Fee cash cards (Robinhood Gold, Amex BCP, …)
    fee_cards = sorted(
        [c for c in cash if (c.get('fee') or 0) > 0],
        key=lambda c: -_net(c, profile),
    )

    rh = next((c for c in fee_cards if c['id'] == 'rh'), None)
    rh_rate = ((rh.get('earn') or {}).get('other', 0) if rh else 0)
    rh_fee = (rh.get('fee') or 0) if rh else 0
    rh_net = _net(rh, profile) if rh else 0
    rh_gross = _annual_reward(rh, profile) if rh else 0
    gap = rh_rate - flat_rate if rh else 0
    rh_be = (rh_fee / (gap / 100)) if rh and gap > 0 else None

    spend_lbl = f'{annual_spend:,.0f}'
    twist = (f'The twist: a ${rh_fee:,.0f}/yr {_pct(rh_rate)} card can beat free {_pct(flat_rate)} once you spend enough — '
             f'and category cards only win if dining and groceries are heavy.' if rh else
             'Category cards only win if dining and groceries are heavy enough to beat flat 2%.')
    lead = (f'A plain {_pct(flat_rate)} card with no annual fee — like {e(top["name"])} — pays about {_usd(flat_net)} a year '
            f'on our ${spend_lbl}/yr spend mix. That is the default win for most people.')
    head = ('<section class="pagehead"><p class="eyebrow">CARDS / CHECKED ' + e(checked.upper()) + '</p>'
            '<h1>Best cash-back cards <em>with no annual fee.</em></h1>'
            f'<p class="lead">{lead} {twist}</p></section>')

    bars = [(c['name'].split()[0] if len(c['name']) > 18 else c['name'], _net(c, profile), _usd(_net(c, profile)), '#flat')
            for c in flat[:3]]
    for c in fee_cards[:1]:
        bars.append((c['name'].split()[0], _net(c, profile), _usd(_net(c, profile)), '#fee'))
    if cat_cards:
        bars.append((cat_cards[0]['name'].split()[0], _net(cat_cards[0], profile), _usd(_net(cat_cards[0], profile)), '#cats'))
    card = topcard('Simple pick · one card, no fee', _pct(flat_rate) + ' back', top['name'],
                   f'About {_usd(flat_net)}/yr on our ${_usd(annual_spend)[1:]}/yr profile. No categories to track.',
                   f'Checked {checked}',
                   [('Annual fee', '$0'), ('On everything', _pct(flat_rate))],
                   ('Full card table', '/cards'), bars,
                   'Net cash back / yr on the site profile')

    # --- Profile strip ---
    mix = ', '.join(f'{e(cat)} ${_usd(profile[cat])[1:]}/mo' for cat in CATS if profile.get(cat))
    prof_s = ('<section class="digest" id="profile"><p class="eyebrow"><span class="dot"></span> THE SPEND MIX</p>'
              f'<h2 class="takeaway">${_usd(annual_spend)[1:]} a year across dining, groceries, gas, travel, streaming, and other.</h2>'
              f'<p>We score every card on the same profile from cards.json: {mix} '
              f'(${_usd(monthly_total)[1:]}/mo). Annual reward = category spend × cash-back rate, minus the annual fee. '
              'No sign-up bonuses, credits, or point-transfer boosts — just the ongoing earn rate.</p></section>')

    # --- True flat 2% ---
    frow = ''.join(
        f'<tr><td>{_name(c)}<small>{e(c.get("earnText") or "")}</small>'
        + (f'<small>{e(c["perks"])}</small>' if c.get('perks') else '')
        + f'</td><td class="n">{_pct((c.get("earn") or {}).get("other", 0))}</td>'
        f'<td class="n">{_usd(_net(c, profile))}</td></tr>'
        for c in flat)
    cond_note = ''
    for c in conditional:
        note = c.get('note') or ''
        if 'Apple Pay' in (c.get('earnText') or '') or 'Apple Pay' in note:
            cond_note += (f' {e(c["name"])} lists {_pct((c.get("earn") or {}).get("other", 0))} only with Apple Pay '
                          f'(1% with the physical card), so it is not a true flat {_pct(flat_rate)}.')
        elif 'PayPal' in (c.get('earnText') or '') or 'PayPal' in note:
            cond_note += (f' {e(c["name"])} pays more at PayPal checkout; we count the '
                          f'{_pct((c.get("earn") or {}).get("other", 0))} everywhere-else rate from the data.')
    flat_s = ('<section class="digest" id="flat"><p class="eyebrow"><span class="dot"></span> TRUE FLAT 2%, $0 FEE</p>'
              f'<h2 class="takeaway">{len(flat)} cards pay {_pct(flat_rate)} on everything with no annual fee.</h2>'
              f'<p>Same net on our profile: about {_usd(flat_net)}/yr. Pick any; the difference is perks and issuer, not the math.</p>'
              '<table class="ctable"><thead><tr><th>Card · how it pays</th><th style="text-align:right">Rate</th>'
              '<th style="text-align:right">Net / yr</th></tr></thead>'
              f'<tbody>{frow}</tbody></table>'
              + (f'<p>{cond_note.strip()}</p>' if cond_note else '')
              + '</section>')

    # --- Category no-fee ---
    crow = ''.join(
        f'<tr><td>{_name(c)}<small>{e(c.get("earnText") or "")}</small></td>'
        f'<td class="n">{_usd(_net(c, profile))}</td>'
        f'<td class="n">{"+" if _net(c, profile) - flat_net >= 0 else ""}{_usd(_net(c, profile) - flat_net)}</td></tr>'
        for c in cat_cards)
    best_cat = cat_cards[0] if cat_cards else None
    cat_take = (f'On this mix, none of the no-fee category cards beat flat {_pct(flat_rate)}.'
                if best_cat and _net(best_cat, profile) < flat_net else
                f'{e(best_cat["name"])} leads the category pack on this mix.' if best_cat else
                'No category no-fee cards in the data.')
    cat_s = ('<section class="digest" id="cats"><p class="eyebrow"><span class="dot"></span> CATEGORY NO-FEE</p>'
             f'<h2 class="takeaway">{cat_take}</h2>'
             f'<p>Savor, Freedom Unlimited, Altitude Go, and the rest pay more only where you spend a lot. '
             f'Against flat {_pct(flat_rate)}’s {_usd(flat_net)}, every one of them lands lower on dining ${_usd(profile["dining"])[1:]}/mo + '
             f'groceries ${_usd(profile["groceries"])[1:]}/mo + the rest of this profile.</p>'
             '<table class="ctable"><thead><tr><th>Card · earn rates</th><th style="text-align:right">Net / yr</th>'
             '<th style="text-align:right">vs flat 2%</th></tr></thead>'
             f'<tbody>{crow}</tbody></table></section>') if cat_cards else ''

    # --- When a fee is worth it ---
    fee_bits = []
    if rh:
        fee_note = rh.get('feeNote') or f'${rh_fee}/yr'
        fee_bits.append(
            f'<tr><td>{_name(rh)}<small>{e(rh.get("earnText") or "")}</small>'
            f'<small>{e(fee_note)}</small>'
            f'<small><b>What it is worth:</b> {_pct(rh_rate)} on ${_usd(annual_spend)[1:]} is {_usd(rh_gross)}, '
            f'minus {_usd(rh_fee)} = {_usd(rh_net)}. That beats free {_pct(flat_rate)}’s {_usd(flat_net)} by {_usd(rh_net - flat_net)}.'
            + (f' Break-even vs flat {_pct(flat_rate)}: about {_usd(round(rh_be, -2))} of annual spend '
               f'(extra {_pct(gap)} covers the {_usd(rh_fee)} fee).' if rh_be else '')
            + f'</small></td><td class="n">{_usd(rh_fee)}</td><td class="n">{_usd(rh_net)}</td></tr>'
        )
    bcp = next((c for c in fee_cards if c['id'] == 'bcp'), None)
    if bcp:
        bcp_net = _net(bcp, profile)
        bcp_fee = bcp.get('fee') or 0
        bcp_gross = _annual_reward(bcp, profile)
        vs = bcp_net - flat_net
        be_g = None
        for g in range(int(profile['groceries']), int(profile['groceries']) + 2000, 25):
            p2 = dict(profile)
            p2['groceries'] = g
            if _net(bcp, p2) > _annual_reward(top, p2):
                be_g = g
                break
        worth = (f'On this profile: {_usd(bcp_gross)} gross − {_usd(bcp_fee)} fee = {_usd(bcp_net)}, '
                 f'{_usd(abs(vs))} {"above" if vs >= 0 else "under"} flat {_pct(flat_rate)}’s {_usd(flat_net)}.')
        if be_g and vs < 0:
            worth += (f' Needs heavier grocery spend to win — about ${_usd(be_g)[1:]}/mo groceries '
                      f'(other categories held at the profile) before it beats free {_pct(flat_rate)}.')
        fee_bits.append(
            f'<tr><td>{_name(bcp)}<small>{e(bcp.get("earnText") or "")}</small>'
            f'<small>{e(bcp.get("feeNote") or ("$" + str(bcp_fee) + "/yr"))}</small>'
            f'<small><b>What it is worth:</b> {worth}</small></td>'
            f'<td class="n">{_usd(bcp_fee)}</td><td class="n">{_usd(bcp_net)}</td></tr>'
        )
    rh_hook = (f'{e(rh["name"])} nets more than free {_pct(flat_rate)} '
               f'once yearly spend clears a clear break-even.') if rh else f'A fee card can beat free {_pct(flat_rate)} with enough spend.'
    rh_lead = (f'On ${_usd(annual_spend)[1:]}/yr, the ${_usd(rh_fee)[1:]}/yr {_pct(rh_rate)} card wins. '
               if rh else '')
    fee_s = ('<section class="digest" id="fee"><p class="eyebrow"><span class="dot"></span> WHEN A FEE BEATS FREE</p>'
             f'<h2 class="takeaway">{rh_hook}</h2>'
             f'<p>{rh_lead}Category fee cards (grocery-heavy) only pay off if that category is fat enough to cover the fee and still beat flat 2%.</p>'
             '<table class="ctable"><thead><tr><th>Card · the math</th><th style="text-align:right">Fee</th>'
             '<th style="text-align:right">Net / yr</th></tr></thead>'
             f'<tbody>{"".join(fee_bits)}</tbody></table></section>') if fee_bits else ''

    flat_names = ', '.join(e(c['name']) for c in flat[:3])
    rh_li = ''
    if rh and rh_be:
        rh_li = (f'<li><b>Spend over ~${_usd(round(rh_be, -2))[1:]}/yr and already want Gold:</b> '
                 f'{e(rh["name"])}’s {_pct(rh_rate)} nets {_usd(rh_net)} here vs {_usd(flat_net)} free.</li>')
    pick_s = ('<section class="digest" id="pick"><p class="eyebrow"><span class="dot"></span> HOW TO PICK</p>'
              '<h2 class="takeaway">Most people should take a flat 2% no-fee card and stop optimizing.</h2><ul>'
              f'<li><b>Want zero homework:</b> {flat_names} — same {_pct(flat_rate)}, $0 fee.</li>'
              + rh_li
              + '<li><b>Dining + groceries are most of your card spend:</b> re-run the category table with your mix — Savor / Altitude Go can flip ahead of flat 2% when those buckets are fat.</li>'
              + '<li><b>Ignore sign-up bonuses here:</b> they are one-time. This page ranks the ongoing earn rate only.</li>'
              + '</ul></section>')

    foot = ('<section class="digest" id="more"><p class="eyebrow"><span class="dot"></span> MORE</p>'
            f'<p>Every rate and fee here comes from cards.json (checked {checked}). Confirm on the issuer’s site before you apply — terms change.</p>'
            '<p><a href="/cards">See the full Cards table →</a> · <a href="/disclosure">How this site makes money</a>. '
            'No links on this page pay us, and rankings are by net cash back on the profile, never by payout.</p></section>')

    body = ('<p class="trust"><span><b>●</b> Checked ' + e(checked) + '</span><span>Flat 2% vs categories vs fees</span>'
            '<span>No sponsored rankings</span></p>'
            + head + card + prof_s + flat_s + cat_s + fee_s + pick_s + foot)
    mon = date.fromisoformat(cj['checkedAt']).strftime('%b %Y')
    title = f'Best no-fee cash-back cards ({mon}) — getmoneybeast.com'
    desc = (f'Flat {_pct(flat_rate)} no-fee cards pay about {_usd(flat_net)}/yr on a ${spend_lbl} spend mix. '
            + (f'{rh["name"]} (3% + ${rh_fee:,.0f}/yr Gold membership) nets {_usd(rh_net)}. '.replace('3%', _pct(rh_rate)) if rh else '')
            + 'Category cards only win with heavy dining/grocery spend. Hand-checked, no sponsored rankings.')
    return title, desc, body


def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    title, desc, body = build(D.parent)
    (D / 'best-nofee-cards.html').write_text(
        finalize(lazyimg(page(title, desc, '/best-nofee-cards', 'x', body, pages2.CSS + TRUST_CSS + DIGEST_CSS + UI_CSS))))
    h = rd('cards.html')
    if 'href="/best-nofee-cards"' not in h:
        for old, new in (
            ('<a href="/best-hysa">Best no-strings savings</a> · <a href="/sponsor">Sponsor</a> · ',
             '<a href="/best-hysa">Best no-strings savings</a> · <a href="/best-nofee-cards">Best no-fee cards</a> · <a href="/sponsor">Sponsor</a> · '),
            ('<a href="/sponsor">Sponsor</a> · ',
             '<a href="/best-nofee-cards">Best no-fee cards</a> · <a href="/sponsor">Sponsor</a> · '),
        ):
            if old in h:
                (D / 'cards.html').write_text(h.replace(old, new, 1))
                break
