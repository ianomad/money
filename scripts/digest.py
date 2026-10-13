"""Shared 'easy to digest' components (pattern from the US savings page):
takeaway sentence + top pick card + short top-N table with Show all + everything else folded."""
import re, html
e = lambda s: html.escape(str(s), quote=True)
DIGEST_CSS = '''<style>.digest{margin:2rem 0}.digest .takeaway{font-size:1.35rem;line-height:1.35;margin:.3rem 0 1rem;max-width:46rem}
.digest .pick{display:flex;flex-wrap:wrap;align-items:baseline;gap:.3rem 1rem;border:1px solid rgba(127,127,127,.3);border-radius:1rem;padding:1rem 1.2rem;margin:0 0 1rem}
.digest .pick .k{font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;opacity:.7;width:100%}.digest .pick .n{font-size:2.2rem;font-weight:700;line-height:1}.digest .pick .w{font-weight:600}.digest .pick .c{width:100%;opacity:.8;font-size:.95rem;margin:0}
.dg-rows{border-top:1px solid rgba(127,127,127,.25)}.dg-row{display:grid;grid-template-columns:1.6fr .8fr 2fr;gap:.4rem 1rem;padding:.7rem .2rem;border-bottom:1px solid rgba(127,127,127,.25);align-items:baseline}
.dg-row h3{font-size:1rem;margin:0}.dg-row .sub{font-size:.85rem;opacity:.7;margin:.1rem 0 0}.dg-row .v{font-weight:700;font-size:1.15rem}.dg-row .t{font-size:.9rem;opacity:.85;margin:0}.dg-head{font-size:.75rem;letter-spacing:.08em;opacity:.6;text-transform:uppercase}
.dg-rows.collapsed .dg-row:nth-child(n+8){display:none}@media(max-width:640px){.dg-row{grid-template-columns:1fr auto}.dg-row .t{grid-column:1/-1}.dg-head{display:none}}
.insight-list.compact .insight{margin:.2rem 0;padding:.6rem 0;border-bottom:1px solid rgba(127,127,127,.2)}.insight-list.compact .insight h3{font-size:1.02rem;margin:.1rem 0}.insight-list.compact details summary{cursor:pointer;font-size:.9rem;opacity:.8}</style>'''
DIGEST_JS = '''<script>document.querySelectorAll('.dg-more').forEach(b=>b.onclick=()=>{b.previousElementSibling.classList.remove('collapsed');b.remove()})</script>'''
def digest(id_, eyebrow, takeaway, pick, cols, rows, n=7):
    """pick=(label, number, who, catch); rows=[(name, sub, value, note)]; cols=(name, value, note) headers"""
    pk = pick if isinstance(pick, str) else f'<div class="pick"><span class="k">{e(pick[0])}</span><span class="n">{e(pick[1])}</span><span class="w">{e(pick[2])}</span><p class="c">{e(pick[3])}</p></div>' if pick else ''
    head = f'<div class="dg-row dg-head"><span>{e(cols[0])}</span><span>{e(cols[1])}</span><span>{e(cols[2])}</span></div>'
    body = ''.join(f'<div class="dg-row"><div><h3>{e(a)}</h3><p class="sub">{e(b)}</p></div><span class="v">{e(c)}</span><p class="t">{e(d)}</p></div>' for a,b,c,d in rows)
    more = f'<button type="button" class="show-all dg-more">Show all {len(rows)}</button>' if len(rows) > n else ''
    return (f'<section class="digest" id="{id_}"><p class="eyebrow"><span class="dot"></span> {e(eyebrow)}</p><h2 class="takeaway">{e(takeaway)}</h2>{pk}'
            f'{head}<div class="dg-rows{" collapsed" if len(rows)>n else ""}">{body}</div>{more}</section>')
def compact_insights(block):
    """Each <li class="insight">: keep rank/tag/headline visible, fold the rest."""
    def one(m):
        li = m.group(0)
        hm = re.search(r'(<h3>.*?</h3>)(.*)</div></li>$', li, re.S)
        if not hm: return li
        pre = li[:hm.start(1)]
        return f'{pre}{hm.group(1)}<details><summary>Why, the numbers, and the catch</summary>{hm.group(2)}</details></div></li>'
    out = re.sub(r'<li class="insight[^"]*">.*?</div></li>', one, block, flags=re.S)
    return out.replace('class="insight-list"', 'class="insight-list compact"')
def strip_tags(s): return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

