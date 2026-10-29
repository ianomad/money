"""Crawl served docs/*.html: every internal link must resolve to a served file (or a _redirects rule) and every #anchor must exist on its target page."""
import re, sys
from pathlib import Path
D = Path(__file__).resolve().parents[1] / 'docs'
SOURCE = {'cards-src.html', 'savings.html', 'world.html', 'daily.html', 'crypto.html', 'economy.html', 'insights.html'}
def served():
    return [p for p in D.glob('*.html') if p.name not in SOURCE and not p.name.startswith('google')] + list((D / 'frag').glob('*.html'))
def redirects():
    r = {}
    for l in (D / '_redirects').read_text().splitlines():
        p = l.split()
        if len(p) >= 2: r[p[0]] = p[1]
    return r
def target(path, R):
    if path in R: path = R[path].split('#')[0] or '/'
    if path in ('', '/'): return D / 'index.html'
    f = D / path.lstrip('/')
    if f.is_file(): return f
    if (D / (path.lstrip('/') + '.html')).is_file() and path.lstrip('/') + '.html' not in SOURCE: return D / (path.lstrip('/') + '.html')
    return None
def ids(f, cache={}):
    if f not in cache:
        h = f.read_text(errors='ignore'); s = set(re.findall(r'\bid="([^"]+)"', h)) | set(re.findall(r'\bname="([^"]+)"', h))
        if f.name in ('index.html', 'markets.html', 'rates.html', 'abroad.html'):  # lazy fragments are inserted into these pages
            for fr in (D / 'frag').glob('*.html'): s |= set(re.findall(r'\bid="([^"]+)"', fr.read_text()))
        cache[f] = s
    return cache[f]
def main():
    R = redirects(); bad = []
    for f in served():
        h = f.read_text(errors='ignore')
        for u in re.findall(r'\b(?:href|src)="([^"]+)"', h):
            if re.match(r'(https?:|mailto:|data:|tel:|javascript:)', u) and not u.startswith('https://getmoneybeast.com'): continue
            if "'+" in u: continue
            u = re.sub(r'^https://getmoneybeast.com', '', u).split('?')[0]
            path, _, frag = u.partition('#')
            t = f if path == '' else target(path, R)
            if t is None: bad.append(f'{f.name}: {u} (no such page)'); continue
            if frag and frag not in ids(t) and not (t.name == 'index.html' and frag in ('world',)): bad.append(f'{f.name}: {u} (no #{frag} on {t.name})')
    for b in sorted(set(bad)): print('BROKEN', b)
    print(f'links: {len(served())} pages, {len(set(bad))} broken'); return len(set(bad))
if __name__ == '__main__': sys.exit(1 if main() else 0)
