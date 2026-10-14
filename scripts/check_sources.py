"""Source universe: fetch each institution's official savings/card page, record status + what the page says.
Writes data/sources.json. Block/Cash App/Square/Afterpay are excluded by policy."""
import json, re, html, urllib.request, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
U = [  # (name, group, kind, product, url)
 ("JPMorgan Chase","Big bank","savings","Chase Savings","https://www.chase.com/personal/savings"),
 ("Bank of America","Big bank","savings","Advantage Savings","https://www.bankofamerica.com/deposits/savings/savings-accounts/"),
 ("Citi","Big bank","savings","Citi Accelerate Savings","https://www.citi.com/banking/savings-account"),
 ("Wells Fargo","Big bank","savings","Way2Save Savings","https://www.wellsfargo.com/savings-cds/way2save/"),
 ("U.S. Bank","Big bank","savings","Standard Savings","https://www.usbank.com/bank-accounts/savings-accounts/standard-savings-account.html"),
 ("PNC","Big bank","savings","High Yield Savings","https://www.pnc.com/en/personal-banking/banking/savings/high-yield-savings.html"),
 ("Capital One","Big bank","savings","360 Performance Savings","https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/"),
 ("Goldman Sachs (Marcus)","Big bank","savings","Marcus High-Yield Savings","https://www.marcus.com/us/en/savings/high-yield-savings"),
 ("Truist","Big bank","savings","Truist One Savings","https://www.truist.com/savings/truist-one-savings"),
 ("American Express","Big bank","savings","Amex High Yield Savings","https://www.americanexpress.com/en-us/banking/online-savings/account/"),
 ("Discover","Big bank","savings","Online Savings","https://www.discover.com/online-banking/savings-account/"),
 ("Ally","Big bank","savings","Online Savings","https://www.ally.com/bank/online-savings-account/"),
 ("Synchrony","Big bank","savings","High Yield Savings","https://www.synchrony.com/banking/high-yield-savings"),
 ("Citizens","Big bank","savings","Citizens Access Savings","https://www.citizensaccess.com/savings/high-yield-savings-account"),
 ("Fifth Third","Big bank","savings","Momentum Savings","https://www.53.com/content/fifth-third/en/personal-banking/bank/savings-cds/momentum-savings.html"),
 ("SoFi","Fintech","savings","Checking & Savings","https://www.sofi.com/banking/"),
 ("Chime","Fintech","savings","Chime Savings","https://www.chime.com/savings-account/"),
 ("Robinhood","Fintech","savings","Gold cash sweep","https://robinhood.com/us/en/gold/"),
 ("Wealthfront","Fintech","savings","Cash Account","https://www.wealthfront.com/cash"),
 ("Betterment","Fintech","savings","Cash Reserve","https://www.betterment.com/cash-reserve"),
 ("Apple","Fintech","savings","Apple Card Savings","https://www.apple.com/apple-card/savings/"),
 ("PayPal","Fintech","savings","PayPal Savings","https://www.paypal.com/us/digital-wallet/manage-money/savings-account"),
 ("Revolut","Fintech","savings","Revolut US savings","https://www.revolut.com/en-US/savings/"),
 ("Varo","Fintech","savings","Varo Savings","https://www.varomoney.com/bank/savings-account/"),
 ("Current","Fintech","savings","Savings Pods","https://current.com/savings/"),
 ("X Money","Fintech","savings","X Money balance","https://money.x.com/"),
 ("Mercury","Fintech","savings","Mercury Treasury","https://mercury.com/treasury"),
 ("Bilt","Startup","card","Bilt Cards","https://www.bilt.com/card"),
 ("Imprint","Startup","card","Imprint co-brand cards","https://www.imprint.co/"),
 ("Jiko","Startup","savings","Jiko T-bill account","https://www.jiko.io/"),
 ("Atomic","Startup","savings","Atomic Treasury","https://atomic.financial/"),
]
APY = re.compile(r'(\d{1,2}\.\d{1,2})\s?%\s?(?:APY|Annual Percentage Yield)', re.I)
def get(u):
    r = urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept-Language':'en-US'})
    with urllib.request.urlopen(r, timeout=25) as f: return f.status, f.read().decode('utf-8','ignore')
out = []; today = datetime.date.today().isoformat()
for n,g,k,p,u in U:
    row = dict(name=n, group=g, kind=k, product=p, url=u, checked=today)
    try:
        st, t = get(u); t = re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?s)<(script|style).*?</\1>','',t))))
        apys = sorted({float(x) for x in APY.findall(t) if 0 < float(x) < 20}, reverse=True)
        row.update(status='read' if len(t) > 1500 else 'thin page (needs a browser)', apy=apys[0] if apys else None, apys=apys[:4])
    except Exception as e:
        row.update(status=f'blocked ({getattr(e,"code",type(e).__name__)})', apy=None)
    out.append(row); print(n, row['status'], row.get('apys'))
(ROOT/'data'/'sources.json').write_text(json.dumps({'checkedAt': today, 'excluded': 'Block, Cash App, Square, Afterpay (policy)', 'sources': out}, indent=1))
