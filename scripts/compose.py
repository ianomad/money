"""Compose the 4-tab site from builder outputs: python3 scripts/compose.py

Builders write SOURCE pages (not served; see scripts/site_dir.sh + docs/_redirects):
  build.py -> docs/savings.html   build_yields.py -> docs/world.html
  build_crypto.py -> docs/crypto.html   build_economy.py -> docs/economy.html
  build_insights.py -> docs/insights.html   daily card routine -> docs/daily.html
This writes the SERVED pages: docs/index.html (Rates: US savings + World views),
docs/markets.html (Daily, stock notes, crypto, economy), docs/notes.html, and fixes nav in cards.html.
Every builder calls this at the end; deploy.yml runs it again before deploying. Idempotent.
"""
import re, hashlib, json, sys
from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parent))
from digest import digest, compact_insights, strip_tags, DIGEST_CSS, DIGEST_JS
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT/'docs'
def dj(n): return json.loads((ROOT/'data'/n).read_text())
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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="https://money.ilyusha.xyz{url}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz{url}"><meta name="twitter:card" content="summary"><link rel="icon" href="/favicon.ico?v=6" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png?v=6"><link rel="apple-touch-icon" href="/apple-touch-icon.png?v=6"><link rel="stylesheet" href="/styles.css"><script src="/analytics.js" defer></script>{scripts}{TUCK_CSS}{extra_head}</head>
<body><header><a class="brand" href="/"><img class="brand-mark" src="/favicon.svg?v=6" width="32" height="32" style="border-radius:6px" alt="">money<span class="brand-by">/ by ilyusha</span></a>{nav(cur)}<a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
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
yd = dj('yields.json'); best = []
for c in yd['countries']:
    pr = max(c['products'], key=lambda x: x['rate']); best.append((c, pr))
best.sort(key=lambda t: -t[1]['rate'])
kg = next(((c, pr) for c, pr in best if c.get('featured')), best[0])
world_hero = digest('world-top', 'WORLD / BANK DEPOSITS ABROAD',
    'Banks abroad pay far more than US savings, but in their own currency, so a falling currency can wipe out the extra interest.',
    ('Standout: steady currency', f"{kg[1]['rate']:g}%", f"{kg[0]['name']} · {kg[1]['bank']}", f"{kg[1]['product']}, {kg[1]['term']}, in {kg[1]['currency']}. {kg[0]['insurance'].split('(')[0].strip()}."),
    ('Country', 'Best rate', 'Bank, term, currency'),
    [(c['name'], pr['bank'], f"{pr['rate']:g}%", f"{pr['product']} · {pr['term']} · {pr['currency']}") for c, pr in best])
world_rest = tuck(wdm[wdm.index(sec(wdm, 'hero')) + len(sec(wdm, 'hero')):], 'Bank-by-bank details, the $500k Kyrgyzstan example, and how foreigners open accounts')
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

idx = page('Money — rates at home and abroad', desc, '/', 'rates', body + DIGEST_JS, head_styles(wd) + DIGEST_CSS, '<script src="/app.js" defer></script>')
for asset in ('styles.css', 'app.js', 'analytics.js', 'favicon.svg'):
    v = hashlib.sha256((D/asset).read_bytes()).hexdigest()[:10]
    idx = idx.replace(f'"/{asset}"', f'"/{asset}?v={v}"')
(D/'index.html').write_text(lazyimg(idx))

# ---------- Markets ----------
dy, ins, cr, ec = rd('daily.html'), rd('insights.html'), rd('crypto.html'), rd('economy.html')
dym, insm, crm, ecm = main(dy), main(ins), main(cr), main(ec)
cy = sec(svm, 'crypto-rates').replace('<div class="rows">', '<div class="rows">', 1)
cj = dj('crypto.json'); coins = sorted(cj['coins'], key=lambda c: c['market_cap_rank'])
def money(v): return f'${v/1e12:.2f}T' if v >= 1e12 else (f'${v/1e9:.0f}B' if v >= 1e9 else f'${v:,.0f}')
def px(v): return f'${v:,.0f}' if v >= 100 else (f'${v:,.2f}' if v >= 1 else f'${v:.4f}')
btc = coins[0]; tot = cj['global']['totalMarketCapUsd']
crypto_block = ('<div id="crypto">' + digest('crypto-top', 'CRYPTO / BY MARKET VALUE',
    f"Bitcoin alone is {cj['global']['btcDominance']:.0f}% of the {money(tot)} crypto market; most coins move with it.",
    ('Biggest coin', px(btc['current_price']), f"{btc['name']} ({btc['symbol'].upper()})", f"{btc['price_change_percentage_24h']:+.1f}% in 24h · worth {money(btc['market_cap'])} in total. Prices from CoinGecko."),
    ('Coin', 'Price', '24h move · total value'),
    [(c['name'], c['symbol'].upper(), px(c['current_price']), f"{c['price_change_percentage_24h']:+.1f}% · {money(c['market_cap'])}") for c in coins])
    + tuck(cy, 'Crypto & stablecoin yields (moved from Rates)').replace('<details class="tuck">', '<details class="tuck" id="crypto-yields">', 1) + '</div>')
