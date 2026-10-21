"""Latest Treasury bill yields (coupon equivalent) from home.treasury.gov daily bill rates CSV -> data/tbills.json"""
import csv, io, json, pathlib, urllib.request
from datetime import date, datetime
root = pathlib.Path(__file__).resolve().parent.parent
y = date.today().year
url = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
       f'?type=daily_treasury_bill_rates&field_tdr_date_value={y}&page&_format=csv')
t = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'curl/8'}), timeout=60).read().decode()
row = next(csv.DictReader(io.StringIO(t)))
terms = {}
for k, v in row.items():
    if k.endswith('COUPON EQUIVALENT') and v:
        terms[k.replace(' COUPON EQUIVALENT', '').title()] = float(v)
d = datetime.strptime(row['Date'], '%m/%d/%Y').date().isoformat()
out = {'date': d, 'checkedAt': date.today().isoformat(), 'measure': 'coupon equivalent (bond-equivalent yield), %',
       'source': 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates',
       'terms': terms}
(root / 'data' / 'tbills.json').write_text(json.dumps(out, indent=1))
print(out)
