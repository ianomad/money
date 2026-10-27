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
 var chk=v.verifiedAt?'Checked '+fd(v.verifiedAt):'Check date not recorded';
 return '<li class="res'+(v.flags.length?' stale':'')+'"><div class="rtop"><span class="rk">'+i+'</span><div><b class="nm">'+h(v.name)+'</b><span class="pd">'+h(v.product)+'</span></div><div class="amt"><b>'+m(r.net)+'</b><span>first year</span></div></div>'
 +'<p class="how">'+h(r.label)+(needs?' · needs '+needs:'')+'</p><p class="how">'+mt+' on '+m(b)+' ≈ '+(r.net/b*100).toFixed(2)+'% over 12 months.'+after+'</p>'
 +'<p class="meta"><span class="chip '+ins[1]+'">'+ins[0]+'</span>'+chips+'<span>'+chk+src+'</span></p></li>'}
function go(){var b=parseFloat(bal.value.replace(/[$,\s]/g,''));var bad=!(b>=1&&b<=1e7);err.hidden=!bad;bal.setAttribute('aria-invalid',bad);if(bad)return;
 var o={};f.querySelectorAll('input[type=checkbox]').forEach(function(c){o[c.name]=c.checked});
 var R=MBCalc.run(D,b,o,D.today),top=R.rows.filter(function(r){return r.rankable})[0];
 pick.innerHTML=top?'For '+m(b)+' with these choices, <b>'+h(P[top.id].name)+'</b> pays the most over a year: about <b>'+m(top.net)+'</b>.':'No account matches these choices. Try unchecking a filter.';
 list.innerHTML=R.rows.map(function(r,i){return card(r,b,i+1)}).join('');more.textContent='Show all '+R.rows.length;more.hidden=R.rows.length<=5;
 skip.textContent=R.skipped.length?'Not counted: '+R.skipped.map(function(s){return P[s.id].name+' ('+s.why+')'}).join('; ')+'.':''}
f.addEventListener('input',go);f.addEventListener('change',go);
more.addEventListener('click',function(){var c=list.classList.toggle('collapsed');more.textContent=c?'Show all '+list.children.length:'Show fewer'});
go()})();
