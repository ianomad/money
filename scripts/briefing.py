"""Home "What changed" briefing. Items are real diffs between dated snapshots in
data/history.json (see history.py). Topics and last visit live only in localStorage."""
import json, datetime, re
from html import escape as e
import history

TOPICS = [('savings', 'US savings'), ('world', 'Abroad'), ('cards', 'Cards'), ('tbills', 'T-bills')]

def fd(s): d = datetime.date.fromisoformat(s); return f'{d:%b} {d.day}'

def host(u):
    m = re.match(r'https?://(?:www\.)?([^/]+)', u or ''); return m.group(1) if m else ''

def item(x):
    src = f'<a href="{e(x["a"])}" target="_blank" rel="noopener">{e(host(x["a"]))} ↗</a>' if x.get('a') else ''
    arrow = '' if 'd' not in x else ('<b class="up" aria-label="up">▲</b> ' if x['d'] else '<b class="dn" aria-label="down">▼</b> ')
    return (f'<li data-t="{x["t"]}" data-d="{x["date"]}"><time datetime="{x["date"]}">{fd(x["date"])}</time>'
            f'<p class="bh">{arrow}{e(x["h"])}</p>' + (f'<p class="bw">{e(x["w"])}</p>' if x.get('w') else '')
            + f'<p class="bs">{src}<button type="button" class="lnk" data-share>Share</button></p></li>')

def render():
    h = history._load(history.HIST) or {'snapshots': []}
    ev = history.events(h, 60)
    snaps = h.get('snapshots', [])
    if len(snaps) < 2: return ''
    last = snaps[-1]['date']; first = snaps[0]['date']
    chips = ''.join(f'<label class="pill"><input type="checkbox" name="{k}"> {e(v)}</label>' for k, v in TOPICS)
    items = ''.join(item(x) for x in ev)
    return (f'<section class="brief fc" id="brief" aria-labelledby="brief-h" data-last="{last}" data-first="{first}">'
            f'<div class="brh"><h2 id="brief-h" class="fc-k">What changed</h2><span class="brs" id="brief-since">Last 14 days</span></div>'
            f'<ul class="bl" id="brief-list">{items}</ul>'
            f'<p class="bnone" id="brief-none" hidden></p>'
            f'<div class="bctl"><button type="button" class="lnk" id="brief-more" hidden></button>'
            f'<button type="button" class="lnk" id="brief-topics" aria-expanded="false" aria-controls="brief-pick">Topics</button>'
            f'<button type="button" class="lnk" id="brief-reset" hidden>Reset</button></div>'
            f'<fieldset class="pills" id="brief-pick" hidden><legend class="sr">Show changes about</legend>{chips}</fieldset>'
            f'<p class="fc-foot">Real changes between our dated daily snapshots ({fd(first)}–{fd(last)}), not forecasts. '
            f'Your topics and last visit are saved only in this browser.</p></section>')

JS = r'''<script>(()=>{const B=document.getElementById('brief');
const K='mb.v1',ld=()=>{try{return JSON.parse(localStorage.getItem(K))||{}}catch(e){return{}}},sv=o=>{try{localStorage.setItem(K,JSON.stringify(o))}catch(e){}};
const fd=s=>new Date(s+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric'});
const share=async b=>{const a=b.closest('li,article,.fc');let t;if(a.matches('li')){t=a.querySelector('.bh').textContent.replace(/^[▲▼]\s*/,'')+' (recorded '+a.querySelector('time').textContent+'; source: '+((a.querySelector('.bs a')||{}).textContent||'provider page').replace(' ↗','')+'), via Money Beast'}else{t=[...a.querySelectorAll('.fc-k,.fc-big,.fc-line,.fc-catch')].map(x=>x.textContent.trim()).filter(Boolean).join(' · ')+'. Source: provider pages, via Money Beast'}
const u=location.origin+location.pathname+(b.dataset.share||'');try{if(navigator.share){await navigator.share({title:'Money Beast',text:t,url:u});return}await navigator.clipboard.writeText(t+' '+u);const o=b.textContent;b.textContent='Copied';setTimeout(()=>b.textContent=o,1500)}catch(e){}};
document.addEventListener('click',e=>{const b=e.target.closest('[data-share]');if(b){e.preventDefault();share(b)}});
if(!B)return;const st=ld(),L=[...B.querySelectorAll('#brief-list li')],more=B.querySelector('#brief-more'),none=B.querySelector('#brief-none'),pick=B.querySelector('#brief-pick'),tb=B.querySelector('#brief-topics'),rs=B.querySelector('#brief-reset'),since=B.querySelector('#brief-since');
let prev=sessionStorage.getItem('mb.since');if(prev===null){prev=st.last||'';sessionStorage.setItem('mb.since',prev)}
st.last=B.dataset.last;sv(st);let open=false;
const draw=()=>{const s=ld(),T=s.topics||[];const lim=prev&&prev<B.dataset.last?prev:'';const cut=lim||new Date(Date.parse(B.dataset.last)-14*864e5).toISOString().slice(0,10);
 const ok=L.filter(li=>li.dataset.d>cut&&(!T.length||T.includes(li.dataset.t)));L.forEach(li=>li.hidden=true);ok.forEach((li,i)=>li.hidden=!open&&i>=3);
 since.textContent=(lim?'Since your last visit, '+fd(lim):'Last 14 days')+(T.length?' · your topics':'');
 more.hidden=ok.length<=3;more.textContent=open?'Show fewer':'Show '+(ok.length-3)+' more';
 none.hidden=!!ok.length;none.textContent='No rate changes '+(lim?'since '+fd(lim):'in the last 14 days')+(T.length?' in your topics':'')+'. Latest check '+fd(B.dataset.last)+'.';
 pick.querySelectorAll('input').forEach(c=>c.checked=T.includes(c.name));rs.hidden=!(T.length||s.sv)};
more.onclick=()=>{open=!open;draw()};tb.onclick=()=>{pick.hidden=!pick.hidden;tb.setAttribute('aria-expanded',!pick.hidden)};
pick.addEventListener('change',()=>{const s=ld();s.topics=[...pick.querySelectorAll('input:checked')].map(c=>c.name);sv(s);draw()});
rs.onclick=()=>{localStorage.removeItem(K);sv({last:B.dataset.last});const m=document.getElementById('sv-my');if(m){m.value='';m.dispatchEvent(new Event('input',{bubbles:true}))}draw()};draw()})();</script>'''

def apply(h):
    if 'id="sv-pick"' not in h or 'id="brief"' in h: return h
    sec = render()
    if not sec: return h
    i = h.find('</article>', h.find('id="sv-pick"'))
    if i < 0: return h
    h = h[:i + 10] + sec + h[i + 10:]
    return h.replace('</body>', JS + '</body>', 1)
