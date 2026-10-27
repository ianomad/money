(function(){var el=document.getElementById('wc-data');if(!el)return;var D=JSON.parse(el.textContent),C={};D.rows.forEach(function(r){C[r.code]=r});
var body=document.getElementById('wc-body'),why=document.getElementById('wc-why');
document.querySelectorAll('#world-compare [data-wsort]').forEach(function(b){b.addEventListener('click',function(){var k=b.dataset.wsort;
  document.querySelectorAll('#world-compare [data-wsort]').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});
  [].slice.call(body.children).sort(function(a,c){return parseFloat(c.dataset[k])-parseFloat(a.dataset[k])}).forEach(function(tr){body.appendChild(tr)});
  why.textContent=k==='est'?'Sorted by a dollar what-if: the headline rate for 12 months, with the currency moving as much per year as it did since Oct 12, 2023. Not a forecast.':'Sorted by the bank’s advertised rate in local money. Switch to see a dollar estimate that includes the currency.'})});
var $=function(i){return document.getElementById(i)},out=$('wc-out'),err=$('wc-err');
function n(i){return parseFloat(String($(i).value).replace(/[$,%\s]/g,'').replace('−','-'))}
function m(x){return (x<0?'−$':'$')+Math.abs(Math.round(x)).toLocaleString('en-US')}
function sg(x){return (x>0?'+':x<0?'−':'')+Math.abs(x).toLocaleString('en-US',{maximumFractionDigits:2})}
function h(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function be(c,cur){var z=c.beZero,u=c.beUS;return (z<0?'you lose dollars if the '+h(cur)+' falls more than <b>'+(-z).toFixed(1)+'%</b> over the term':'you lose dollars unless the '+h(cur)+' rises at least <b>'+z.toFixed(1)+'%</b>')+', and '+(u<0?'you do worse than US savings if it falls more than <b>'+(-u).toFixed(1)+'%</b>':'you do worse than US savings unless it rises at least <b>'+u.toFixed(1)+'%</b>')+'.'}
function go(){var a=n('wc-a'),r=n('wc-r'),t=n('wc-t'),fx=n('wc-fx'),c=n('wc-cost'),row=C[$('wc-c').value];
 var bad=!(a>0&&r>=0&&r<=100&&t>=1&&t<=60&&fx>-100&&c>=0&&c<50);err.hidden=!bad;if(bad)return;
 var k=MBWorld.calc(a,r,t,fx,c,D.us),s=function(x){return k.scen(x)},box=function(l,v){return '<div><b>'+l+'</b><strong>'+m(v)+'</strong><span>'+m(v-a)+' vs your '+m(a)+'</span></div>'};
 var past=row.move!=null?row.move*t/12:null;
 out.innerHTML='<p class="pick-line">At '+r+'% a year for '+t+' month'+(t==1?'':'s')+', the deposit earns <b>'+k.termReturn.toFixed(1)+'%</b> in '+h(row.cur)+' over the whole term (the annual rate is not what you get unless the term is 12 months).</p><div class="scen">'
  +box('Currency rises 10%',s(10))+box('Currency moves '+sg(fx)+'%',s(fx))+box('Currency falls 10%',s(-10))
  +(past!=null?box('Repeats its pace since Oct 2023 ('+sg(Math.round(past*10)/10)+'%)',s(past)):'')
  +'<div><b>US savings instead</b><strong>'+m(k.usEnd)+'</strong><span>'+D.us+'% APY, same term</span></div></div><p class="how"><b>Break-even:</b> '+be(k,row.cur)+'</p>'}
$('wc-c').addEventListener('change',function(){var r=C[this.value];$('wc-r').value=r.rate;$('wc-t').value=r.months;go()});
$('wc-form').addEventListener('input',go);go()})();
