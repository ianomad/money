"""Write docs/guides.html: one hub for the plain-English guides and tools. Called from compose.py."""
import re
GUIDES = [
    ('/best-hysa', 'Savings', 'Best no-strings savings', 'Accounts that pay a good rate without direct deposit, fees or promos that run out.'),
    ('/tbills-vs-savings-california', 'Savings', 'T-bills vs savings in California', 'Why a lower T-bill rate can beat a savings account after state tax.'),
    ('/best-nofee-cards', 'Cards', 'Best no-fee cash-back cards', 'Simple flat-rate cards versus category cards, worked out on real spending.'),
    ('/pay-property-tax-credit-card', 'Cards', 'Paying property tax by card', 'County card fees versus rewards: when it pays and when it costs you.'),
]
TOOLS = [
    ('/#calc', 'Savings earnings calculator', 'What each US account would pay you in the first year, after promos, caps and fees.'),
    ('/#world', 'Banks abroad', 'Deposit rates in 10 tracked countries, with the currency risk worked out in dollars.'),
    ('/cards', 'Card calculator', 'Enter your spending and see what each card is worth after its fee.'),
    ('/markets', 'Today’s numbers', 'Mortgage rates, gas, stocks, the Fed and dates to watch.'),
]
def write(page, finalize, lazyimg, rd, D, DIGEST_CSS, UI_CSS):
    def meta(fn):
        h = (D / fn).read_text() if (D / fn).exists() else ''
        m = re.search(r'"dateModified":\s*"([^"]+)"', h) or re.search(r'<time[^>]*datetime="([^"]+)"', h)
        return m.group(1)[:10] if m else ''
    import feed as F
    def hook(fn):
        h = (D / fn).read_text() if (D / fn).exists() else ''
        g = lambda c: (lambda m: re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else '')(re.search(rf'<p class="{c}">(.*?)</p>', h, re.S))
        return g('share-rate'), g('share-who')
    cards, bul = [], []
    for u, t, n, d in GUIDES:
        big, who = hook(u.strip('/') + '.html')
        if big and len(bul) < 3: bul.append(f'<li>{n}: <b>{big}</b> · {who}</li>')
        cards.append(f'<a class="fc gcard" href="{u}"><p class="fc-k">{t}</p><p class="fc-big">{big or n}</p><p class="fc-line"><b>{n}</b>{" · " + who if big else ""}</p><p class="fc-foot">Read the guide →</p></a>')
    tl = ''.join(f'<a class="btn" href="{u}">{n}</a>' for u, n, d in TOOLS)
    body = (F.head('Plain answers to <em>money questions.</em>', 'The math shown. Sources linked.')
            + (f'<article class="fc tldr"><p class="fc-k">TL;DR</p><ul>{"".join(bul)}</ul></article>' if len(bul) == 3 else '')
            + f'<section aria-labelledby="g-h"><h2 id="g-h" class="fh">Guides</h2><div class="feed gfeed">{"".join(cards)}</div></section>'
            + f'<section aria-labelledby="t-h"><h2 id="t-h" class="fh">Tools</h2><div class="fc-act tools">{tl}</div></section>'
            + '<p class="hint"><a href="mailto:dev@ilyusha.xyz?subject=Money%20Beast%20correction">Suggest a correction ↗</a></p>')
    (D / 'guides.html').write_text(finalize(lazyimg(page('Guides — Money Beast', 'Plain-English money guides with the math shown: savings, T-bills, no-fee cards and property tax by card.', '/guides', 'x', body, DIGEST_CSS + UI_CSS))))
