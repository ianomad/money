"""Share-card images for X / iMessage / Slack: python3 scripts/build_og.py

Writes docs/og/<name>.png (1200x630) with ONE live number per page, taken from the same data the pages use
(rates.json, insights.json, markets.json, cards.json, and the article builders' own build()), plus
docs/og/meta.json (alt text per card). Called at the end of compose.py, so the daily refresh keeps the numbers current.
Never invents numbers: if a number can't be derived, the card falls back to the page's own headline text.
Pages only reference these images in <meta> tags (crawlers fetch them); no page loads them.
"""
import json, re, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]; D = ROOT/'docs'; OUT = D/'og'; FONTS = Path(__file__).resolve().parent/'fonts'
W, H = 1200, 630
PAPER, INK, MUTED, LINE, GOLD, DARK, GOLD_HI = '#fbfaf6', '#17181a', '#5f6062', '#e6e2d6', '#8a6a1f', '#141414', '#f3d27a'
PAGES = ['home', 'markets', 'cards', 'best-hysa', 'best-nofee-cards', 'tbills-vs-savings-california', 'pay-property-tax-credit-card']

def dj(n): return json.loads((ROOT/'data'/n).read_text())
def pct(v): return f'{v:.2f}%'

def _plain_top():
    """Same rule as build_article_hysa: top insured plain bank rate, no boost/promo/membership."""
    rj = dj('rates.json')
    cash = [p for p in rj['providers'] if p.get('category') == 'cash' and p.get('base') is not None]
    plain = sorted([p for p in cash if p.get('boost') is None and (p.get('fdic') or {}).get('status') == 'bank'
                    and 'paused' not in (p.get('rateLabel') or '').lower()], key=lambda p: -p['base'])
    try: nat = dj('insights.json')['inputs']['fdicNational']['savings']
    except Exception: nat = None
    return plain[0], nat

def _h1(page):
    try:
        h = (D/page).read_text(); m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    except Exception: return 'Money'

def specs():
    """name -> dict(eyebrow, big, line, alt). Each is wrapped so one bad source only drops to the page's headline text."""
    out = {}
    def put(name, page, fn):
        try: out[name] = fn()
        except Exception as ex:
            print(f'og: {name} fell back to headline ({ex!r})')
            out[name] = dict(eyebrow='MONEY', big='', line=_h1(page), alt=f'Money: {_h1(page)}')
    def home():
        top, nat = _plain_top()
        line = f'{top["name"]} pays it with no conditions.' + (f' The US average is {pct(nat)}.' if nat is not None else '')
        return dict(eyebrow='Top no-strings savings rate', big=pct(top['base']), line=line,
                    alt=f'Top no-strings savings rate: {top["name"]} {pct(top["base"])}' + (f' vs the {pct(nat)} US average' if nat is not None else ''))
    def hysa():
        top, nat = _plain_top()
        if nat is None: raise ValueError('no national average')
        a, b = 10000*top['base']/100, 10000*nat/100
        return dict(eyebrow='Best no-strings savings', big=f'${a:,.0f}/yr', line=f'on $10,000 at {top["name"]}’s {pct(top["base"])}, vs ${b:,.0f} at the {pct(nat)} US average.',
                    alt=f'$10,000 earns ${a:,.0f} a year at {top["name"]} ({pct(top["base"])}) vs ${b:,.0f} at the {pct(nat)} US average savings rate')
    def markets():
        mo = dj('markets.json')['series']['mortgage']
        pay = lambda r: 400000*(r/1200)/(1-(1+r/1200)**-360)
        d = date.fromisoformat(mo['date']).strftime('%b %-d')
        return dict(eyebrow='30-year mortgage rate', big=f'{mo["value"]:.2f}%', line=f'About ${pay(mo["value"]):,.0f}/mo on a $400,000 loan, vs ${pay(mo["y1"]):,.0f} a year ago. Freddie Mac, {d}.',
                    alt=f'30-year mortgage rate {mo["value"]:.2f}%: about ${pay(mo["value"]):,.0f} a month on a $400,000 loan')
    def cards():
        import pages2
        d = dj('cards.json'); prof = d['profile']; pv = d['pointValue']
        for c in d['cards']: c['val'] = pages2.card_value(c, prof, pv)
        best = max(d['cards'], key=lambda c: c['val'])
        nofee = max((c for c in d['cards'] if c['fee'] == 0 and c['type'] == 'cash'), key=lambda c: c['val'])
        spend = sum(v for k, v in prof.items() if isinstance(v, (int, float)) and k != 'rent')
        return dict(eyebrow='Which card pays you the most?', big=f'${best["val"]:,}/yr', line=f'{best["name"]} on ${spend:,.0f}/mo of spending, after its fee. Best no-fee card: {nofee["name"]}, ${nofee["val"]:,}.',
                    alt=f'{best["name"]} pays ${best["val"]:,} a year after fees on ${spend:,.0f} a month of spending; best no-fee card {nofee["name"]} pays ${nofee["val"]:,}')
    def nofee():
        import build_article_nofee_cards as m
        desc = m.build(ROOT)[1]
        g = re.search(r'Flat ([\d.]+%) no-fee cards pay about (\$[\d,]+)/yr on a \$([\d,]+) spend mix', desc)
        return dict(eyebrow='Best no-fee cash-back cards', big=f'{g[2]}/yr', line=f'from a flat {g[1]} no-fee card on ${g[3]} a year of spending. Category cards win only on heavy dining or groceries.',
                    alt=f'A flat {g[1]} no-fee card pays about {g[2]} a year on ${g[3]} of spending')
    def tbills():
        import build_article_tbills as m
        desc = m.build(ROOT)[1]
        g = re.search(r'In the ([\d.]+%) bracket a ([\d.]+%) savings account keeps ([\d.]+%); a ([\d.]+%) (.+?) bill keeps it all', desc)
        return dict(eyebrow='T-bills vs savings in California', big=f'{g[4]} vs {g[3]}', line=f'A {g[5].replace(" week", "-week")} T-bill keeps all {g[4]}. A {g[2]} savings account keeps {g[3]} after CA tax ({g[1]} bracket).',
                    alt=f'In California’s {g[1]} bracket a {g[4]} {g[5].replace(" week", "-week")} T-bill keeps {g[4]} while {g[2]} savings keeps {g[3]} after state tax')
    def proptax():
        import build_article_proptax as m
        desc = m.build(ROOT)[1]
        g = re.search(r'CA counties charge ([\d.]+%)–([\d.]+%) to pay property tax by card', desc)
        lo, hi = float(g[1].rstrip('%')), float(g[2].rstrip('%'))
        big = f'{lo:.2f}%' if lo == hi else f'{lo:.2f}–{hi:.2f}%'
        return dict(eyebrow='California property tax by card', big=big, line='card fee charged by CA counties. eCheck is free. A 2% card loses money; a bonus minimum can win.',
                    alt=f'California counties charge {lo:.2f}% to {hi:.2f}% to pay property tax by credit card; eCheck is free')
    put('home', 'index.html', home); put('markets', 'markets.html', markets); put('cards', 'cards.html', cards)
    put('best-hysa', 'best-hysa.html', hysa); put('best-nofee-cards', 'best-nofee-cards.html', nofee)
    put('tbills-vs-savings-california', 'tbills-vs-savings-california.html', tbills); put('pay-property-tax-credit-card', 'pay-property-tax-credit-card.html', proptax)
    return out

