"""Compose the 4-tab site from builder outputs: python3 scripts/compose.py

Builders write SOURCE pages (not served; see scripts/site_dir.sh + docs/_redirects):
  build.py -> docs/savings.html   build_yields.py -> docs/world.html
  build_crypto.py -> docs/crypto.html   build_economy.py -> docs/economy.html
  build_insights.py -> docs/insights.html   daily card routine -> docs/daily.html
This writes the SERVED pages: docs/index.html (Rates: US savings + World views),
docs/markets.html (Daily, stock notes, crypto, economy), docs/notes.html, and fixes nav in cards.html.
Every builder calls this at the end; deploy.yml runs it again before deploying. Idempotent.
"""
import re, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT/'docs'
def rd(n): return (D/n).read_text()
NAV_ITEMS = [('Rates','/','rates'),('Markets','/markets','markets'),('Cards','/cards','cards'),('Notes','/notes','notes')]
def nav(cur): return '<nav aria-label="Main navigation">'+''.join(f'<a class="nav-switch" href="{h}"{" aria-current=\"page\"" if k==cur else ""}>{l}</a>' for l,h,k in NAV_ITEMS)+'</nav>'
def setnav(s, cur): return re.sub(r'<nav aria-label="Main navigation">.*?</nav>', nav(cur), s, count=1, flags=re.S)
def main(s): return re.search(r'<main[^>]*>(.*)</main>', s, re.S).group(1)
def head_styles(s): return ''.join(re.findall(r'<style>.*?</style>', s.split('<body')[0], re.S))
def sections(m):
    """Top-level <section ...>...</section> blocks, keyed by id or class."""
    out, depth, start = [], 0, 0
    for t in re.finditer(r'<(/?)section\b[^>]*>', m):
        if t.group(1):
            depth -= 1
            if depth == 0: out.append(m[start:t.end()])
        else:
            if depth == 0: start = t.start()
            depth += 1
    return out
def sec(m, key):
    """First <section> (any depth) whose opening tag has id=key or class starting with key; balanced."""
    for t in re.finditer(r'<section\b[^>]*>', m):
        tag = t.group(0)
        if f'id="{key}"' in tag or f'class="{key}' in tag:
            depth = 0
            for u in re.finditer(r'<(/?)section\b[^>]*>', m[t.start():]):
                depth += -1 if u.group(1) else 1
                if depth == 0: return m[t.start():t.start()+u.end()]
    raise KeyError(key)
def demote(s): return re.sub(r'<(/?)h1\b', r'<\1h2', s)
def tuck(block, label):
    return f'<details class="tuck"><summary>{label}</summary>{block}</details>'
