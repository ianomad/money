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
    li = ''.join(f'<li><a href="{u}"><span class="tag">{t}</span><b>{n}</b><span>{d}</span></a></li>' for u, t, n, d in GUIDES)
    tl = ''.join(f'<li><a href="{u}"><b>{n}</b><span>{d}</span></a></li>' for u, n, d in TOOLS)
    body = ('<section class="pagehead"><p class="eyebrow">Guides</p><h1>Plain answers to <em>money questions.</em></h1>'
            '<p class="lead">Short guides with the math shown, plus the tools they use. Every number links back to where it came from.</p></section>'
            f'<section aria-labelledby="g-h"><h2 id="g-h" class="sec-h">Guides</h2><ul class="guides-list">{li}</ul></section>'
            f'<section aria-labelledby="t-h"><h2 id="t-h" class="sec-h">Tools</h2><ul class="guides-list">{tl}</ul></section>'
            '<p class="hint">Something wrong or missing? <a href="mailto:dev@ilyusha.xyz?subject=Money%20Beast%20correction">Suggest a correction ↗</a></p>')
    (D / 'guides.html').write_text(finalize(lazyimg(page('Guides — Money Beast', 'Plain-English money guides with the math shown: savings, T-bills, no-fee cards and property tax by card.', '/guides', 'x', body, DIGEST_CSS + UI_CSS))))
