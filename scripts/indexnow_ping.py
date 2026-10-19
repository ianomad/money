"""Notify IndexNow (Bing, Yandex, Seznam, Naver; Bing feeds DuckDuckGo/Yahoo) of site URLs. Free, no account.
Key file docs/eee57cc8470cf61aee1a47a2c3905510.txt proves ownership. Run after a deploy that adds or materially changes pages:
  python3 scripts/indexnow_ping.py            # all sitemap URLs
  python3 scripts/indexnow_ping.py /best-hysa # specific paths
"""
import json, re, sys, urllib.request
BASE = 'https://money.ilyusha.xyz'
KEY = 'eee57cc8470cf61aee1a47a2c3905510'
paths = sys.argv[1:]
if paths:
    urls = [BASE + p for p in paths]
else:
    sm = urllib.request.urlopen(BASE + '/sitemap.xml', timeout=20).read().decode()
    urls = re.findall(r'<loc>([^<]+)</loc>', sm)
body = json.dumps({'host': 'money.ilyusha.xyz', 'key': KEY, 'keyLocation': f'{BASE}/{KEY}.txt', 'urlList': urls}).encode()
req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
try:
    r = urllib.request.urlopen(req, timeout=30); print(r.status, len(urls), 'urls')
except urllib.error.HTTPError as e:
    print(e.code, e.read()[:300])
