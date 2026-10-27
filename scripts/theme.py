"""theme: the Money Beast design system + site chrome, applied LAST to every served page (hooked into ui3.finalize).
- Drops every older inline <style> layer and inlines scripts/theme.css once (one shared stylesheet, no render-blocking CSS).
- Replaces <header>/<footer> with one consistent header (top nav + no-JS mobile menu) and footer (grouped links).
- Idempotent: running it twice gives the same page."""
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
X_URL = 'https://x.com/MoneyBeastHQ'
CORR = 'mailto:dev@ilyusha.xyz?subject=Money%20Beast%20correction'
NAV = [('Savings', '/', 'savings'), ('World', '/#world', 'world'), ('Cards', '/cards', 'cards'), ('Markets', '/markets', 'markets'), ('Guides', '/guides', 'guides')]
GROUPS = [
    ('Savings & rates', [('US savings rates', '/'), ('Banks abroad (World)', '/#world'), ('Best no-strings savings', '/best-hysa'), ('T-bills vs savings (California)', '/tbills-vs-savings-california')]),
    ('Cards & fees', [('Card calculator', '/cards'), ('Best no-fee cash-back cards', '/best-nofee-cards'), ('Paying property tax by card', '/pay-property-tax-credit-card')]),
    ('Markets', [('Today’s numbers', '/markets'), ('Dates to watch', '/markets#watch'), ('Crypto', '/markets#crypto'), ('World economy', '/markets#economy')]),
    ('About', [('How we check and rank', '/disclosure'), ('Sponsor', '/sponsor'), ('Privacy', '/privacy'), ('Suggest a correction ↗', CORR)]),
]
SECTION = {'/': 'savings', '/cards': 'cards', '/cards.html': 'cards', '/markets': 'markets', '/guides': 'guides',
           '/best-hysa': 'guides', '/best-nofee-cards': 'guides', '/pay-property-tax-credit-card': 'guides', '/tbills-vs-savings-california': 'guides'}
DATA_PAGES = {'/', '/cards', '/cards.html', '/markets', '/best-hysa', '/best-nofee-cards', '/pay-property-tax-credit-card', '/tbills-vs-savings-california'}

def css():
    s = (HERE / 'theme.css').read_text()
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'\s*\n\s*', '', s)
    return re.sub(r'\s*([{};,>])\s*', r'\1', s).replace(';}', '}')

def _links(items, cur=None, cls=''):
    return ''.join(f'<a href="{h}"{" aria-current=\"page\"" if k == cur else ""}>{l}</a>' for l, h, k in items)

def header(cur):
    groups = ''.join(f'<div><h2>{g}</h2>' + ''.join(f'<a href="{h}">{l}</a>' for l, h in items) + '</div>' for g, items in GROUPS)
    return (f'<header class="site-header"><a class="skip-link" href="#top">Skip to content</a><div class="hbar">'
            '<a class="brand" href="/" aria-label="Money Beast home"><img src="/favicon.svg?v=6" width="32" height="32" alt="" class="brand-mark"><span class="bn">Money <b>Beast</b></span></a>'
            f'<nav class="mainnav" aria-label="Main">{_links(NAV, cur)}</nav>'
            f'<div class="hact"><a class="xfollow" href="{X_URL}" target="_blank" rel="noopener" data-x-follow="header">Follow on X ↗</a>'
            f'<details class="menu"><summary aria-label="All pages"><span class="bars" aria-hidden="true"></span>Menu</summary><div class="menu-panel"><nav class="menu-grid" aria-label="All pages">{groups}</nav></div></details></div></div>'
            f'<nav class="tabs-m" aria-label="Sections">{_links(NAV, cur)}</nav></header>')

def footer(note):
    groups = ''.join(f'<div><h2>{g}</h2>' + ''.join(f'<a href="{h}">{l}</a>' for l, h in items) + '</div>' for g, items in GROUPS)
    return ('<footer class="site-footer"><div>'
            f'<nav class="fgrid" aria-label="Footer">{groups}</nav>'
            f'<p class="fabout"><b>Money Beast</b> is an independent tracker of savings rates, cards and markets by <a href="https://ilyusha.xyz">Ilyusha ↗</a>. Rankings are never paid. '
            f'Daily charts on X: <a class="xline" href="{X_URL}" target="_blank" rel="noopener" data-x-follow="footer">@MoneyBeastHQ ↗</a></p>'
            f'<p class="fine">{note}</p></div></footer>')

MENU_JS = ('<script>(()=>{const m=document.querySelector(".site-header .menu");if(!m)return;'
           'document.addEventListener("click",e=>{if(m.open&&!m.contains(e.target))m.open=false});'
           'document.addEventListener("keydown",e=>{if(e.key==="Escape"&&m.open){m.open=false;m.querySelector("summary").focus()}});'
           'm.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>m.open=false))})()</script>')

def apply(h):
    if '<main' not in h or '</head>' not in h: return h
    # clean canonical/og:url (/cards.html -> /cards): .html URLs only redirect
    h = re.sub(r'((?:rel="canonical" href|property="og:url" content)="https://getmoneybeast\.com/[a-z0-9-]+)\.html"', r'\1"', h)
    m = re.search(r'<link rel="canonical" href="https://getmoneybeast\.com(/[^"]*)"', h)
    path = m.group(1) if m else '/'
    cur = SECTION.get(path)
    # 1. styles: drop all older layers, inline the one design system
    h = re.sub(r'<style[^>]*>.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<link rel="stylesheet"[^>]*>', '', h)
    h = h.replace('</head>', f'<style>{css()}</style></head>', 1)
    h = h.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="theme-color" content="#fbfaf6">', 1)
    # 2. chrome
    h = re.sub(r'<a class="skip-link"[^>]*>.*?</a>', '', h, flags=re.S)
    h = re.sub(r'<header\b[^>]*>.*?</header>', lambda _: header(cur), h, count=1, flags=re.S)
    fm = re.search(r'<footer\b[^>]*>.*?</footer>', h, re.S)
    if fm:
        nm = re.search(r'<p class="fine">(.*?)</p>', fm.group(0), re.S)
        note = nm.group(1) if nm else 'General information, not financial advice. Rates and terms change; confirm with the provider before you move money.'
        h = h[:fm.start()] + footer(note) + h[fm.end():]
    if MENU_JS not in h: h = h.replace('</body>', MENU_JS + '</body>', 1)
    # 3. trust line only on data pages, and one per page
    if path not in DATA_PAGES: h = re.sub(r'<p class="trust">.*?</p>', '', h, count=1, flags=re.S)
    # 4. brand in titles
    h = re.sub(r'<title>Money — ', '<title>Money Beast — ', h)
    h = re.sub(r'(<meta property="og:title" content=")Money — ', r'\1Money Beast — ', h)
    return h