# ---------- redesign2: Savings-style top card, stat tiles, mini charts, note cards ----------
UI_CSS = '''<style>.tc{max-width:640px;margin:0 0 1.4rem}.tc .share-card{margin:0 0 12px}.tc-cta{display:inline-block;margin-top:14px;padding:9px 16px;border-radius:99px;background:#c9a24a;color:#111!important;font:600 13px/1 -apple-system,BlinkMacSystemFont,sans-serif}.tc-cta:hover{background:#e0bb5e}
.tc-facts{display:flex;flex-wrap:wrap;gap:6px 18px;margin:10px 0 0;padding:10px 0 0;border-top:1px solid #f6f1e722;font:11px var(--mono);color:#f6f1e7bb}.tc-facts b{color:#f6f1e7;font-weight:600}
.bar i.neg{background:var(--orange)}.bar-row strong.neg{color:var(--orange)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0 22px}.tile{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 6px 18px #1f241c08;display:block}.tile .k{font:10px var(--mono);letter-spacing:.8px;text-transform:uppercase;color:var(--muted)}.tile .n{display:block;font:normal 30px/1.1 Georgia,serif;letter-spacing:-1px;margin:6px 0 2px}.tile .d{font:600 12px var(--mono)}.up{color:var(--green)}.down{color:var(--orange)}.tile .s{display:block;font-size:11px;color:var(--muted);margin-top:4px}
.vgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 24px}.vcard{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 8px 24px #1f241c0c}.vcard h3{font:normal 21px/1.2 Georgia,serif;margin:2px 0 4px}.vcard .one{font-size:12px;color:var(--muted);margin:0 0 12px}.vcard .more{font-size:12px;color:var(--orange)}
.notes-intro{max-width:720px;margin:28px 0 8px}.notes-intro h1{font-size:44px;margin-bottom:10px}.notes-intro p{font-size:15px;color:var(--muted);margin:0 0 6px}
.ncards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:18px 0 30px;padding:0;list-style:none}.ncard{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 8px 24px #1f241c0c}.ncard .meta{font:10px var(--mono);letter-spacing:.8px;text-transform:uppercase;color:var(--muted);display:flex;justify-content:space-between}.ncard .n{display:block;font:normal 34px/1.1 Georgia,serif;letter-spacing:-1px;color:var(--green);margin:10px 0 6px}.ncard h3{font-size:14px;line-height:1.45;font-weight:600;margin:0 0 6px}.ncard h3 em{color:inherit}.ncard .detail-body{font-size:12px}
@media(max-width:760px){.vgrid{grid-template-columns:1fr}.tiles{grid-template-columns:1fr 1fr}.tile{padding:10px 12px}.tile .n{font-size:22px}.tile .s{display:none}.tiles{gap:8px}.notes-intro h1{font-size:32px}}</style>'''
def topcard(eyebrow, number, who, catch, date, facts=(), cta=None, bars=None, caption=''):
    """The US-savings top card (black share-card + optional bar chart). facts=[(k,v)], cta=(text,href), bars=[(name,value,label,href)]"""
    f = ''.join(f'<span>{e(k)} <b>{e(v)}</b></span>' for k, v in facts)
    f = f'<p class="tc-facts">{f}</p>' if f else ''
    c = f'<a class="tc-cta" href="{e(cta[1])}">{e(cta[0])} →</a>' if cta else ''
    out = (f'<div class="tc"><section class="share-card"><p class="eyebrow">{e(eyebrow)}</p><p class="share-rate">{e(number)}</p>'
           f'<p class="share-who">{e(who)}</p><p class="share-catch">{e(catch)}</p>{f}<p class="share-date">{e(date)} · money.ilyusha.xyz</p>{c}</section>')
    if bars: out += barchart(bars, caption)
    return out + '</div>'
def barchart(bars, caption):
    m = max(abs(b[1]) for b in bars) or 1
    rows = ''.join(f'<a class="bar-row" href="{e(h)}"><b>{e(n)}</b><span class="bar"><i{" class=neg" if v<0 else ""} style="width:{max(3,abs(v)/m*100):.0f}%"></i></span><strong{" class=neg" if v<0 else ""}>{e(l)}</strong></a>' for n, v, l, h in bars)
    return f'<figure class="share-chart"><figcaption>{e(caption)}</figcaption>{rows}</figure>'
def tile(k, n, d=None, s='', href=None):
    dd = f'<span class="d {"up" if d>=0 else "down"}">{"▲" if d>=0 else "▼"} {abs(d):.1f}%</span>' if d is not None else ''
    tag = f'a href="{e(href)}"' if href else 'div'
    return f'<{tag} class="tile"><span class="k">{e(k)}</span><span class="n">{e(n)}</span>{dd}<span class="s">{e(s)}</span></{tag.split()[0]}>'
