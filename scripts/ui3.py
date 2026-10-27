"""ui3: one design system + performance pass applied to every served page (called by compose.py).
- inlines styles.css + the ui3 override layer (no render-blocking CSS)
- loads the standard GA4 gtag.js via /analytics.js exactly once per page (no hand-rolled beacon: it broke sessions/engagement/attribution)
- trims header clutter; moves legal fine print to the footer"""
import re
from pathlib import Path
D = Path(__file__).resolve().parents[1]/'docs'
GA = 'G-7WGRRRQQRB'
BEACON = ('<script>addEventListener("load",function(){if(location.hostname!=="getmoneybeast.com"||navigator.doNotTrack==="1")return;'
 'var k="mb_cid",c;try{c=localStorage.getItem(k)||(Math.random()*1e9|0)+"."+(Date.now()/1e3|0);localStorage.setItem(k,c)}catch(e){c=(Math.random()*1e9|0)+".1"}'
 'var p=new URLSearchParams({v:"2",tid:"'+GA+'",cid:c,en:"page_view",_s:"1",sid:String(Date.now()/1e3|0),seg:"1",dl:location.origin+location.pathname,dr:document.referrer.split(/[?#]/)[0],dt:document.title,npa:"1"});'
 'navigator.sendBeacon?navigator.sendBeacon("https://www.google-analytics.com/g/collect?"+p):fetch("https://www.google-analytics.com/g/collect?"+p,{method:"POST",mode:"no-cors",keepalive:true})})</script>')
