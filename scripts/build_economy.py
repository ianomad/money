"""Build docs/economy.html from data/economy.json and data/world-110m.json.

  python3 scripts/build_economy.py           # rebuild the page from the saved data
  python3 scripts/build_economy.py --fetch   # refetch IMF, UNCTAD and Natural Earth first

--fetch needs network access, openpyxl and py7zr. Nothing is estimated here:
every number on the page comes from the saved source files.
"""
import csv, hashlib, io, json, math, subprocess, sys
from datetime import date
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, GEO, OUT = ROOT / 'data/economy.json', ROOT / 'data/world-110m.json', ROOT / 'docs/economy.html'

IMF_API = 'https://www.imf.org/external/datamapper/api/v1/NGDPD'
IMF_PAGE = 'https://www.imf.org/external/datamapper/NGDPD@WEO/OEMDC/ADVEC/WEOWORLD'
# Vintage-specific; update the link for each new WEO from https://data.imf.org/en/datasets/IMF.RES:WEO
WEO_XLSX = 'https://data.imf.org/-/media/iData/External-Storage/Documents/2F78EE59F79143A7921E5E203D3AAA80/en/WEOApr2026all.xlsx'
UNCTAD_BULK = 'https://unctadstat-api.unctad.org/bulkdownload/US.FdiFlowsStock/US_FdiFlowsStock'
UNCTAD_PAGE = 'https://unctadstat.unctad.org/datacentre/dataviewer/US.FdiFlowsStock'
NE_GEOJSON = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson'
NE_PAGE = 'https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
           'Accept': 'application/json,text/html;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9', 'Referer': IMF_PAGE}

def get(url):
    # curl rather than urllib: the IMF's CDN rejects urllib's TLS fingerprint.
    args = ['curl', '-sSfL', '--compressed', '--max-time', '180']
    for k, v in HEADERS.items(): args += ['-H', f'{k}: {v}']
    return subprocess.run(args + [url], check=True, capture_output=True).stdout

# ---------- fetch ----------
def fetch_gdp():
    values = json.loads(get(IMF_API))['values']['NGDPD']
    labels = {k: v['label'] for k, v in json.loads(get('https://www.imf.org/external/datamapper/api/v1/countries'))['countries'].items()}
    meta = json.loads(get('https://www.imf.org/external/datamapper/api/v1/indicators'))['indicators']['NGDPD']
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(get(WEO_XLSX)), read_only=True)['Countries']
    rows = ws.iter_rows(values_only=True); head = list(next(rows))
    latest = {r[2]: r[head.index('LATEST_ACTUAL_ANNUAL_DATA')] for r in rows if r[4] == 'NGDPD'}
    countries = {k: v for k, v in values.items() if k in labels}
    # Latest year that is not a WEO projection: WEO projections start in the publication year.
    year = str(int(meta['last-modified'][:4]) - 1)
    out = {}
    for iso, series in countries.items():
        if series.get(year) is None: continue
        la = latest.get(iso)
        out[iso] = {'name': labels[iso], 'value': series[year], 'latestActual': str(la) if la is not None else None,
                    'estimate': not (isinstance(la, int) and la >= int(year))}
    return {'indicator': 'NGDPD', 'label': meta['label'], 'unit': meta['unit'], 'release': meta['source'],
            'lastModified': meta['last-modified'], 'year': int(year), 'api': IMF_API, 'page': IMF_PAGE,
            'estimateFlags': WEO_XLSX, 'estimateNote': 'estimate = the WEO LATEST_ACTUAL_ANNUAL_DATA for the economy is earlier than the year shown, or is a fiscal year',
            'values': dict(sorted(out.items()))}

