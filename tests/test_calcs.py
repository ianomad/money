"""Calculator unit tests with concrete examples. Run: python3 tests/test_calcs.py (also run by scripts/check_data.py)."""
import sys, json, subprocess, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
# Frozen data snapshot: daily rate changes must not fail the build; only real math bugs should.
FIX = ROOT / 'tests' / 'fixtures'; os.environ['MB_DATA'] = str(FIX)
import savings as S
T = '2026-10-26'
D, problems = S.dataset(T)
def one(pid, b, opt, today=T):
    r = S.run(D, b, opt, today); row = [x for x in r['rows'] if x['id'] == pid]
    return row[0] if row else [s for s in r['skipped'] if s['id'] == pid][0]
def near(a, b, tol=0.01): assert abs(a - b) <= tol, (a, b)
CASES = []
def case(name):
    def w(f): CASES.append((name, f)); return f
    return w
@case('plain rate: Pibank 4.40% on $10,000 = $440')
def _(): near(one('pibank', 10000, {})['net'], 440)
@case('6-month promo is not annualized: Openbank 4.35% x 6mo + 4.00% x 6mo on $10,000 = $417.50')
def _(): r = one('openbank', 10000, {'new': True}); near(r['net'], 417.5); near(r['promoMonths'], 6)
@case('3-month referral: Marcus $10,000 = $375, not $450')
def _(): near(one('marcus', 10000, {'new': True, 'referral': True})['net'], 375)
@case('cap + fee: SoFi Plus $30,000 = 940 + 330 - 120 = $1,150')
def _(): r = one('sofi', 30000, {'fee': True}); near(r['gross'], 1270); near(r['net'], 1150)
@case('capped promo: Axos $100,000 new + DD = $4,407.50')
def _(): near(one('axos', 100000, {'new': True, 'dd': True})['net'], 4407.5, 0.02)
@case('expired offer falls back: Axos after Oct 31 opening window = 4.21% -> $4,210')
def _(): r = one('axos', 100000, {'new': True, 'dd': True}, '2026-11-01'); near(r['net'], 4210, 0.02)
@case('balance above interest cap: Elevault $600,000 earns on $500,000 only = $21,700')
def _(): near(one('elevault', 600000, {})['net'], 21700)
@case('unpublished tier: Barclays $2,000,000 is not estimated')
def _(): assert 'why' in one('barclays', 2_000_000, {})
@case('promo with an end date: Betterment counts only until Feb 15, 2027')
def _():
    pm = 112 / 30.4375; near(one('betterment', 10000, {'new': True})['net'], 425 * pm / 12 + 350 * (12 - pm) / 12)
@case('split cap during promo: Wealthfront $200,000 referral + deposits = $7,881.25')
def _(): near(one('wealthfront', 200000, {'referral': True, 'activity': True})['net'], 7881.25)
@case('whole-balance tier: CIT $4,000 new = $20')
def _(): near(one('cit', 4000, {'new': True})['net'], 20)
@case('minimum to open: Openbank $400 not counted')
def _(): assert 'why' in one('openbank', 400, {'new': True})
@case('fee makes the paid tier worse: X Money $10,000 picks the free 4.00% ($400) over Premium+ ($205)')
def _(): r = one('x-money', 10000, {'fee': True}); near(r['net'], 400); assert r['fee'] == 0
@case('paused offers are never ranked: Newtek')
def _(): assert one('newtek', 10000, {})['why'] == 'not taking new applications'
@case('data model matches rates.json (no problems)')
def _(): assert not problems, problems
@case('JS calculator returns the same numbers as Python')
def _():
    opts = [{}, {'new': True}, {'new': True, 'dd': True, 'fee': True, 'referral': True, 'activity': True}, {'bankOnly': True, 'noPromo': True}]
    bals = [400, 4000, 10000, 30000, 100000, 600000, 2000000]
    js = (ROOT / 'scripts/savings_calc.js').read_text() + f"\nconst D={json.dumps(D)};const out=[];for(const b of {bals})for(const o of {json.dumps(opts)}){{const r=MBCalc.run(D,b,o,'{T}');out.push(r.rows.map(x=>[x.id,Math.round(x.net*100)]))}};console.log(JSON.stringify(out))"
    got = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
    want = [[[x['id'], round(x['net'] * 100)] for x in S.run(D, b, o, T)['rows']] for b in bals for o in opts]
    assert got == want, 'JS/Python mismatch'