def render(s, path):
    from PIL import Image, ImageDraw, ImageFont
    F = lambda f, n: ImageFont.truetype(str(FONTS/f), n)
    serif_b, serif, mono = 'IBMPlexSerif-SemiBold.ttf', 'IBMPlexSerif-Regular.ttf', 'IBMPlexMono-Medium.ttf'
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    M = 72
    # brand row
    try:
        ic = Image.open(D/'apple-touch-icon.png').convert('RGBA').resize((56, 56), Image.LANCZOS)
        mask = Image.new('L', (56, 56), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 55, 55), 12, fill=255)
        im.paste(ic, (M, 56), mask); x0 = M + 72
    except Exception: x0 = M
    d.text((x0, 84), 'Money', font=F(serif_b, 44), fill=INK, anchor='lm')
    d.text((W-M, 84), 'money.ilyusha.xyz', font=F(mono, 26), fill=MUTED, anchor='rm')
    d.line((M, 132, W-M, 132), fill=LINE, width=2)
    # eyebrow
    d.text((M, 178), s['eyebrow'].upper(), font=F(mono, 28), fill=GOLD, anchor='lm')
    y = 214
    if s['big']:
        size = 150
        while size > 70 and d.textlength(s['big'], font=F(serif_b, size)) > W-2*M: size -= 6
        fb = F(serif_b, size); d.text((M-4, y), s['big'], font=fb, fill=INK, anchor='la'); y += int(size*1.22)
    # wrapped line
    fl_size = 40 if s['big'] else 64
    fl = F(serif, fl_size); words, lines, cur = s['line'].split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=fl) <= W-2*M: cur = t
        else: lines.append(cur); cur = w_
    lines.append(cur)
    for ln in lines[:3]:
        d.text((M, y), ln, font=fl, fill=INK if not s['big'] else '#2c2d2f', anchor='la'); y += int(fl_size*1.3)
    # footer bar
    d.rectangle((0, H-70, W, H), fill=DARK)
    d.text((M, H-35), 'Hand-checked · No sponsored rankings', font=F(mono, 24), fill='#e9e4d6', anchor='lm')
    d.text((W-M, H-35), 'Updated ' + date.today().strftime('%b %-d, %Y'), font=F(mono, 24), fill=GOLD_HI, anchor='rm')
    im = im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(path, optimize=True)

def main():
    try: import PIL  # noqa
    except ImportError:
        print('og: Pillow not installed; keeping existing docs/og images (pip install pillow)'); return
    OUT.mkdir(exist_ok=True)
    sp = specs(); meta = {}
    for name, s in sp.items():
        p = OUT/f'{name}.png'; render(s, p)
        meta[name] = {'alt': s['alt'], 'big': s['big'], 'line': s['line']}
        print(f'og: {name}.png {p.stat().st_size//1024}KB  {s["big"]} | {s["line"]}')
    (OUT/'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False) + '\n')

if __name__ == '__main__': main()
