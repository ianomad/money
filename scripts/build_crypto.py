"""Build docs/crypto.html from data/crypto.json.

  python3 scripts/build_crypto.py           # rebuild the page from the saved snapshot
  python3 scripts/build_crypto.py --fetch   # refetch the CoinGecko public API first

Nothing is estimated here: every price and market cap on the page comes from the saved snapshot.
"""
import hashlib, json, subprocess, sys, time
from datetime import datetime, timezone
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / 'data/crypto.json', ROOT / 'docs/crypto.html'
MARKETS = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false'
GLOBAL = 'https://api.coingecko.com/api/v3/global'
COIN_PAGE = 'https://www.coingecko.com/en/coins/'

def get(url, tries=4):
    for i in range(tries):
        r = subprocess.run(['curl', '-sSL', '--compressed', '--max-time', '60', '-H', 'Accept: application/json', '-w', '\n%{http_code}', url],
                           check=True, capture_output=True, text=True)
        body, code = r.stdout.rsplit('\n', 1)
        if code == '200': return json.loads(body)
        if i < tries - 1: time.sleep(20 * (i + 1))  # CoinGecko's free tier answers 429 when busy
    raise RuntimeError(f'{url} -> HTTP {code}')

def fetch():
    coins = get(MARKETS)
    keep = ('id', 'symbol', 'name', 'image', 'current_price', 'market_cap', 'market_cap_rank', 'price_change_percentage_24h', 'last_updated')
    data = {'fetchedAt': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'), 'source': 'CoinGecko public API',
            'sourceUrl': MARKETS, 'coins': [{k: c.get(k) for k in keep} for c in coins]}
    try:
        g = get(GLOBAL)['data']
        data['global'] = {'sourceUrl': GLOBAL, 'totalMarketCapUsd': g['total_market_cap']['usd'], 'btcDominance': g['market_cap_percentage']['btc'],
                          'activeCryptocurrencies': g['active_cryptocurrencies'], 'updatedAt': g['updated_at']}
    except Exception as err:
        print(f'Global endpoint skipped: {err}')
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')

def usd(n, long=False):
    for div, s, w in ((1e12, 'T', 'trillion'), (1e9, 'B', 'billion'), (1e6, 'M', 'million')):
        if n >= div: return f'${n / div:,.2f} {w}' if long else f'${n / div:,.2f}{s}' if n < 100 * div else f'${n / div:,.0f}{s}'
    return f'${n:,.0f}'

def price(p):
    if p >= 1000: return f'${p:,.0f}'
    if p >= 1: return f'${p:,.2f}'
    if p >= 0.01: return f'${p:.4f}'
    return f'${p:.8f}'.rstrip('0')

def pct(p):
    if p is None: return '<span class="chg">—</span>'
    cls = 'up' if p > 0 else 'down' if p < 0 else ''
    return f'<span class="chg {cls}">{"+" if p > 0 else "−" if p < 0 else ""}{abs(p):.2f}%</span>'

