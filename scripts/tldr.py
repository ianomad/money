"""Guide pages (Oct 27 2026 stories pass): 3-bullet TL;DR card built from the page's own data-driven takeaways,
lead and long section text behind Details. Runs last in ui3.finalize; idempotent; only touches pages with section.digest."""
import re
def _txt(s): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()
JS = ('<script>(()=>{const o=()=>{const id=decodeURIComponent(location.hash.slice(1));const el=id&&document.getElementById(id);'
      'if(!el)return;let d=el.closest("details");while(d){d.open=true;d=d.parentElement&&d.parentElement.closest("details")}el.scrollIntoView()};'
      'addEventListener("hashchange",o);o()})()</script>')
def apply(h):
    if 'class="digest"' not in h or 'class="fc tldr"' in h: return h
    tk = [_txt(t) for t in re.findall(r'<h2 class="takeaway">(.*?)</h2>', h, re.S)][:3]
    if len(tk) < 3: return h
    card = ('<article class="fc tldr"><p class="fc-k">TL;DR</p><ul>' + ''.join(f'<li>{t}</li>' for t in tk) + '</ul></article>')
    def lead(m): return m.group(1) + f'<details class="i"><summary>In full</summary><div class="dbody"><p class="lead">{m.group(2)}</p></div></details>'
    h = re.sub(r'(<section class="pagehead">.*?</h1>)<p class="lead">(.*?)</p>', lead, h, count=1, flags=re.S)
    h = re.sub(r'(<section class="pagehead">.*?</section>)', lambda m: m.group(1) + card, h, count=1, flags=re.S)
    def sec(m):
        body = m.group(3)
        if len(_txt(body).split()) < 25: return m.group(0)
        return m.group(1) + m.group(2) + f'<details class="i"><summary>Details</summary><div class="dbody">{body}</div></details></section>'
    h = re.sub(r'(<section class="digest"[^>]*>)(.*?<h2 class="takeaway">.*?</h2>)(.*?)</section>', sec, h, flags=re.S)
    return h.replace('</body>', JS + '</body>', 1)