def fetch_fdi():
    import py7zr
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        with py7zr.SevenZipFile(io.BytesIO(get(UNCTAD_BULK))) as z:
            name = z.getnames()[0]; z.extractall(tmp)
        text = (Path(tmp) / name).read_text(encoding='utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(text)))
    V = 'Millions of US$ at current prices'
    flows = [r for r in rows if r['Flow Label'] == 'Flow' and len(r['Economy']) == 3 and r[V]]  # 3-digit codes = single economies; 4-digit = groups
    years = sorted({r['Year'] for r in flows}, key=int)
    year = next(y for y in reversed(years) if sum(r['Year'] == y and r['Direction Label'] == 'Inward' for r in flows) >= 150)
    def side(d):
        return {r['Economy']: {'name': r['Economy Label'], 'value': float(r[V]), **({'note': r[V + ' Footnote']} if r[V + ' Footnote'] else {})}
                for r in flows if r['Year'] == year and r['Direction Label'] == d}
    world = {r['Direction Label']: float(r[V]) for r in rows if r['Year'] == year and r['Economy'] == '0000' and r['Flow Label'] == 'Flow'}
    return {'source': 'UNCTADstat, Foreign direct investment: Inward and outward flows and stock (US.FdiFlowsStock), as published with the World Investment Report 2026',
            'unit': 'Millions of US dollars at current prices', 'year': int(year), 'page': UNCTAD_PAGE, 'bulk': UNCTAD_BULK,
            'world': world, 'inflows': side('Inward'), 'outflows': side('Outward')}

def natural_earth(lon, lat):
    l, p = math.radians(lon), math.radians(lat); p2 = p * p; p4 = p2 * p2
    x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y

def simplify(pts, tol):
    if len(pts) < 4: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop(); (ax, ay), (bx, by) = pts[a], pts[b]; dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy) or 1e-9
        best, idx = 0, None
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / n
            if d > best: best, idx = d, i
        if idx is not None and best > tol: keep[idx] = True; stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]

def fetch_geo(width=1000, tol=0.45):
    gj = json.loads(get(NE_GEOJSON))
    fix = {'PSX': 'WBG', 'KOS': 'UVK', 'SAH': 'ESH'}  # Natural Earth ADM0_A3 -> IMF code
    sx = width / (2 * natural_earth(180, 0)[0]); top, bottom = natural_earth(0, 84)[1], natural_earth(0, -57)[1]
    height = round((top - bottom) * sx)
    out = []
    for f in gj['features']:
        pr = f['properties']
        if pr['ADM0_A3'] == 'ATA': continue
        iso = pr['ISO_A3'] if pr['ISO_A3'] != '-99' else pr['ADM0_A3']; iso = fix.get(pr['ADM0_A3'], iso)
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        parts = []
        for poly in polys:
            for ring in poly:
                pts = [natural_earth(lo, la) for lo, la in ring]
                pts = [(round(x * sx + width / 2, 1), round((top - y) * sx, 1)) for x, y in pts]
                far = max(range(len(pts)), key=lambda i: math.dist(pts[0], pts[i]))  # split the closed ring so both halves have a real chord
                pts = simplify(pts[:far + 1], tol)[:-1] + simplify(pts[far:], tol)
                area = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2
                if len(pts) < 4 or area < 0.6: continue
                d = 'M' + 'L'.join(f'{x:g} {y:g}' for x, y in pts[:-1]) + 'Z'
                parts.append(d)
        if parts: out.append({'iso': iso, 'name': pr['NAME_LONG'], 'd': ''.join(parts)})
    return {'source': NE_GEOJSON, 'page': NE_PAGE, 'license': 'Natural Earth, public domain',
            'projection': 'Natural Earth I', 'viewBox': f'0 0 {width} {height}', 'countries': out}

def fetch():
    data = {'fetchedAt': date.today().isoformat(), 'gdp': fetch_gdp(), 'fdi': fetch_fdi()}
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
    GEO.write_text(json.dumps(fetch_geo(), separators=(',', ':'), ensure_ascii=False) + '\n')

