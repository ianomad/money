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
    pk = f'<div class="pick"><span class="k">{e(pick[0])}</span><span class="n">{e(pick[1])}</span><span class="w">{e(pick[2])}</span><p class="c">{e(pick[3])}</p></div>' if pick else ''
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