UI3 = r'''
:root{--paper:#fbfaf6;--ink:#17181a;--muted:#5f6062;--line:#e6e2d6;--gold:#8a6a1f;--orange:#9b3b22;--green:#8a6a1f;--serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
html{scroll-padding-top:16px}body{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--paper);color:var(--ink);-webkit-font-smoothing:antialiased}
header,main,footer{max-width:760px!important;padding:0 20px!important;margin:0 auto}
header{height:auto!important;padding-top:18px!important;padding-bottom:14px!important;flex-wrap:wrap;gap:12px 20px!important}
.brand{font:600 20px/1 var(--serif)!important;letter-spacing:-.3px!important}.brand-by,.personal{display:none!important}
nav{gap:4px!important;font-size:15px!important}nav a{padding:6px 12px!important;border:0!important;border-radius:99px;color:var(--muted)!important;background:none!important}nav a[aria-current=page]{color:var(--ink)!important;background:#efe9da!important;font-weight:600}
a:hover{color:var(--gold)}:focus-visible{outline-color:var(--gold)}
h1,h2,.takeaway,.share-rate,.tile .n,.ncard .n,.vcard h3{font-family:var(--serif)!important}
h1{font-size:clamp(32px,6vw,44px)!important;line-height:1.1!important;letter-spacing:-.8px!important;margin:0 0 14px!important}
h2{font-size:clamp(24px,4.5vw,30px);line-height:1.2;letter-spacing:-.4px;font-weight:600}
.digest .takeaway{font-size:clamp(22px,4.2vw,27px)!important;font-weight:500!important;line-height:1.3!important;margin:4px 0 18px!important}
h3{font-size:16px;line-height:1.35}
.eyebrow{font:600 12px/1.5 var(--mono)!important;letter-spacing:1.2px!important;color:var(--gold)!important;text-transform:uppercase;margin:0 0 8px!important}.dot{display:none!important}
em{color:var(--gold)}p{max-width:68ch}
.hero{display:block!important;padding:32px 0 8px!important}.intro{font-size:16px!important}.snapshot{display:none!important}
.digest,.tc{margin:28px 0 36px!important;max-width:none!important}
.share-card{border-radius:18px!important;padding:24px!important;background:#141414!important}.share-card .eyebrow{color:#d8b15a!important}.share-rate{font-size:clamp(56px,14vw,76px)!important;font-weight:500!important;color:#f3d27a!important;letter-spacing:-2px!important}
.share-who{font-size:18px!important}.share-catch{font-size:15px!important;line-height:1.55!important;opacity:.85}.share-date,.tc-facts{font-size:12px!important}
.tc-cta{background:linear-gradient(180deg,#e6c46a,#c69b3c)!important;font-size:15px!important;padding:12px 20px!important}
.share-chart{border:1px solid var(--line)!important;border-radius:16px!important;padding:16px 18px!important;background:#fff!important;margin:12px 0 0!important}.share-chart figcaption{font:600 12px var(--mono);letter-spacing:1px;text-transform:uppercase;color:var(--muted)}
.bar-row{font-size:14px!important;padding:5px 0!important}.bar i{background:var(--gold)!important}.bar i.neg{background:var(--orange)!important}.bar-row strong{color:var(--ink)!important}.bar-row strong.neg{color:var(--orange)!important}
.dg-row{padding:14px 2px!important;border-color:var(--line)!important}.dg-row h3{font-size:16px!important;font-weight:600}.dg-row .sub,.dg-row .t{font-size:14px!important;color:var(--muted);opacity:1!important}.dg-row .v{font-size:18px!important}.dg-head{font:600 12px var(--mono)!important;color:var(--muted)}
.show-all{font-size:15px!important;padding:10px 18px!important;border-color:var(--line)!important;background:#fff!important}
.tuck{border:1px solid var(--line)!important;border-radius:14px!important;background:#fff;padding:14px 18px!important;margin:12px 0!important}.tuck>summary{font-weight:600;font-size:16px;list-style:none}.tuck>summary::-webkit-details-marker{display:none}.tuck>summary:after{content:" +";color:var(--gold)}.tuck[open]>summary:after{content:" −"}
.tiles{grid-template-columns:repeat(3,1fr)!important;gap:10px!important}.tile,.vcard,.ncard{box-shadow:none!important;border-color:var(--line)!important;border-radius:14px!important}.tile .k,.ncard .meta{font-size:11px!important}.tile .n{font-size:28px!important}.tile .d{font-size:13px!important}.up{color:#2f6b45!important}.down{color:var(--orange)!important}
.vgrid{grid-template-columns:1fr!important}.vcard .one,.vcard .more{font-size:14px!important}.vcard .more{color:var(--gold)!important}
.ncards{grid-template-columns:1fr!important}.ncard h3{font-size:16px!important}.ncard .n{color:var(--gold)!important}.ncard .detail-body{font-size:14px!important}
.toolbar{flex-wrap:wrap}.tools input,.tools select,.filters button{font-size:14px!important}
.provider-row{border-color:var(--line)!important}.provider h3{font-size:16px!important}.provider p,.terms,.checked,.mobile-label{font-size:13px!important}.rate{font-family:var(--serif)}
.view-tabs a{font-size:15px}.view-tabs a[aria-selected=true]{background:var(--ink)!important;color:var(--paper)!important}.view-tabs a[aria-selected=true] span{filter:none!important}
.jump,.hint,.result-count,.change-note,.toolbar,#daily .intro{display:none!important}.fit-line{font-size:16px;margin:14px 0 0}
footer{margin-top:56px!important;padding-top:24px!important;padding-bottom:40px!important;border-top:1px solid var(--line);font-size:13px!important;color:var(--muted);display:flex;flex-direction:column;gap:8px}
.fine{font-size:12px;color:var(--muted);margin:0}
header{background:none!important;border-bottom:1px solid var(--line)}.tracker-controls{background:none!important;padding:8px 0!important;margin:8px 0!important;position:static!important;box-shadow:none!important;border:0!important}
details>summary{color:var(--gold)!important;opacity:1!important}footer a{text-decoration:underline;text-underline-offset:3px}
@media(max-width:560px){.tiles{grid-template-columns:1fr 1fr!important}nav a{padding:6px 10px!important}header{gap:10px!important}}
'''
def mini(css): return re.sub(r'\s*([{};:,>])\s*', r'\1', re.sub(r'/\*.*?\*/', '', css, flags=re.S)).replace(';}', '}').strip()
def finalize(h):
    css = mini((D/'styles.css').read_text()) + mini(UI3)
    h = re.sub(r'<link rel="stylesheet" href="/?styles\.css[^"]*">', lambda m: '<style>'+css+'</style>', h, count=1)
    # Standard gtag.js via /analytics.js (host-gated, async gtag). Strip any old beacon or duplicate tag, then add exactly one.
    h = h.replace(BEACON, '')
    h = re.sub(r'<script>addEventListener\("load",function\(\)\{if\(location\.hostname!=="[^"]+".*?</script>', '', h, flags=re.S)
    tag = '<script src="/analytics.js" defer></script>'
    h = re.sub(r'<script src="/?analytics\.js[^"]*"[^>]*></script>', '', h)
    h = h.replace('</head>', tag + '</head>', 1) if '</head>' in h else h
    fine = re.findall(r'<p class="econ-note crypto-plain">(General information.*?)</p>', h, re.S)
    h = re.sub(r'<p class="econ-note crypto-plain">General information.*?</p>', '', h, flags=re.S)
    note = fine[0] if fine else 'General information, not financial advice. Rates and terms change; confirm with the provider before you move money.'
    h = h.replace('</footer>', f'<p class="fine">{note}</p></footer>', 1)
    h = h.replace('<footer>', '<footer>', 1)
    return h

