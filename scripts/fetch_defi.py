"""Fetch live stablecoin yields from DefiLlama -> data/defi.json. Also syncs the Aave row in data/rates.json."""
import json, urllib.request, datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
OK = {'aave-v3':'Aave v3','sky-lending':'Sky','spark-savings':'Spark','compound-v3':'Compound v3','morpho-blue':'Morpho','morpho-v1':'Morpho','maple':'Maple','ethena-usde':'Ethena'}
COINS = {'USDC','USDT','DAI','USDS','SUSDS','USDE','SUSDE','GHO','SGHO','PYUSD','USDG','FRAX','RLUSD','USDT0','SYRUPUSDC','SYRUPUSDT'}
req = urllib.request.Request('https://yields.llama.fi/pools', headers={'User-Agent':'getmoneybeast.com'})
pools = json.load(urllib.request.urlopen(req, timeout=60))['data']
rows = []
for p in pools:
    if p.get('project') not in OK or not p.get('stablecoin') or (p.get('tvlUsd') or 0) < 100e6: continue
    if p['symbol'].upper() not in COINS: continue
    apy = p.get('apy') or 0
    if not 0 < apy < 25: continue
    rows.append({'protocol': OK[p['project']], 'project': p['project'], 'chain': p['chain'], 'coin': p['symbol'],
                 'apy': round(apy, 2), 'apyBase': round(p.get('apyBase') or 0, 2), 'tvl': round(p['tvlUsd']), 'pool': p['pool']})
rows.sort(key=lambda r: -r['apy'])
out = {'checkedAt': datetime.date.today().isoformat(), 'source': 'https://defillama.com/yields', 'pools': rows[:20]}
(ROOT/'data/defi.json').write_text(json.dumps(out, indent=1))
# keep the Aave USDC (Ethereum) row on the savings tracker in sync
aave = next((r for r in rows if r['project']=='aave-v3' and r['chain']=='Ethereum' and r['coin']=='USDC'), None)
if aave:
    rp = ROOT/'data/rates.json'; d = json.loads(rp.read_text())
    for pr in d['providers']:
        if pr['id']=='aave':
            pr['base'] = aave['apy']
            now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
            pr['observedAt'] = now; pr['verifiedAt'] = datetime.date.today().isoformat()
            pr['product'] = 'USDC · Ethereum (Aave v3)'; pr['kind'] = 'DeFi lending · Aave v3'
            pr['details'] = (f"Deposit APY for the Aave v3 USDC pool on Ethereum as reported by DefiLlama at {now}. "
                "This is one USDC market, not a protocol-wide rate. Rates change with how much of the pool is borrowed and can fall quickly; "
                "other assets, networks, and markets have different yields. Network fees reduce net returns. Withdrawals depend on available liquidity.")
            src = {'label': 'DefiLlama pool data (refreshed daily)', 'url': 'https://defillama.com/yields/pool/' + aave['pool']}
            pr['sources'] = [src] + [x for x in pr.get('sources', []) if 'defillama' not in x['url'] and 'pro.aave.com' not in x['url']]
    rp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
print(f"defi: {len(rows)} pools; top {rows[0]['protocol']} {rows[0]['coin']} {rows[0]['apy']}%" if rows else 'defi: none')
