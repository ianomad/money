"""Write docs/robots.txt and docs/sitemap.xml (clean URLs matching docs/_redirects). Called from compose.py."""
from datetime import date

BASE = 'https://money.ilyusha.xyz'
# (path, served file) — only composed, public pages; builder source pages redirect and stay out.
PAGES = [('/', 'index.html'), ('/best-hysa', 'best-hysa.html'), ('/best-nofee-cards', 'best-nofee-cards.html'), ('/markets', 'markets.html'), ('/cards', 'cards.html'),
         ('/sponsor', 'sponsor.html'), ('/disclosure', 'disclosure.html'), ('/privacy', 'privacy.html')]


def write(D, today=None):
    today = today or date.today().isoformat()
    (D / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
    urls = ''.join(f'  <url><loc>{BASE}{p}</loc><lastmod>{today}</lastmod></url>\n' for p, f in PAGES if (D / f).exists())
    (D / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                   + urls + '</urlset>\n')
