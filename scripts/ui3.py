"""ui3: one design system + performance pass applied to every served page (called by compose.py).
- inlines styles.css + the ui3 override layer (no render-blocking CSS)
- swaps the 176KB gtag.js for a ~1KB cookieless GA4 page_view beacon (same property)
- trims header clutter; moves legal fine print to the footer"""
import re
from pathlib import Path
D = Path(__file__).resolve().parents[1]/'docs'
GA = 'G-7WGRRRQQRB'
BEACON = ('<script>addEventListener("load",function(){if(location.hostname!=="money.ilyusha.xyz"||navigator.doNotTrack==="1")return;'
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
    h = re.sub(r'<script src="/?analytics\.js[^"]*" defer></script>', lambda m: BEACON, h)
    fine = re.findall(r'<p class="econ-note crypto-plain">(General information.*?)</p>', h, re.S)
    h = re.sub(r'<p class="econ-note crypto-plain">General information.*?</p>', '', h, flags=re.S)
    note = fine[0] if fine else 'General information, not financial advice. Rates and terms change; confirm with the provider before you move money.'
    h = h.replace('</footer>', f'<p class="fine">{note}</p></footer>', 1)
    h = h.replace('<footer>', '<footer>', 1)
    return h