# ---------- build ----------
SHORT = {'United States of America': 'United States', "China, People's Republic of": 'China', 'Russian Federation': 'Russia',
         'Korea, Republic of': 'South Korea', 'Republic of Korea': 'South Korea', 'Türkiye, Republic of': 'Türkiye',
         'China, Hong Kong SAR': 'Hong Kong (China)', 'Netherlands (Kingdom of the)': 'Netherlands', 'Netherlands, The': 'Netherlands',
         'Taiwan Province of China': 'Taiwan', 'China, Taiwan Province of': 'Taiwan', 'Poland, Republic of': 'Poland',
         'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom', 'Iran (Islamic Republic of)': 'Iran'}
def short(n): return SHORT.get(n, n)

def usd_b(b, long=False):
    if b >= 1000: return f'${b / 1000:.2f} trillion' if long else f'${b / 1000:.1f}T'
    if long: return f'${b:,.1f} billion' if b >= 10 else f'${b:.2f} billion'
    return f'${b:,.0f}B' if b >= 100 else f'${b:.1f}B'

BINS = [(2000, '$2T and up'), (500, '$500B–2T'), (100, '$100B–500B'), (25, '$25B–100B'), (0, 'Under $25B')]
def shade(b):
    for i, (lo, _) in enumerate(BINS):
        if b >= lo: return 4 - i

def build():
    data, geo = json.loads(DATA.read_text()), json.loads(GEO.read_text())
    gdp, fdi = data['gdp'], data['fdi']; Y = gdp['year']; vals = gdp['values']
    est = lambda r: ' (IMF estimate)' if r['estimate'] else ''
    names = {c['iso']: c['name'] for c in geo['countries']}
    ranked = sorted(vals.items(), key=lambda kv: -kv[1]['value'])
    top_iso, top = ranked[0]
    name_of = lambda iso: short(names.get(iso) or vals[iso]['name'])

    paths = []
    for c in geo['countries']:
        r = vals.get(c['iso'])
        if r: cls, tip = f'g{shade(r["value"])}', f'{short(c["name"])}: {usd_b(r["value"], True)}, {Y}{est(r)}'
        else: cls, tip = 'gn', f'{short(c["name"])}: no IMF data for {Y}'
        paths.append(f'<path class="{cls}" d="{c["d"]}"><title>{e(tip)}</title></path>')
    legend = ''.join(f'<li><i class="g{4 - i}"></i>{e(label)}</li>' for i, (_, label) in reversed(list(enumerate(BINS)))) + '<li><i class="gn"></i>No data</li>'
    on_map = sum(1 for c in geo['countries'] if c['iso'] in vals)

    peak = ranked[0][1]['value']; bars = []
    for iso, r in ranked[:10]:
        star = '*' if r['estimate'] else ''
        bars.append(f'<div class="bar-row"><b>{e(name_of(iso))}</b><span class="bar"><i style="width:{max(2, round(r["value"] / peak * 100))}%"></i></span><strong>{usd_b(r["value"])}{star}</strong></div>')
    any_est = any(r['estimate'] for _, r in ranked[:10])

    def flow_list(side):
        rows = sorted(fdi[side].values(), key=lambda r: -r['value'])[:10]
        return ''.join(f'<li><span>{e(short(r["name"]))}</span><strong>${r["value"] / 1000:,.1f}B</strong></li>' for r in rows)

    fetched = date.fromisoformat(data['fetchedAt']).strftime('%b %-d, %Y')
    hero = (f'<section class="share-card" id="share"><p class="eyebrow">Largest economy</p><p class="share-rate">{usd_b(top["value"])}</p>'
            f'<p class="share-who">{e(name_of(top_iso))}</p><p class="share-catch">Nominal GDP in {Y}{" (IMF estimate)" if top["estimate"] else ""}, current US dollars.</p>'
            f'<p class="share-date">IMF World Economic Outlook · money.ilyusha.xyz</p></section>')
    desc = f'World GDP by country from the IMF World Economic Outlook, and FDI flows from UNCTAD. {name_of(top_iso)} is the largest economy at {usd_b(top["value"], True)} in {Y}.'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Money — economy</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="https://money.ilyusha.xyz/economy.html"><meta property="og:title" content="Money — economy"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz/economy.html"><meta name="twitter:card" content="summary"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="analytics.js" defer></script></head>