ej = dj('economy.json'); gv = ej['gdp']['values']; world = sum(v['value'] for v in gv.values() if v.get('value'))
top = sorted([v for v in gv.values() if v.get('value')], key=lambda v: -v['value'])[:20]
def bn(v): return f'${v/1000:.1f}T' if v >= 1000 else f'${v:,.0f}B'
econ_block = ('<div id="economy">' + digest('economy-top', f"ECONOMY / GDP {ej['gdp']['year']}",
    f"The US and China together make up {(top[0]['value']+top[1]['value'])/world*100:.0f}% of the world economy.",
    ('Biggest economy', bn(top[0]['value']), top[0]['name'], f"{top[0]['value']/world*100:.0f}% of world GDP. IMF World Economic Outlook, {ej['gdp']['release'].split('(')[-1].rstrip(')')}."),
    ('Country', 'GDP', 'Share of world'),
    [(v['name'], 'IMF estimate' if v.get('estimate') else 'IMF', bn(v['value']), f"{v['value']/world*100:.1f}% of world") for v in top])
    + lazytuck(sec(ecm, 'map'), 'World GDP map', 'gdp-map') + lazytuck(sec(ecm, 'flows'), 'Investment flows (FDI)', 'fdi') + '</div>')
jump = '<p class="jump"><a href="#daily">Today’s card</a><a href="#stocks">Stock notes</a><a href="#crypto">Crypto</a><a href="#economy">Economy</a></p>'
mk_js = LAZY_JS + '''<script>(()=>{const h=location.hash.slice(1);if(!h)return;const go=()=>{const el=document.getElementById(h);if(el){const d=el.closest('details');if(d)d.open=true;setTimeout(()=>el.scrollIntoView(),50)}};document.getElementById(h)?go():window.__loadAllFrags().then(go)})();</script>'''
brief = sec(dym, 'brief'); daily_m = dym.replace(brief, tuck(brief, 'The full story behind today’s card'))
stocks = sec(insm, 'stocks'); n_st = len(re.findall(r'<li class="insight', stocks))
stocks_c = ('<section class="digest" id="stocks"><p class="eyebrow"><span class="dot"></span> STOCK NOTES</p><h2 class="takeaway">'
    f'{n_st} short notes on stocks and funds, each backed by a company filing. Tap one for the numbers and the risk.</h2>'
    + compact_insights(re.search(r'<ol class="insight-list">.*?</ol>', stocks, re.S).group(0)) + '</section>')
body = f'<div id="daily">{daily_m}</div>{jump}{stocks_c}{crypto_block}{econ_block}{mk_js}{DIGEST_JS}'
desc = re.search(r'<meta name="description" content="([^"]*)"', dy).group(1)
mk = page('Money — markets', desc, '/markets', 'markets', body, head_styles(dy) + head_styles(cr) + head_styles(ec) + head_styles(ins) + DIGEST_CSS)
(D/'markets.html').write_text(lazyimg(mk))

# ---------- Notes ----------
ib = sec(insm, 'insights'); lis = re.findall(r'<li class="insight[^"]*">.*?</div></li>', ib, re.S)
first_h = strip_tags(re.search(r'<h3>(.*?)</h3>', lis[0], re.S).group(1)) if lis else ''
notes_m = ('<section class="digest" id="insights"><p class="eyebrow"><span class="dot"></span> NOTES / CASH, TAX, CREDIT</p>'
    f'<h2 class="takeaway">{len(lis)} money moves, ranked by how many dollars they are worth on a big balance.</h2>'
    f'<div class="pick"><span class="k">Biggest one</span><span class="w">{first_h}</span></div>'
    + compact_insights(re.search(r'<ol class="insight-list">.*?</ol>', ib, re.S).group(0))
    + '<p>Stock notes are on <a href="/markets#stocks">Markets</a>.</p></section>')
desc = re.search(r'<meta name="description" content="([^"]*)"', ins).group(1)
(D/'notes.html').write_text(lazyimg(page('Money — notes', desc, '/notes', 'notes', notes_m, head_styles(ins) + DIGEST_CSS)))

# ---------- nav everywhere ----------
cards = rd('cards-src.html'); cm = main(cards)
crows = []
for a in re.findall(r'<article class="provider-row" data-name.*?</article>', sec(cm, 'cards'), re.S):
    g = lambda pat: (re.search(pat, a, re.S) or [None, ''])[1]
    crows.append((strip_tags(g(r'<h3[^>]*>(.*?)</h3>')), strip_tags(g(r'</h3><p>(.*?)</p>')), float(g(r'data-everyday="([\d.]+)"') or 0), float(g(r'data-best="([\d.]+)"') or 0), strip_tags(g(r'<div class="terms"><p>(.*?)</p>'))))
crows.sort(key=lambda r: (-r[2], -r[3]))
flat = next((r for r in crows if r[1].strip() == '$0 fee'), crows[0])
cards_d = digest('cards-top', 'CARDS / CASH BACK',
    f"For one card that earns on everything, {flat[0]} pays a flat {flat[2]:g}% with no annual fee; category cards pay more only where you spend a lot.",
    ('Simple pick', f'{flat[2]:g}%', flat[0], flat[4].split('. ')[0] + '.'),
    ('Card', 'On everything', 'Best rate · what to know'),
    [(n, sub, f'{ev:g}%', f'Up to {bs:g}% · ' + t.split('. ')[0] + '.') for n, sub, ev, bs, t in crows])
cards_body = cards_d + tuck(sec(cm, 'winners'), 'Best card for each spending category') + tuck(sec(cm, 'cards'), 'All cards, with filters and full terms') + DIGEST_JS
cards_out = cards.replace(cm, cards_body).replace('</head>', DIGEST_CSS + TUCK_CSS + '</head>', 1)
(D/'cards.html').write_text(lazyimg(setnav(cards_out, 'cards')))
for n in ('cards-src.html', 'savings.html', 'world.html', 'crypto.html', 'economy.html', 'insights.html', 'daily.html'):
    (D/n).write_text(setnav(rd(n), 'x'))
print('Composed index.html, markets.html, notes.html')
