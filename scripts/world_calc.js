/* Money Beast foreign-deposit USD calculator. Same math as scripts/world.py (tests cross-check). */
var MBWorld=(function(){
/* a=USD amount, r=local annual rate %, t=term months, fx=% change in the local currency vs USD over the term (−10 = falls 10%), c=conversion cost % each way, us=US savings APY % */
function calc(a,r,t,fx,c,us){var conv=Math.pow(1-c/100,2),g=1+r/100*t/12,u=1+us/100*t/12;
  var end=function(m){return a*conv*g*(1+m/100)};
  return {termReturn:(g-1)*100,end:end(fx),gain:end(fx)-a,usEnd:a*u,beZero:(1/(conv*g)-1)*100,beUS:(u/(conv*g)-1)*100,end:end(fx),scen:function(m){return end(m)}}}
function yearlyMove(start,now,years){return (Math.pow(start/now,1/years)-1)*100} /* start/now in local units per USD: + means the currency gained */
function est12(r,move){return ((1+r/100)*(1+move/100)-1)*100}
return {calc:calc,yearlyMove:yearlyMove,est12:est12}})();
if(typeof module!=='undefined')module.exports=MBWorld;
