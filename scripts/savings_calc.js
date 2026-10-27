/* Money Beast savings calculator. Same math as scripts/savings.py (tests/ cross-check both). */
var MBCalc=(function(){
var NT={'new':'new customers',dd:'direct deposit',fee:'paid membership',referral:'referral link',activity:'monthly deposits'};
function yearly(spec,b){ /* $ per year at this rate spec for balance b, or null if terms unpublished */
  if(typeof spec==='number')return b*spec/100;
  var t=spec.tiers,i,lo=0,sum=0;
  if(spec.split){for(i=0;i<t.length;i++){var up=t[i][0]===null?Infinity:t[i][0];if(b>lo){sum+=(Math.min(b,up)-lo)*t[i][1]/100}lo=up}
    return b>lo?null:sum}
  for(i=0;i<t.length;i++){if(t[i][0]===null||b<=t[i][0])return b*t[i][1]/100}
  return null}
function monthsUntil(today,until){var d=(Date.parse(until)-Date.parse(today))/864e5;return Math.max(0,Math.min(12,d/30.4375))}
function path(p,b,today){var fee=p.feeYr||0,thenY=yearly(p.rate,b);if(thenY===null)return {err:'terms above this balance are not published'};
  var pm=0,promoY=0,pr=p.promo;
  if(pr){if(pr.openBy&&pr.openBy<today)return {err:'offer ended '+pr.openBy};
    if(pr.maxBal&&b>pr.maxBal)return {err:'promo not available above this balance'};
    pm=pr.until?monthsUntil(today,pr.until):Math.min(12,pr.months);promoY=yearly(pr.rate,b);if(promoY===null)return {err:'terms above this balance are not published'}}
  var gross=promoY*pm/12+thenY*(12-pm)/12;
  return {gross:gross,net:gross-fee,fee:fee,promoMonths:pm,ongoing:thenY,label:p.label,needs:p.needs}}
function run(D,b,opt,today){ /* D={providers:[{id,name,terms,status,verifiedAt,fdic,...}]} opt={new,dd,fee,referral,activity,bankOnly,noPromo} */
  var out=[],skipped=[];
  D.providers.forEach(function(v){var T=v.terms;
    if(opt.bankOnly&&v.fdic!=='bank')return;
    if(T.status==='paused'){skipped.push({id:v.id,why:'not taking new applications'});return}
    if(T.minOpen&&b<T.minOpen){skipped.push({id:v.id,why:'needs $'+T.minOpen+' to open'});return}
    var best=null,errs=[];
    T.paths.forEach(function(p){
      if(p.needs.some(function(n){return !opt[n]}))return;
      if(opt.noPromo&&p.promo)return;
      var r=path(p,b,today);if(r.err){errs.push(p.label+': '+r.err);return}
      if(!best||r.net>best.net+1e-9||(Math.abs(r.net-best.net)<1e-9&&r.needs.length<best.needs.length))best=r});
    if(!best){skipped.push({id:v.id,why:errs[0]||'needs '+T.paths.map(function(p){return p.needs.map(function(n){return NT[n]}).join(', ')}).join(' or ')});return}
    best.id=v.id;best.flags=v.flags||[];best.rankable=!best.flags.length;out.push(best)});
  out.sort(function(a,c){return c.net-a.net||(a.needs.length-c.needs.length)});
  return {rows:out,skipped:skipped}}
return {yearly:yearly,path:path,run:run,monthsUntil:monthsUntil}})();
if(typeof module!=='undefined')module.exports=MBCalc;