<body><a class="skip-link" href="#map">Skip to the map</a><header><a class="brand" href="index.html"><img class="brand-mark" src="favicon.svg" alt="">money<span class="brand-by">/ by ilyusha</span></a><nav aria-label="Main navigation"><a class="nav-switch" href="index.html">Savings</a><a class="nav-switch" href="cards.html">Cards</a><a class="nav-switch" href="economy.html" aria-current="page">Economy</a><a class="nav-switch" href="crypto.html">Crypto</a><a class="nav-switch" href="insights.html">Insights</a><a class="nav-switch" href="daily.html">Daily</a></nav><a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main id="top"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> ECONOMY / USD</p><h1>Where the <em>money is.</em></h1>{hero}</div><aside class="snapshot"><div class="snapshot-count">{on_map}<span>economies<br>on the map</span></div><div class="snapshot-date">Fetched <time datetime="{data['fetchedAt']}">{fetched}</time></div><p>GDP for {Y} · FDI for {fdi['year']}</p></aside></section>
<section id="map" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">01 / GDP</span><h2>The world by GDP<span>.</span></h2></div><p>{Y}, current US dollars</p></div><figure class="world-map"><svg viewBox="{geo['viewBox']}" role="img" aria-label="World map shaded by nominal GDP in {Y}"><title>World map shaded by nominal GDP, {Y}</title>{''.join(paths)}</svg><figcaption><ul class="map-legend">{legend}</ul></figcaption></figure></section>
<section id="biggest" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">02 / TOP 10</span><h2>Biggest economies<span>.</span></h2></div><p>Nominal GDP, {Y}</p></div><figure class="share-chart econ-chart"><figcaption>GDP, {Y}, current US${" · * IMF estimate" if any_est else ""}</figcaption>{''.join(bars)}</figure></section>
<section id="flows" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">03 / FDI</span><h2>Investment flows<span>.</span></h2></div><p>{fdi['year']}, billions of US dollars</p></div><p class="econ-note">Foreign direct investment is money companies put into businesses in another country, like building a factory or buying a stake. The official numbers come out a year or more after the fact.</p><div class="flow-lists"><div><h3>Money coming in</h3><ol class="flow-list">{flow_list('inflows')}</ol></div><div><h3>Money going out</h3><ol class="flow-list">{flow_list('outflows')}</ol></div></div></section>
<p class="econ-sources">Sources: GDP from the <a href="{e(gdp['page'])}" target="_blank" rel="noopener">IMF World Economic Outlook DataMapper ↗</a> (<a href="{e(gdp['api'])}" target="_blank" rel="noopener">API ↗</a>, {e(gdp['release'])}; estimate flags from the <a href="{e(gdp['estimateFlags'])}" target="_blank" rel="noopener">WEO dataset ↗</a>). FDI from <a href="{e(fdi['page'])}" target="_blank" rel="noopener">UNCTADstat ↗</a> (<a href="{e(fdi['bulk'])}" target="_blank" rel="noopener">data file ↗</a>, World Investment Report 2026). Map from <a href="{e(geo['page'])}" target="_blank" rel="noopener">Natural Earth ↗</a>. Fetched {fetched}.</p>
</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="index.html">Back to savings</a></footer></body></html>
'''
    for asset in ('styles.css', 'analytics.js', 'favicon.svg'):
        v = hashlib.sha256((ROOT / 'docs' / asset).read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{asset}"', f'"{asset}?v={v}"')
    OUT.write_text(page)
    print(f'Built economy page: {len(page) // 1024} KB, {on_map} economies on the map, GDP {Y}, FDI {fdi["year"]}.')

if __name__ == '__main__':
    if '--fetch' in sys.argv: fetch()
    build()
