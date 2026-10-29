(function(){var el=document.getElementById('sv-data');if(!el)return;var D=JSON.parse(el.textContent),P={};D.providers.forEach(function(v){P[v.id]=v});
var f=document.getElementById('sv-form'),bal=document.getElementById('sv-bal'),err=document.getElementById('sv-bal-err'),list=document.getElementById('sv-list'),pick=document.getElementById('sv-pick'),more=document.getElementById('sv-more'),skip=document.getElementById('sv-skip');
var INS={bank:['FDIC bank deposit','ok'],conditional:['Pass-through FDIC, conditions apply','warn'],mixed:['Partly bank-swept, partly not','warn'],none:['Not FDIC insured','bad']};
var NT={'new':'new customers',dd:'direct deposit',fee:'paid membership',referral:'referral link',activity:'monthly deposits'};
function h(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function m(x){return '$'+Math.round(x).toLocaleString('en-US')}
function fd(s){if(!s)return '';var d=new Date(s+'T12:00:00');return d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}
function card(r,b,i){var v=P[r.id],ins=INS[v.fdic],pm=r.promoMonths,needs=r.needs.map(function(n){return NT[n]}).join(', ');
 var mt=m(r.gross)+' interest'+(r.fee?' − '+m(r.fee)+' fees = <b>'+m(r.net)+'</b>':'');
 var after=pm?' After the promo ends: about '+m(r.ongoing-r.fee)+'/yr at today’s rate.':'';
 var chips=v.flags.map(function(f){return '<span class="chip warn">'+h(f[1])+'</span>'}).join('');
 var src=v.src?' · <a href="'+h(v.src)+'" target="_blank" rel="noopener">Source ↗</a>':'';
 var chk=v.verifiedAt?'Checked '+fd(v.verifiedAt):'Check date not recorded';var pc=(r.net/b*100).toFixed(2)+'%';
 return '<li class="res'+(v.flags.length?' stale':'')+'"><div class="rtop"><span class="rk">'+i+'</span><div><b class="nm">'+h(v.name)+'</b><span class="pd">'+(needs?'Needs '+needs:'No conditions')+'</span>'+chips+'</div><div class="amt"><b>'+pc+'</b><span>'+(pm||r.fee?'yr 1':'APY')+'</span></div></div>'
 +'<details class="i"><summary>Details</summary><p class="how">'+h(v.product)+' · '+h(r.label)+'</p><p class="how">'+mt+' on '+m(b)+' ≈ '+pc+' over 12 months.'+after+'</p>'
 +'<p class="meta"><span class="chip '+ins[1]+'">'+ins[0]+'</span><span>'+chk+src+'</span></p></details></li>'}
function go(){var b=parseFloat(bal.value.replace(/[$,\s]/g,''));var bad=!(b>=1&&b<=1e7);err.hidden=!bad;bal.setAttribute('aria-invalid',bad);if(bad)return;
 var o={};f.querySelectorAll('input[type=checkbox]').forEach(function(c){o[c.name]=c.checked});
 var R=MBCalc.run(D,b,o,D.today),top=R.rows.filter(function(r){return r.rankable})[0];
 var tops=R.rows.filter(function(r){return r.rankable}),top=tops[0];
 function y1(r){return !!(r.promoMonths||r.fee)}function pc(r){return (r.net/b*100).toFixed(2)+'%'}function nds(r){return r.needs.filter(function(n){return n!=='new'}).map(function(n){return NT[n]}).join(', ')}
 function cond(r){var v=P[r.id],nd=nds(r);if(v.catches&&(nd||r.promoMonths))return v.catches.filter(function(c){return !/^no monthly fee/i.test(c)}).join(' · ');if(nd&&v.req)return v.req.replace(/\.$/,'')+(r.promoMonths?' · promo rate for '+Math.round(r.promoMonths)+' of 12 months':'');return (nd?'Needs '+nd:'No conditions')+(r.promoMonths?' · promo rate for '+Math.round(r.promoMonths)+' of 12 months':'')}
 pick.innerHTML=top?(function(){var v=P[top.id],nd=nds(top);
  return '<p class="fc-k">Top savings rate'+(nd?'':' · no strings')+'</p><p class="fc-big">'+pc(top)+'<small>'+(y1(top)?' yr 1':' APY')+'</small></p><p class="fc-line"><b>'+h(v.name)+'</b>'+(y1(top)?' · first-year rate'+(top.fee?' · after '+m(top.fee)+' fees':''):'')+'</p>'
  +'<p class="fc-catch"><span>'+h(cond(top))+' · '+INS[v.fdic][0]+' · variable, '+(v.verifiedAt?'checked '+fd(v.verifiedAt):'check date not recorded')+'</span></p>'})()
 :'<p class="fc-k">Top savings rate</p><p class="fc-big">—</p><p class="fc-line">No account matches these options.</p><p class="fc-catch"><span>Try fewer options in Personalize.</span></p>';
 var t3=document.getElementById('sv-top3'),t3k=document.getElementById('sv-t3k');if(t3){var mx=Math.max.apply(null,tops.slice(0,3).map(function(r){return r.net/b}))||1;
  t3.innerHTML=tops.slice(0,3).map(function(r,i){var n=nds(r);return '<li><span class="rk">'+(i+1)+'</span><span class="nm">'+h(P[r.id].name)+'<small>'+(n?'Needs '+n:'No conditions')+(r.promoMonths?' · promo '+Math.round(r.promoMonths)+' of 12 mo':'')+'</small><i class="t3b" style="--w:'+Math.round(r.net/b/mx*100)+'%" aria-hidden="true"></i></span><b>'+pc(r)+'<small>'+(y1(r)?' yr 1':' APY')+'</small></b></li>'}).join('')}
 var dflt=true;f.querySelectorAll('input[type=checkbox]').forEach(function(c){if(c.checked!==c.defaultChecked)dflt=false});if(t3k)t3k.textContent=dflt?'Top 3 · no strings':'Top 3 for your options';
 var ea=document.getElementById('sv-earn'),me=document.getElementById('sv-my'),mr=document.getElementById('sv-my-err'),mv=me&&me.value.trim()!==''?parseFloat(me.value.replace(/[%\s]/g,'')):NaN,mbad=me&&me.value.trim()!==''&&!(mv>=0&&mv<=30);if(mr){mr.hidden=!mbad;me.setAttribute('aria-invalid',!!mbad)}if(ea)ea.innerHTML=!top?'':(mv>=0&&mv<=30)?(function(){var d=top.net-b*mv/100;return d>0.5?'≈ <b>'+m(d)+' more</b> in year one at '+h(P[top.id].name)+' than at your '+mv+'%, on '+m(b)+', before tax':'Your '+mv+'% already matches or beats '+h(P[top.id].name)+' for year one'})():(function(){var vn=document.getElementById('sv-vs'),nr=vn?parseFloat(vn.dataset.nat):NaN;return '<b>'+m(b)+'</b> earns ≈ <b>'+m(top.net)+'</b> in year one'+(nr>=0?' vs '+m(b*nr/100)+' at the US average':' at '+h(P[top.id].name))+', before tax'})();try{var S=JSON.parse(localStorage.getItem('mb.v1'))||{};if(me&&(me.value.trim()||S.sv)){S.sv={bal:bal.value,my:me.value};if(!me.value.trim())delete S.sv;localStorage.setItem('mb.v1',JSON.stringify(S))}}catch(e){}
 var vs=document.getElementById('sv-vs'),rg=document.getElementById('sv-rng'),ro=document.getElementById('sv-rng-o');if(rg&&document.activeElement!==rg){rg.value=Math.max(1000,Math.min(100000,b))}if(ro)ro.textContent=m(b);if(vs&&top){var na=b*parseFloat(vs.dataset.nat)/100,mx=Math.max(top.net,na)||1;vs.innerHTML='<ul class="fbars">'+[[h(P[top.id].name),top.net,1],['US average',na,0]].map(function(x){return '<li class="'+(x[2]?'hi':'')+'"><span class="l">'+x[0]+'</span><span class="b"><i style="--w:'+Math.max(2,x[1]/mx*100).toFixed(1)+'%"></i></span><b>'+m(x[1])+'</b></li>'}).join('')+'</ul>'}
 list.innerHTML=R.rows.map(function(r,i){return card(r,b,i+1)}).join('');more.textContent='Show all '+R.rows.length;more.hidden=R.rows.length<=5;
 skip.textContent=R.skipped.length?'Not counted: '+R.skipped.map(function(s){return P[s.id].name+' ('+s.why+')'}).join('; ')+'.':''}
try{var S0=(JSON.parse(localStorage.getItem('mb.v1'))||{}).sv;if(S0&&document.getElementById('sv-my')){bal.value=S0.bal;document.getElementById('sv-my').value=S0.my;var ad=document.getElementById('sv-adjust');if(ad&&S0.my)ad.open=true}}catch(e){}
var rg0=document.getElementById('sv-rng');if(rg0)rg0.addEventListener('input',function(){bal.value=(+rg0.value).toLocaleString('en-US')});f.addEventListener('input',go);f.addEventListener('change',go);
more.addEventListener('click',function(){var c=list.classList.toggle('collapsed');more.textContent=c?'Show all '+list.children.length:'Show fewer'});
go()})();