def build():
    data = json.loads(DATA.read_text())
    coins = sorted((c for c in data['coins'] if c.get('market_cap')), key=lambda c: -c['market_cap'])
    top = coins[0]; g = data.get('global')
    when = datetime.fromisoformat(data['fetchedAt'].replace('Z', '+00:00'))
    checked = when.strftime('%b %-d, %Y'); stamp = when.strftime('%b %-d, %Y, %H:%M UTC')
    link = lambda c: COIN_PAGE + e(c['id'])
    icon = lambda c: f'<img class="coin-icon" src="{e(c["image"])}" width="28" height="28" alt="" loading="lazy" decoding="async">' if c.get('image') else ''

    peak = coins[0]['market_cap']
    bars = ''.join(f'<div class="bar-row"><b>{e(c["name"])}</b><span class="bar"><i style="width:{max(2, round(c["market_cap"] / peak * 100))}%"></i></span><strong>{usd(c["market_cap"])}</strong></div>' for c in coins[:10])
    rows = ''.join(f'<li class="coin-row"><span class="coin-rank">{i}</span><a class="coin-name" href="{link(c)}" target="_blank" rel="noopener">{icon(c)}<span><b>{e(c["name"])}</b><small>{e(c["symbol"].upper())}</small></span></a>'
                   f'<span class="coin-price"><span class="mobile-label">Price</span>{price(c["current_price"])}</span><span class="coin-cap"><span class="mobile-label">Market cap</span>{usd(c["market_cap"])}</span><span class="coin-chg"><span class="mobile-label">24h</span>{pct(c.get("price_change_percentage_24h"))}</span></li>'
                   for i, c in enumerate(coins, 1))
    total = (f'<p class="crypto-total">All crypto together: <b>{usd(g["totalMarketCapUsd"], True)}</b>. Bitcoin is <b>{g["btcDominance"]:.1f}%</b> of it.</p>' if g else '')
    hero = (f'<section class="share-card" id="share"><p class="eyebrow">Biggest by market cap</p><p class="share-rate">{usd(top["market_cap"])}</p>'
            f'<p class="share-who">{e(top["name"])} ({e(top["symbol"].upper())})</p><p class="share-catch">Total value of all {e(top["name"])} in circulation, in US dollars.</p>'
            f'<p class="share-date">Checked {checked} · money.ilyusha.xyz</p></section>')
    desc = f'The top {len(coins)} cryptocurrencies by market cap, with prices and 24h moves from CoinGecko. {top["name"]} is the largest at {usd(top["market_cap"], True)}.'
    sources = f'Sources: prices and market caps from the <a href="{e(data["sourceUrl"])}" target="_blank" rel="noopener">CoinGecko public API ↗</a> (<code>{e(data["sourceUrl"])}</code>)'
    if g: sources += f'; total market cap and Bitcoin share from <a href="{e(g["sourceUrl"])}" target="_blank" rel="noopener">CoinGecko global ↗</a> (<code>{e(g["sourceUrl"])}</code>)'
    sources += f'. Fetched {stamp}.'
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Money — crypto</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="https://money.ilyusha.xyz/crypto.html"><meta property="og:title" content="Money — crypto"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://money.ilyusha.xyz/crypto.html"><meta name="twitter:card" content="summary"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="analytics.js" defer></script></head>
<body><a class="skip-link" href="#coins">Skip to the list</a><header><a class="brand" href="index.html"><img class="brand-mark" src="favicon.svg" alt="">money<span class="brand-by">/ by ilyusha</span></a><nav aria-label="Main navigation"><a class="nav-switch" href="index.html">Savings</a><a class="nav-switch" href="cards.html">Cards</a><a class="nav-switch" href="economy.html">Economy</a><a class="nav-switch" href="crypto.html" aria-current="page">Crypto</a><a class="nav-switch" href="insights.html">Insights</a><a class="nav-switch" href="daily.html">Daily</a></nav><a class="personal" href="https://ilyusha.xyz">ilyusha.xyz ↗</a></header>
<main id="top"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> CRYPTO / USD</p><h1>Where the <em>coins sit.</em></h1>{hero}</div><aside class="snapshot"><div class="snapshot-count">{len(coins)}<span>assets<br>listed</span></div><div class="snapshot-date">Checked <time datetime="{e(data['fetchedAt'])}">{checked}</time></div><p>Prices move all the time · This is a snapshot</p></aside></section>
<section id="biggest" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">01 / TOP 10</span><h2>Biggest by market cap<span>.</span></h2></div><p>US dollars, {checked}</p></div><figure class="share-chart econ-chart"><figcaption>Market cap, US$</figcaption>{bars}</figure>{total}</section>
<section id="coins" class="rate-group econ-section"><div class="group-heading"><div><span class="eyebrow">02 / TOP {len(coins)}</span><h2>The full list<span>.</span></h2></div><p>Price, market cap and 24h change</p></div><div class="coin-head" aria-hidden="true"><span>#</span><span>COIN</span><span>PRICE</span><span>MARKET CAP</span><span>24H</span></div><ol class="coin-list">{rows}</ol></section>
<p class="econ-note crypto-plain">This is market size, not a savings rate. Stablecoin yields stay on <a href="index.html#crypto-rates">Savings</a>.</p>
<p class="econ-sources">{sources}</p>
</main><footer><span>Money / An independent tracker by <a href="https://ilyusha.xyz">Ilyusha ↗</a></span><a href="index.html">Back to savings</a></footer></body></html>
'''
    for asset in ('styles.css', 'analytics.js', 'favicon.svg'):
        v = hashlib.sha256((ROOT / 'docs' / asset).read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{asset}"', f'"{asset}?v={v}"')
    OUT.write_text(page)
    print(f'Built crypto page: {len(page) // 1024} KB, {len(coins)} coins, top {top["name"]} {usd(top["market_cap"], True)}, fetched {data["fetchedAt"]}.')

if __name__ == '__main__':
    if '--fetch' in sys.argv: fetch()
    build()
