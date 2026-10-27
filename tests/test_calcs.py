"""Calculator unit tests with concrete examples. Run: python3 tests/test_calcs.py (also run by scripts/check_data.py)."""
import sys, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
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
def main():
    bad = 0
    for n, f in CASES:
        try: f(); print('ok  ', n)
        except Exception as ex: bad += 1; print('FAIL', n, '->', repr(ex))
    return bad
if __name__ == '__main__': sys.exit(1 if main() else 0)
