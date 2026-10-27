"""Refresh data/fx.json: local currency per 1 USD, official central-bank rates where reachable.
Per currency: rate, date, source, url, official. If a source fails, the last good value is kept (with its old date),
then open.er-api.com is used only for currencies with no official value at all. Never raises: a stale rate beats no build."""
import json, re, subprocess, sys
from datetime import date, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; FX = ROOT / 'data/fx.json'; ER = 'https://open.er-api.com/v6/latest/USD'
def get(url, data=None, hdr=None):
    cmd = ['curl', '-sSfL', '--max-time', '25', '-A', 'Mozilla/5.0 (MoneyBeast rates bot)']
    for h in (hdr or []): cmd += ['-H', h]
    if data: cmd += ['-X', 'POST', '--data', data]
    return subprocess.run(cmd + [url], check=True, capture_output=True, timeout=40).stdout.decode('utf-8', 'ignore')
def mdy(d): return d.strftime('%m-%d-%Y')
def brl(t):
    u = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='{mdy(t - timedelta(days=10))}'&@dataFinalCotacao='{mdy(t)}'&$format=json"
    v = json.loads(get(u))['value'][-1]; return v['cotacaoVenda'], v['dataHoraCotacao'][:10], 'Banco Central do Brasil PTAX (sell)', 'https://www.bcb.gov.br/estabilidadefinanceira/historicocotacoes'
def ngn(t):
    rows = [x for x in json.loads(get('https://www.cbn.gov.ng/api/GetAllExchangeRates')) if x['currency'].strip() == 'US DOLLAR']
    x = max(rows, key=lambda x: x['ratedate']); return float(x['centralrate']), x['ratedate'][:10], 'Central Bank of Nigeria central rate', 'https://www.cbn.gov.ng/rates/ExchRateByCurrency.html'
def kgs(t):
    x = get('https://www.nbkr.kg/XML/daily.xml'); d = re.search(r'Date="(\d\d)\.(\d\d)\.(\d{4})"', x)
    v = re.search(r'ISOCode="USD">\s*<Nominal>1</Nominal>\s*<Value>([\d,]+)', x).group(1)
    return float(v.replace(',', '.')), f'{d[3]}-{d[2]}-{d[1]}', 'National Bank of the Kyrgyz Republic official', 'https://www.nbkr.kg/index1.jsp?item=1562&lang=ENG'
def kzt(t):
    x = get(f'https://nationalbank.kz/rss/get_rates.cfm?fdate={t:%d.%m.%Y}')
    v = re.search(r'<title>USD</title>\s*<description>([\d.]+)', x).group(1); d = re.search(r'<date>(\d\d)\.(\d\d)\.(\d{4})', x)
    return float(v), (f'{d[3]}-{d[2]}-{d[1]}' if d else t.isoformat()), 'National Bank of Kazakhstan official', 'https://nationalbank.kz/en/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut'
def try_(t):
    x = get('https://www.tcmb.gov.tr/kurlar/today.xml'); d = re.search(r'Date="(\d\d)/(\d\d)/(\d{4})"', x)
    v = re.search(r'Kod="USD".*?<ForexSelling>([\d.]+)', x, re.S).group(1)
    return float(v), f'{d[3]}-{d[1]}-{d[2]}', 'Central Bank of Türkiye indicative (forex selling)', 'https://www.tcmb.gov.tr/kurlar/today.xml'
def ars(t):
    r = json.loads(get(f'https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD?fechadesde={t - timedelta(days=10)}&fechahasta={t}'))['results']
    x = max(r, key=lambda x: x['fecha']); return x['detalle'][0]['tipoCotizacion'], x['fecha'], 'BCRA official (Com. A 3500)', 'https://www.bcra.gob.ar/PublicacionesEstadisticas/Tipos_de_cambios.asp'
def gel(t):
    x = json.loads(get('https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/?currencies=USD'))[0]['currencies'][0]
    return x['rate'], x['validFromDate'][:10], 'National Bank of Georgia official', 'https://nbg.gov.ge/en/monetary-policy/currency'
def amd(t):
    x = get('https://api.cba.am/exchangerates.asmx', '<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><ExchangeRatesLatest xmlns="http://www.cba.am/" /></soap12:Body></soap12:Envelope>', ['Content-Type: application/soap+xml; charset=utf-8'])
    v = re.search(r'<ISO>USD</ISO><Amount>1</Amount><Rate>([\d.]+)', x).group(1); d = re.search(r'<CurrentDate>(\d{4}-\d\d-\d\d)', x)
    return float(v), (d[1] if d else t.isoformat()), 'Central Bank of Armenia official', 'https://www.cba.am/en/SitePages/ExchangeArchive.aspx'
def uzs(t):
    x = json.loads(get('https://cbu.uz/en/arkhiv-kursov-valyut/json/USD/'))[0]
    dd, mm, yy = x['Date'].split('.'); return float(x['Rate']), f'{yy}-{mm}-{dd}', 'Central Bank of Uzbekistan official', 'https://cbu.uz/en/arkhiv-kursov-valyut/'
OFFICIAL = {'BRL': brl, 'NGN': ngn, 'KGS': kgs, 'KZT': kzt, 'TRY': try_, 'ARS': ars, 'GEL': gel, 'AMD': amd, 'UZS': uzs}
def main(today=None):
    t = date.fromisoformat(today) if today else date.today()
    codes = [c['currency'] for c in json.loads((ROOT / 'data/yields.json').read_text())['countries']]
    try: old = json.loads(FX.read_text())
    except Exception: old = {}
    od = old.get('detail', {}); out = {}; log = []
    for c in codes:
        if c == 'USD': out[c] = {'rate': 1, 'date': t.isoformat(), 'source': 'USD', 'url': '', 'official': True}; continue
        try:
            r, d, s, u = OFFICIAL[c](t)
            if not r or r <= 0: raise ValueError('bad rate')
            out[c] = {'rate': float(r), 'date': d, 'source': s, 'url': u, 'official': True}
        except Exception as ex:
            log.append(f'{c}: official fetch failed ({type(ex).__name__})')
            if od.get(c, {}).get('official'): out[c] = dict(od[c], stale=True)
    miss = [c for c in codes if c not in out]
    if miss:
        try:
            raw = json.loads(get(ER))
            for c in miss:
                if c in raw['rates']: out[c] = {'rate': raw['rates'][c], 'date': t.isoformat(), 'source': 'open.er-api.com (market aggregate; official source unreachable)', 'url': ER, 'official': False}
        except Exception as ex: log.append(f'er-api failed ({type(ex).__name__})')
        for c in codes:
            if c not in out and c in od: out[c] = dict(od[c], stale=True)
            elif c not in out and c in old.get('rates', {}): out[c] = {'rate': old['rates'][c], 'date': old.get('fetched', ''), 'source': old.get('source', ''), 'url': old.get('source', ''), 'official': False, 'stale': True}
    if not out: print('fx: nothing fetched; keeping old file'); return 1
    FX.write_text(json.dumps({'fetched': t.isoformat(), 'note': 'Local currency per 1 USD. Official central-bank rate where reachable; see detail.',
                              'rates': {c: out[c]['rate'] for c in codes if c in out}, 'detail': out}, indent=1, ensure_ascii=False) + '\n')
    for l in log: print('WARN fx:', l)
    print('fx:', ', '.join(f"{c} {v['rate']:g} ({'official' if v['official'] else 'aggregate'}{', stale' if v.get('stale') else ''}, {v['date']})" for c, v in out.items()))
    return 0
if __name__ == '__main__': sys.exit(main(*(sys.argv[1:2])))