# ---------- ui4: patterns from NerdWallet/Bankrate (badges, earnings calc, trust line), Robinhood/Yahoo (sticky nav, colored chips) ----------
UI4 = r'''
header{position:sticky;top:0;z-index:20;background:#fbfaf6!important}
.trust{font:12px/1.5 var(--mono);color:var(--muted);margin:14px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px}.trust b{color:#2f6b45;font-weight:600}
.badge{display:inline-block;font:600 11px/1 var(--mono);letter-spacing:.4px;text-transform:uppercase;color:var(--gold);background:#f4ecd6;border-radius:99px;padding:4px 8px;margin:4px 6px 0 0;vertical-align:middle}
.earn{border:1px solid var(--line);border-radius:16px;background:#fff;padding:14px 18px;margin:12px 0;font-size:16px;display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px}
.earn input{font:600 18px var(--serif);width:7.5em;padding:6px 10px;border:1px solid var(--line);border-radius:10px;background:var(--paper);color:var(--ink)}
.earn output{font:600 24px var(--serif);color:var(--gold)}.yr{display:block;font:12px var(--mono);color:var(--muted);font-weight:400}
.tile .d{display:inline-block;padding:2px 7px;border-radius:99px}.tile .d.up{background:#e6f0e9}.tile .d.down{background:#f7e6e0}
'''
EARN_JS = r'''<script>(()=>{const i=document.getElementById("earn-amt");if(!i)return;const m=+i.dataset.m,o=document.getElementById("earn-out"),top=parseFloat(i.dataset.r),f=n=>"$"+Math.round(n).toLocaleString("en-US"),els=[...document.querySelectorAll(i.dataset.sel)].filter(e=>/%/.test(e.textContent));els.forEach(e=>{e.dataset.r=parseFloat(e.textContent);e.insertAdjacentHTML("beforeend",'<span class="yr"></span>')});const u=()=>{const a=(+i.value.replace(/[^\d.]/g,"")||0)*m;o.textContent=f(a*top/100);els.forEach(e=>e.lastChild.textContent=f(a*e.dataset.r/100)+"/yr")};i.oninput=u;u()})()</script>'''
from datetime import date as _date
def ui4(h):
    if '<main' not in h or 'class="trust"' in h: return h
    path = re.search(r'<link rel="canonical" href="https://[^/"]+(/[a-z-]*)(?:\.html)?"', h)
    rates = 'data-view="us"' in h; cards = 'class="calc"' in h and bool(path) and path.group(1).startswith('/cards')  # was matching World's .calc sections -> stray card calculator on World
    today = _date.today().strftime('%b %-d, %Y')
    src = {True: 'Rates checked by hand against each bank’s own page'}.get(rates) or ('Card terms checked against issuer pages' if cards else 'Data from FRED (Fed, Treasury, EIA, Freddie Mac), BLS and CoinGecko')
    h = re.sub(r'(<main[^>]*>)', r'\1' + f'<p class="trust"><span><b>●</b> Updated {today}</span><span>{src}</span><span>No sponsored rankings</span></p>', h, count=1)
    if rates:
        rows = re.findall(r'<article id="(provider-[^"]+)" class="provider-row"[^>]*data-base="([\d.]+)" data-top="([\d.]+)"', h)
        if rows:
            tb = max(rows, key=lambda r: float(r[2]))[0]; bb = max(rows, key=lambda r: float(r[1]))[0]
            for pid, lab in ((tb, 'Highest advertised rate'), (bb, 'Highest standard rate')):
                h = re.sub(rf'(<article id="{pid}".*?</h3>)', lambda m: m.group(1) + f'<span class="badge">{lab}</span>', h, count=1, flags=re.S)
        r = re.search(r'class="share-rate">([\d.]+)%', h)
        if r:
            box = (f'<div class="earn"><label for="earn-amt">If you keep $</label><input id="earn-amt" inputmode="decimal" value="10,000" data-m="1" data-r="{r.group(1)}" data-sel=".rate.top strong,#stable-top .dg-row .v">'
                   f'<span>at the top rate, you earn</span><output id="earn-out"></output><span>a year.</span></div>')
            h = re.sub(r'(<section class="share-card" id="share">.*?</figure>)', lambda m: m.group(1) + box, h, count=1, flags=re.S)
    if cards:
        h = re.sub(r'(<div class="dg-rows[^"]*"><div class="dg-row"><div><h3>[^<]*</h3>)', r'\1<span class="badge">Highest rate</span>', h, count=1)
        w = re.search(r'class="share-who">([^<]*)<', h)
        if w: h = h.replace(f'<div class="dg-row"><div><h3>{w.group(1)}</h3>', f'<div class="dg-row"><div><h3>{w.group(1)}</h3><span class="badge">Best for one card</span>', 1)
        r = re.search(r'class="share-rate">([\d.]+)%', h)
        if r:
            box = (f'<div class="earn"><label for="earn-amt">If you spend $</label><input id="earn-amt" inputmode="decimal" value="2,000" data-m="12" data-r="{r.group(1)}" data-sel="#cards-top .dg-row .v">'
                   f'<span>a month, this card pays</span><output id="earn-out"></output><span>a year.</span></div>')
            h = re.sub(r'(<div class="tc">.*?</figure></div>)', lambda m: m.group(1) + box, h, count=1, flags=re.S)
    if 'id="earn-amt"' in h: h = h.replace('</body>', EARN_JS + '</body>', 1)
    return h.replace('</style>', mini(UI4) + '</style>', 1)