import world as W
@case('World: annual rate is not the term return: 44.5% for 1 month = 3.7% over the term')
def _(): near(W.calc(10000, 44.5, 1, 0, 0, 4.4)['termReturn'], 44.5 / 12)
@case('World: 1% conversion each way, no FX move: Turkey $10,000, 1 month = $10,164')
def _(): near(W.calc(10000, 44.5, 1, 0, 1, 4.4)['end'], 10000 * 0.99 ** 2 * (1 + 0.445 / 12))
@case('World: currency falls 10%: KGS 14.5% for 24 months, no costs = $11,610')
def _(): near(W.calc(10000, 14.5, 24, -10, 0, 4.4)['end'], 11610)
@case('World: break-even vs keeping dollars: 14.5% for 24 months, no costs = currency can fall 22.5%')
def _(): near(W.calc(10000, 14.5, 24, 0, 0, 4.4)['beZero'], (1 / 1.29 - 1) * 100); assert abs(W.calc(10000, 14.5, 24, 0, 0, 4.4)['beZero'] + 22.48) < 0.01
@case('World: break-even vs US savings at 4.4% for 24 months = currency can fall 15.7%')
def _(): near(W.calc(10000, 14.5, 24, 0, 0, 4.4)['beUS'], (1.088 / 1.29 - 1) * 100)
@case('World: yearly currency move: 349.95 -> 1528.26 ARS per $ over 3 years = about -38.8%/yr')
def _(): near(W.yearly_move(349.95, 1528.26, 3), ((349.95 / 1528.26) ** (1 / 3) - 1) * 100)
@case('World: no country is labelled best; 10 tracked countries stated')
def _():
    h = (ROOT / 'docs/index.html').read_text()
    v = h[h.index('id="view-world"'):]
    import re as _re
    assert 'Top pick abroad' not in h and 'best in the world' not in h.lower() and _re.search(r'\d+ tracked countries', v)
@case('World: JS calculator matches Python')
def _():
    cases = [(10000, 44.5, 1, 0, 1, 4.4), (5000, 14.5, 24, -10, 0.5, 4.4), (25000, 9.25, 12, 3, 0, 4.4)]
    js = (ROOT / 'scripts/world_calc.js').read_text() + f"\nconsole.log(JSON.stringify({json.dumps(cases)}.map(c=>{{const k=MBWorld.calc(...c);return [k.end,k.beZero,k.beUS,k.termReturn].map(x=>Math.round(x*1e6))}})))"
    got = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
    want = [[round(x * 1e6) for x in (k['end'], k['beZero'], k['beUS'], k['termReturn'])] for k in (W.calc(*c) for c in cases)]
    assert got == want, (got, want)
import pages2 as P
_CD = json.loads((FIX / 'cards.json').read_text()); _CB = {c['id']: c for c in _CD['cards']}; _PR = _CD['profile']
@case('Cards: Chase Sapphire Preferred at $2,000/mo, 1c points = $373 rewards - $95 fee = $278 (verified on Chase Oct 26, 2026)')
def _(): near(P.card_rewards(_CB['csp'], _PR), 373.2); assert P.card_value(_CB['csp'], _PR) == 278
@case('Cards: CSP first year adds 75,000 points = $750 because $6,000 in 3 months meets $5,000 -> $1,028')
def _(): assert P.card_value(_CB['csp'], _PR, 0.01, True) == 1028
@case('Cards: bonus not counted if spend misses requirement: CSP at $1,000/mo (3,000 < 5,000)')
def _(): assert P.card_bonus(_CB['csp'], {k: v / 2 for k, v in _PR.items()}) == 0
@case('Cards: points at 1.5c raise CSP to $373.2*1.5 - $95 = $465; cash cards unchanged')
def _(): assert P.card_value(_CB['csp'], _PR, 0.015) == 465 and P.card_value(_CB['dc'], _PR, 0.015) == 480
@case('Cards: Blue Cash Preferred grocery cap: $1,000/mo groceries = $6,000*6% + $6,000*1%')
def _(): p = dict.fromkeys(_PR, 0); p['groceries'] = 1000; assert P.card_value(_CB['bcp'], p) == round(360 + 60 - 95)
@case('Cards: JS calculator matches Python on every card (3 scenarios)')
def _():
    sc = [(_PR, 1, False), (_PR, 1.7, True), ({k: v * 3 for k, v in _PR.items()}, 0.8, True)]
    js = (ROOT / 'scripts/cards_calc.js').read_text() + f"\nconst C={json.dumps(_CD['cards'])},S={json.dumps(sc)};console.log(JSON.stringify(S.map(s=>C.map(c=>MBCards.value(c,s[0],s[1],s[2])))))"
    got = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
    want = [[P.card_value(c, p, cpp / 100, fy) for c in _CD['cards']] for p, cpp, fy in sc]
    assert got == want, (got, want)
def main():
    bad = 0
    for n, f in CASES:
        try: f(); print('ok  ', n)
        except Exception as ex: bad += 1; print('FAIL', n, '->', repr(ex))
    return bad
if __name__ == '__main__': sys.exit(1 if main() else 0)
