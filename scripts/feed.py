"""Feed components (Oct 27 2026 'stories' pass): short visual insight cards, swipe rows with dots, bars, scenario bars.
Every number passed in comes from the data files via the page builders; nothing here is hardcoded data."""
from html import escape as e

def card(kicker, big, line='', catch='', foot='', viz='', actions='', cls='', unit='', attrs=''):
    return (f'<article class="fc {cls}"{attrs}><p class="fc-k">{kicker}</p><p class="fc-big">{big}{f"<small>{unit}</small>" if unit else ""}</p>'
            + (f'<p class="fc-line">{line}</p>' if line else '') + viz
            + (f'<div class="fc-catch"><span>{catch}</span></div>' if catch else '') + (f'<p class="fc-foot">{foot}</p>' if foot else '') + actions + '</article>')

def swipe(cards, label, title=''):
    n = len(cards)
    dots = ''.join(f'<i{" class=on" if i == 0 else ""}></i>' for i in range(n))
    return (f'<section class="sw" data-swipe aria-label="{e(label)}">' + (f'<h2 class="fh">{title}</h2>' if title else '')
            + f'<div class="sw-track" tabindex="0" role="group" aria-roledescription="carousel" aria-label="{e(label)}">'
            + ''.join(f'<div class="sw-it" role="group" aria-roledescription="slide" aria-label="{i + 1} of {n}">{c}</div>' for i, c in enumerate(cards))
            + f'</div><div class="sw-nav"><button type="button" class="sw-b" data-d="-1" aria-label="Previous">‹</button><span class="dots" aria-hidden="true">{dots}</span>'
            + f'<span class="sr" aria-live="polite" data-pos>1 of {n}</span><button type="button" class="sw-b" data-d="1" aria-label="Next">›</button></div></section>')

def bars(items, unit_label=''):
    """items: [(label, value, shown, hi)] — bars scaled to the largest |value|; negatives drawn muted."""
    mx = max((abs(v) for _, v, _, _ in items), default=1) or 1
    return ('<ul class="fbars">' + ''.join(
        f'<li class="{"hi" if hi else ""}{" neg" if v < 0 else ""}"><span class="l">{l}</span><span class="b"><i style="--w:{max(2, abs(v) / mx * 100):.1f}%"></i></span><b>{s}</b></li>'
        for l, v, s, hi in items) + '</ul>' + (f'<p class="fbars-u">{unit_label}</p>' if unit_label else ''))

def more(summary, body, cls='i', open_=False, id_=''):
    return f'<details class="{cls}"{f" id={id_}" if id_ else ""}{" open" if open_ else ""}><summary>{summary}</summary><div class="dbody">{body}</div></details>'

def head(h, sub, tag='h1'):
    return f'<section class="fhead"><{tag}>{h}</{tag}><p class="sub">{sub}</p></section>'

CSS = ''  # styles live in scripts/theme.css (theme.apply strips inline <style> layers)

JS = '''<script>(()=>{const rm=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';document.querySelectorAll('[data-swipe]').forEach(s=>{const t=s.querySelector('.sw-track'),it=[...t.children],d=[...s.querySelectorAll('.dots i')],bs=s.querySelectorAll('.sw-b'),pos=s.querySelector('[data-pos]'),nav=s.querySelector('.sw-nav');
const vis=()=>{const r=t.getBoundingClientRect();return it.map(c=>{const b=c.getBoundingClientRect();return Math.min(b.right,r.right)-Math.max(b.left,r.left)>=b.width*.6})};
const up=()=>{const v=vis();let f=v.indexOf(true),l=v.lastIndexOf(true);if(f<0){f=l=0}d.forEach((x,j)=>x.classList.toggle('on',j>=f&&j<=l));const end=t.scrollLeft+t.clientWidth>=t.scrollWidth-4;bs[0].disabled=t.scrollLeft<4;bs[1].disabled=end;if(nav)nav.hidden=t.scrollWidth<=t.clientWidth+4;if(pos)pos.textContent=(f===l?(f+1):(f+1)+'–'+(l+1))+' of '+it.length;return[f,l]};
const go=i=>{i=Math.max(0,Math.min(it.length-1,i));t.scrollTo({left:t.scrollLeft+it[i].getBoundingClientRect().left-t.getBoundingClientRect().left-2,behavior:rm()})};
bs.forEach(b=>b.onclick=()=>{const[f,l]=up(),n=l-f+1;go(+b.dataset.d>0?l+1:f-n)});
let q=0;t.addEventListener('scroll',()=>{if(!q){q=1;requestAnimationFrame(()=>{q=0;up()})}},{passive:true});addEventListener('resize',up);s.addEventListener('toggle',up,true);
t.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();bs[e.key==='ArrowRight'?1:0].click()}});up()});
document.querySelectorAll('[data-open]').forEach(a=>a.addEventListener('click',e=>{const d=document.getElementById(a.dataset.open);if(d){e.preventDefault();d.open=true;d.scrollIntoView({block:'start',behavior:rm()});const f=d.querySelector('input,select');f&&setTimeout(()=>f.focus({preventScroll:true}),350)}}))})();</script>'''
