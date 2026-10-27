"""SEO layer (Oct 26 2026): consistent titles/descriptions, article og:type, JSON-LD (Article, BreadcrumbList, WebSite)
and a related-tools block on guides. Runs last in ui3.finalize. Idempotent."""
import json, re
from datetime import datetime

SITE = 'https://getmoneybeast.com'
ORG = {'@type': 'Organization', 'name': 'Money Beast', 'url': SITE + '/', 'logo': SITE + '/apple-touch-icon.png',
       'sameAs': ['https://x.com/MoneyBeastHQ']}
# first publish date = the day the page was added to the repo (git log --diff-filter=A)
ARTICLES = {'/best-hysa': '2026-10-15', '/best-nofee-cards': '2026-10-16',
            '/pay-property-tax-credit-card': '2026-10-20', '/tbills-vs-savings-california': '2026-10-21'}
PAGES = {  # path: (title, description or None to keep, breadcrumb name)
    '/': ('Money Beast: savings rates at home and abroad, checked daily',
          'Compare plain US savings rates and the catches behind 5%+ headlines, plus deposit rates in 10 tracked countries shown in dollars. Dates and sources on every number.', None),
    '/markets': ('Markets today: mortgage rates, yields, gas, stocks | Money Beast', None, 'Markets'),
    '/cards': ('Cash-back card calculator: rewards minus fees | Money Beast',
               'See what each cash-back or rewards card nets you a year after its annual fee, using your own spending. Hand-checked terms, no sponsored rankings.', 'Cards'),
    '/guides': ('Money guides with the math shown | Money Beast', None, 'Guides'),
    '/sponsor': ('Sponsor Money Beast', None, 'Sponsor'),
    '/disclosure': ('How we check and rank | Money Beast', None, 'How we check'),
    '/privacy': ('Privacy policy | Money Beast', None, 'Privacy'),
}
RELATED = [('/', 'Savings calculator', 'What a rate pays on your balance'),
           ('/#world', 'World view', 'Deposit rates abroad, in dollars'),
           ('/cards', 'Card calculator', 'Rewards minus fees on your spending'),
           ('/markets', 'Markets', 'Rates, gas and stocks with dates'),
           ('/best-hysa', 'No-strings savings', 'Plain rates vs the catches'),
           ('/best-nofee-cards', 'No-fee cash-back cards', 'Flat 2% vs categories'),
           ('/tbills-vs-savings-california', 'T-bills vs savings (CA)', 'After California tax'),
           ('/pay-property-tax-credit-card', 'Property tax by card', 'County fees vs rewards')]
CSS = ('<style>.related{margin:var(--s6,32px) 0 0;padding-top:var(--s4,16px);border-top:1px solid var(--line)}'
       '.related ul{list-style:none;padding:0;margin:8px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}'
       '.related a{display:block;padding:12px 14px;border:1px solid var(--line);border-radius:var(--r2,12px);background:var(--card);text-decoration:none;color:inherit;min-height:44px}'
       '.related a b{display:block;font-size:15px}.related a span{font-size:13px;color:var(--muted)}</style>')

def esc(s): return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
def text(s): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()

def _set_meta(h, attr, key, val):
    tag = f'<meta {attr}="{key}" content="{esc(val)}">'
    if re.search(rf'<meta {attr}="{re.escape(key)}"', h):
        return re.sub(rf'<meta {attr}="{re.escape(key)}" content="[^"]*">', lambda _: tag, h, count=1)
    return h.replace('</head>', tag + '</head>', 1)

def _checked(h):
    m = re.search(r'(?:Checked|CHECKED|Treasury yields) ([A-Z][a-z]{2} \d{1,2}, \d{4})', h)
    if not m: return None
    return datetime.strptime(m.group(1), '%b %d, %Y').date().isoformat()

def apply(h):
    if '</head>' not in h or '<main' not in h: return h
    m = re.search(r'<link rel="canonical" href="https://getmoneybeast\.com(/[^"]*)"', h)
    path = m.group(1) if m else '/'
    h = re.sub(r'<script type="application/ld\+json" data-seo>.*?</script>', '', h, flags=re.S)
    h = re.sub(r'<meta property="article:[^"]*" content="[^"]*">', '', h)
    import html as _html
    title = _html.unescape(re.search(r'<title>(.*?)</title>', h, re.S).group(1))
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', h)
    desc = _html.unescape(desc_m.group(1)) if desc_m else ''
    crumbs = [('Money Beast', SITE + '/')]
    ld = []
    if path in ARTICLES:
        title = re.sub(r'\s+[—|-]\s+(getmoneybeast\.com|Money Beast)$', '', title) + ' | Money Beast'
        h1 = text(re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S).group(1))
        mod = _checked(h) or ARTICLES[path]
        img = SITE + '/og/' + path.strip('/') + '.png'
        crumbs += [('Guides', SITE + '/guides'), (h1.rstrip('.'), SITE + path)]
        ld.append({'@context': 'https://schema.org', '@type': 'Article', 'headline': h1.rstrip('.')[:110], 'description': desc,
                   'image': img, 'datePublished': ARTICLES[path], 'dateModified': mod, 'author': ORG, 'publisher': ORG,
                   'mainEntityOfPage': SITE + path, 'inLanguage': 'en-US'})
        h = _set_meta(h, 'property', 'og:type', 'article')
        h = h.replace('</head>', f'<meta property="article:published_time" content="{ARTICLES[path]}"><meta property="article:modified_time" content="{mod}"></head>', 1)
        if 'class="related"' not in h:
            items = ''.join(f'<li><a href="{u}"><b>{n}</b><span>{d}</span></a></li>' for u, n, d in RELATED if u != path)
            block = f'<section class="related" aria-labelledby="rel-h"><p class="eyebrow" id="rel-h">TOOLS AND GUIDES</p><ul>{items}</ul></section>'
            h = re.sub(r'(</main>)', lambda mm: block + mm.group(1), h, count=1)
            h = h.replace('</head>', CSS + '</head>', 1)
    elif path in PAGES:
        t, d, crumb = PAGES[path]
        title = t
        if d: desc = d
        if crumb: crumbs.append((crumb, SITE + path))
    if path == '/':
        ld.append({'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Money Beast', 'url': SITE + '/', 'publisher': ORG})
    if len(crumbs) > 1:
        ld.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]})
    h = re.sub(r'<title>.*?</title>', lambda _: f'<title>{esc(title)}</title>', h, count=1, flags=re.S)
    h = _set_meta(h, 'property', 'og:title', title)
    h = _set_meta(h, 'property', 'og:site_name', 'Money Beast')
    if desc:
        h = _set_meta(h, 'name', 'description', desc)
        h = _set_meta(h, 'property', 'og:description', desc)
    for x in ld:
        h = h.replace('</head>', '<script type="application/ld+json" data-seo>' + json.dumps(x, ensure_ascii=False).replace('</', '<\\/') + '</script></head>', 1)
    return h