_fin3 = finalize
def finalize(h): return ui4(_fin3(h))

# ---------- X follow path (50-follower sprint, Oct 25 2026): header pill + footer line, GA4 'x_follow_click' via analytics.js ----------
X_URL = 'https://x.com/MoneyBeastHQ'
X_CSS = ('<style id="xf-css">.xfollow{font:600 12px/1 var(--mono);letter-spacing:.3px;white-space:nowrap;border:1px solid var(--line);border-radius:99px;padding:7px 11px;color:var(--ink)!important;margin-left:auto}'
         '.xfollow:hover{border-color:var(--gold);color:var(--gold)!important}.xline{font-size:14px;color:var(--ink);margin:0}.xline a{font-weight:600}'
         '@media(max-width:340px){.xfollow .xf-long{display:none}.xfollow{padding:6px 9px;font-size:11px}}</style>')
def xfollow(h):
    """Idempotent: adds the header pill and the footer line once per page."""
    if 'class="xfollow"' in h or '<header' not in h: return h
    pill = f'<a class="xfollow" href="{X_URL}" target="_blank" rel="noopener" data-x-follow="header">Follow<span class="xf-long"> on X</span> ↗</a>'
    line = f'<p class="xline">Daily market charts and calls on X: <a href="{X_URL}" target="_blank" rel="noopener" data-x-follow="footer">@MoneyBeastHQ ↗</a></p>'
    h = re.sub(r'(<header>.*?</nav>)', lambda m: m.group(1) + pill, h, count=1, flags=re.S)
    h = h.replace('<footer>', '<footer>' + line, 1)
    return h.replace('</head>', X_CSS + '</head>', 1)
_fin4 = finalize
def finalize(h): return xfollow(_fin4(h))

# ---------- Share cards (Oct 25 2026): large og:image / twitter card on every served page; images from scripts/build_og.py ----------
SITE = 'https://getmoneybeast.com'
OG_PAGES = {'/': 'home', '/markets': 'markets', '/cards': 'cards', '/cards.html': 'cards', '/best-hysa': 'best-hysa',
            '/best-nofee-cards': 'best-nofee-cards', '/tbills-vs-savings-california': 'tbills-vs-savings-california',
            '/pay-property-tax-credit-card': 'pay-property-tax-credit-card'}
def ogtags(h):
    """Idempotent: strips old og:image*/twitter:* tags and writes one fresh set. Unknown pages use the home card."""
    if '</head>' not in h: return h
    m = re.search(r'<link rel="canonical" href="https://(?:money\.ilyusha\.xyz|getmoneybeast\.com)(/[^"]*)"', h)
    name = OG_PAGES.get(m.group(1) if m else '/', 'home')
    try:
        import json; alt = json.loads((D/'og'/'meta.json').read_text())[name]['alt']
    except Exception: alt = 'Money, an independent tracker of savings rates, markets and cards at getmoneybeast.com'
    alt = alt.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
    h = re.sub(r'<meta (?:property="og:image[^"]*"|name="twitter:[^"]*")[^>]*>', '', h)
    img = f'{SITE}/og/{name}.png'
    tags = (f'<meta property="og:image" content="{img}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200">'
            f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="{alt}"><meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:site" content="@MoneyBeastHQ"><meta name="twitter:image" content="{img}"><meta name="twitter:image:alt" content="{alt}">')
    if 'property="og:url"' in h: return re.sub(r'(<meta property="og:url"[^>]*>)', lambda mm: mm.group(1) + tags, h, count=1)
    return h.replace('</head>', tags + '</head>', 1)
_fin5 = finalize
def finalize(h): return ogtags(_fin5(h))

# ---------- theme (revamp Oct 26 2026): one design system + consistent header/nav/footer on every served page ----------
from theme import apply as _theme
_fin6 = finalize
def finalize(h): return _theme(_fin6(h))

# ---------- SEO metadata (Oct 26 2026): titles, descriptions, JSON-LD, related tools on guides ----------
from seo_meta import apply as _seo
_fin7 = finalize
def finalize(h): return _seo(_fin7(h))