def page(title, desc, url, cur, body, extra_head='', scripts=''):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="https://money.ilyusha.xyz{url}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz{url}"><meta name="twitter:card" content="summary"><link rel="icon" href="/favicon.ico?v=3" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png?v=3"><link rel="apple-touch-icon" href="/apple-touch-icon.png?v=3"><link rel="stylesheet" href="/styles.css"><script src="/analytics.js" defer></script>{scripts}{TUCK_CSS}{extra_head}</head>
<body><header><a class="brand" href="/"><img class="brand-mark" src="/favicon.svg?v=3" width="32" height="32" style="border-radius:6px" alt="">money<span class="brand-by">/ by ilyusha</span></a>{nav(cur)}<a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main id="top">{body}</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="mailto:dev@ilyusha.xyz?subject=Money%20correction">Suggest a correction ↗</a></footer></body></html>'''
TUCK_CSS = '''<style>.tuck{margin:1.2rem 0;border:1px solid rgba(127,127,127,.3);border-radius:.8rem;padding:.8rem 1.1rem}.tuck>summary{cursor:pointer;font-weight:600}.tuck[open]>summary{margin-bottom:.8rem}
.view-tabs{display:flex;gap:.5rem;margin:1.2rem 0 .4rem}.view-tabs a{padding:.45rem 1rem;border:1px solid rgba(127,127,127,.4);border-radius:2rem;text-decoration:none;color:inherit}.view-tabs a[aria-selected="true"]{background:currentColor}.view-tabs a[aria-selected="true"] span{filter:invert(1)}
.rows.collapsed .provider-row:nth-child(n+9){display:none}.show-all{margin:1rem 0;padding:.6rem 1.2rem;border-radius:2rem;border:1px solid rgba(127,127,127,.5);background:none;color:inherit;cursor:pointer;font:inherit}
.jump{display:flex;flex-wrap:wrap;gap:.4rem 1rem;margin:.6rem 0 1.4rem;font-size:.95rem}.wrap{max-width:1150px;margin:0 auto;padding:0 1.2rem}</style>'''

# ---------- Rates (index.html) ----------
sv, wd = rd('savings.html'), rd('world.html')
svm, wdm = main(sv), main(wd)
hero = sec(svm, 'hero')
crypto_ids = re.findall(r'id="provider-([^"]+)"', sec(svm, 'crypto-rates'))
for cid in crypto_ids: hero = hero.replace(f'href="#provider-{cid}"', f'href="/markets#provider-{cid}"')
rates = sec(svm, 'rates')
rates = rates.replace(sec(svm, 'crypto-rates'), '', 1)
rates = re.sub(r'<div class="filters" role="group".*?</div>', '', rates, count=1, flags=re.S)  # one-row controls
rates = rates.replace('<div class="rows">', '<div class="rows collapsed">', 1)
ncash = len(re.findall(r'class="provider-row"', rates))
rates = rates.replace('<p id="empty"', f'<button type="button" class="show-all" id="show-all">Show all {ncash}</button><p id="empty"', 1)
rates = rates.replace('<a href="#methodology">How we compare ↗</a>', '<a href="#methodology">How we compare ↓</a> · Crypto yields moved to <a href="/markets#crypto-rates">Markets</a>')
method = re.search(r'<section class="methodology".*?</section>', svm, re.S)
method = tuck(method.group(0).replace('class="methodology" id="methodology"', 'class="methodology"'), 'How we compare: base vs. top APY, checks, caveats') if method else ''
method = method.replace('<details class="tuck">', '<details class="tuck" id="methodology">', 1)
world_hero = demote(sec(wdm, 'hero'))
world_rest = wdm[wdm.index(sec(wdm, 'hero')) + len(sec(wdm, 'hero')):]
show_js = '''<script>(()=>{const r=document.querySelector('#rates .rows'),b=document.getElementById('show-all');if(b)b.onclick=()=>{r.classList.remove('collapsed');b.remove()};
const ex=()=>{if(b&&b.isConnected){r.classList.remove('collapsed');b.remove()}};const q=document.getElementById('search');q&&q.addEventListener('input',ex);['coverage','minimum','sort'].forEach(i=>{const e=document.getElementById(i);e&&e.addEventListener('change',ex)});if(new URLSearchParams(location.search).toString())ex();
const tabs=[...document.querySelectorAll('.view-tabs a')];function show(v){document.getElementById('view-us').hidden=v==='world';document.getElementById('view-world').hidden=v!=='world';tabs.forEach(t=>t.setAttribute('aria-selected',String(t.dataset.view===v)))}
const want=()=>{const h=location.hash.slice(1);return (h==='world'||document.getElementById(h)?.closest('#view-world'))?'world':'us'};tabs.forEach(t=>t.onclick=e=>{e.preventDefault();history.replaceState(null,'',t.dataset.view==='world'?'#world':location.pathname+location.search);show(t.dataset.view)});
window.addEventListener('hashchange',()=>show(want()));show(want());const h=location.hash.slice(1);if(h&&h!=='world'){const el=document.getElementById(h);if(el){if(el.tagName==='DETAILS')el.open=true;el.scrollIntoView()}}})();</script>'''
tabs = '<div class="view-tabs" role="tablist"><a href="/" data-view="us" role="tab"><span>US savings</span></a><a href="/#world" data-view="world" role="tab"><span>World deposits</span></a></div>'
body = (tabs + f'<div id="view-us">{hero}{rates}{method}<a class="back-top" href="#rates" aria-label="Back to filters">↑ Filters</a></div>'
        + f'<div id="view-world" class="wrap" hidden><span id="world"></span>{world_hero}{world_rest}</div>' + show_js)
desc = re.search(r'<meta name="description" content="([^"]*)"', sv).group(1)
# ---------- lazy helpers (perf) ----------
(D/'frag').mkdir(exist_ok=True)
def lazytuck(html, label, name):
    (D/'frag'/f'{name}.html').write_text(html)
    return f'<details class="tuck lazy" data-frag="/frag/{name}?v={hashlib.sha256(html.encode()).hexdigest()[:8]}"><summary>{label}</summary><div class="frag-body"><p>Loading…</p></div></details>'
LAZY_JS = '''<script>(()=>{const load=d=>{if(d.dataset.done)return Promise.resolve();d.dataset.done=1;return fetch(d.dataset.frag).then(r=>r.text()).then(t=>{d.querySelector('.frag-body').innerHTML=t})};document.querySelectorAll('details.lazy').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)load(d)}));window.__loadAllFrags=()=>Promise.all([...document.querySelectorAll('details.lazy')].map(load))})();</script>'''
def lazyimg(h):
    return re.sub(r'<img (?![^>]*loading=)(?![^>]*brand-mark)', '<img loading="lazy" ', h)

idx = page('Money — rates at home and abroad', desc, '/', 'rates', body, head_styles(wd), '<script src="/app.js" defer></script>')
for asset in ('styles.css', 'app.js', 'analytics.js', 'favicon.svg'):
    v = hashlib.sha256((D/asset).read_bytes()).hexdigest()[:10]
    idx = idx.replace(f'"/{asset}"', f'"/{asset}?v={v}"')
(D/'index.html').write_text(lazyimg(idx))

# ---------- Markets ----------
dy, ins, cr, ec = rd('daily.html'), rd('insights.html'), rd('crypto.html'), rd('economy.html')
dym, insm, crm, ecm = main(dy), main(ins), main(cr), main(ec)
cy = sec(svm, 'crypto-rates').replace('<div class="rows">', '<div class="rows">', 1)
crypto_block = (f'<div id="crypto">{demote(sec(crm, "hero"))}{sec(crm, "biggest")}'
                + lazytuck(sec(crm, 'coins'), 'Full coin list', 'coins') + tuck(cy, 'Crypto & stablecoin yields (moved from Rates)').replace('<details class="tuck">', '<details class="tuck" id="crypto-yields">', 1) + '</div>')
econ_block = (f'<div id="economy">{demote(sec(ecm, "hero"))}{sec(ecm, "biggest")}'
              + lazytuck(sec(ecm, 'map'), 'World GDP map', 'gdp-map') + lazytuck(sec(ecm, 'flows'), 'Investment flows (FDI)', 'fdi') + '</div>')
jump = '<p class="jump"><a href="#daily">Today’s card</a><a href="#stocks">Stock notes</a><a href="#crypto">Crypto</a><a href="#economy">Economy</a></p>'
mk_js = LAZY_JS + '''<script>(()=>{const h=location.hash.slice(1);if(!h)return;const go=()=>{const el=document.getElementById(h);if(el){const d=el.closest('details');if(d)d.open=true;setTimeout(()=>el.scrollIntoView(),50)}};document.getElementById(h)?go():window.__loadAllFrags().then(go)})();</script>'''
body = f'<div id="daily">{dym}</div>{jump}{sec(insm, "stocks")}{crypto_block}{econ_block}{mk_js}'
desc = re.search(r'<meta name="description" content="([^"]*)"', dy).group(1)
mk = page('Money — markets', desc, '/markets', 'markets', body, head_styles(dy) + head_styles(cr) + head_styles(ec))
(D/'markets.html').write_text(lazyimg(mk))

# ---------- Notes ----------
notes_m = insm.replace(sec(insm, 'stocks'), '<p class="jump">Stock notes moved to <a href="/markets#stocks">Markets</a>.</p>')
desc = re.search(r'<meta name="description" content="([^"]*)"', ins).group(1)
(D/'notes.html').write_text(lazyimg(page('Money — notes', desc, '/notes', 'notes', notes_m, head_styles(ins))))

# ---------- nav everywhere ----------
cards = rd('cards.html'); (D/'cards.html').write_text(lazyimg(setnav(cards, 'cards')))
for n in ('savings.html', 'world.html', 'crypto.html', 'economy.html', 'insights.html', 'daily.html'):
    (D/n).write_text(setnav(rd(n), 'x'))
print('Composed index.html, markets.html, notes.html')
