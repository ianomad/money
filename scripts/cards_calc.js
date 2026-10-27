var MBCards={CATS:['dining','groceries','gas','travel','streaming','other'],
rewards:function(c,p,cpp){var t=0;this.CATS.forEach(function(k){var a=(p[k]||0)*12,r=(c.earn[k]!=null?c.earn[k]:c.earn.other),cap=c.cap&&c.cap[k];t+=cap&&a>cap?cap*r/100+(a-cap)*c.earn.other/100:a*r/100});return t*(c.points?cpp:1)},
bonus:function(c,p,cpp){var b=c.bonusTerms;if(!b||b.spend==null)return 0;var s=0;for(var k in p)s+=p[k];if(s*b.months<b.spend)return 0;return (b.usd||0)+(b.pts||0)*(c.points?cpp:1)/100},
value:function(c,p,cpp,fy){return Math.round(this.rewards(c,p,cpp)-c.fee+(fy?this.bonus(c,p,cpp):0))}};
