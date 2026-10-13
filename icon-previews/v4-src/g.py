import cairosvg,io
from PIL import Image,ImageDraw
G='#28C878';GD='#1FA866';ML='#7BE3AE';K='#0B0D0C';AU='#E3B341';AUD='#B8861F';W='#F4FFF8'
def bull(p):
    hw,hy,hh=p['hw'],p['hy'],p['hh']        # head half-width, top y, height
    er,ey,ex=p['er'],p['ey'],p['ex']
    mw,my,mh=p['mw'],p['my'],p['mh']
    horn=p['horn']; ear=p['ear']
    s=[f'<defs><linearGradient id="hg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p.get("g1",G)}"/><stop offset="1" stop-color="{p.get("g2",G)}"/></linearGradient></defs>']
    s.append(f'<path d="{horn}" fill="{p.get("hc",G)}"/><path d="{horn}" fill="{p.get("hc",G)}" transform="matrix(-1 0 0 1 64 0)"/>')
    if ear: s.append(f'<path d="{ear}" fill="{GD}"/><path d="{ear}" fill="{GD}" transform="matrix(-1 0 0 1 64 0)"/>')
    s.append(f'<path d="{p["head"]}" fill="url(#hg)"/>' if p.get('head') else f'<rect x="{32-hw}" y="{hy}" width="{2*hw}" height="{hh}" rx="{hw*p.get("rr",.9)}" fill="{G}"/>')
    if not p.get('head'): s.append(f'<ellipse cx="32" cy="{my}" rx="{mw+2}" ry="{mh+1.8}" fill="{G}"/>')
    s.append(f'<ellipse cx="32" cy="{my+.6}" rx="{mw}" ry="{mh}" fill="{p.get("mc",ML)}"/>')
    for sx in (-1,1):
        s.append(f'<circle cx="{32+sx*ex}" cy="{ey}" r="{er}" fill="{K}"/><circle cx="{32+sx*ex+er*.35}" cy="{ey-er*(.1 if p.get('lid') else .38)}" r="{er*.36}" fill="{W}"/>')
        if p.get('lid'): s.append(f'<path d="M{32+sx*(ex-er-1)} {ey-er-1} L{32+sx*(ex+er+1)} {ey-er-1} L{32+sx*(ex+er+1)} {ey-er*.55} L{32+sx*(ex-er-1)} {ey-er*.05} Z" fill="{G}"/>')
        s.append(f'<ellipse cx="{32+sx*mw*.45}" cy="{my-mh*.15}" rx="{mw*.14}" ry="{mh*.26}" fill="#138A50"/>')
    if p.get('tips'):
        s.append(f'<clipPath id="tc"><circle cx="8.6" cy="13.4" r="4.2"/></clipPath><g clip-path="url(#tc)"><path d="{horn}" fill="{AU}"/></g><g clip-path="url(#tc)" transform="matrix(-1 0 0 1 64 0)"><path d="{horn}" fill="{AU}"/></g>')
    if p.get('nocoin'): return ''.join(s)
    cy=my+mh*.55+p.get('cdy',0); cr=p['cr']
    s.append(f'<circle cx="32" cy="{cy+cr*.6}" r="{cr}" fill="{AU}" stroke="{K}" stroke-width="1.2"/><circle cx="32" cy="{cy+cr*.6}" r="{cr*.62}" fill="none" stroke="{AUD}" stroke-width=".7"/>')
    return ''.join(s)
def icon(p,av=False):
    if av: return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="{K}"/><g transform="translate(32 32) scale(.74) translate(-32 {-p.get("cy",33)})">{bull(p)}</g></svg>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{K}"/><g transform="translate(32 32) scale({p.get("s",.92)}) translate(-32 {-p.get("cy",33)})">{bull(p)}</g></svg>'
R=lambda s,n:Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(),output_width=n,output_height=n))).convert('RGB')
def sheet(rows,out):
    Wd=Image.new('RGB',(600,228*len(rows)),'white');d=ImageDraw.Draw(Wd);m=Image.new('L',(200,200),0);ImageDraw.Draw(m).ellipse((0,0,199,199),fill=255)
    for i,(lab,s,a) in enumerate(rows):
        y=14+i*228;d.text((8,y),lab,fill='black')
        Wd.paste(R(s,180),(70,y));Wd.paste(R(s,32),(265,y));Wd.paste(R(s,16),(310,y));Wd.paste(R(s,32).resize((96,96),Image.NEAREST),(265,y+60));Wd.paste(R(a,200),(390,y),m)
    Wd.save(out)
BASE=dict(hw=15,hy=20,hh=34,rr=.95,er=3,ey=33,ex=7,mw=11,my=46,mh=7.5,cr=4,cy=36,
  horn="M18.5 24 C15 22 12.5 18 13 13.5 C15.5 15.5 18.5 17 22 18 Z",
  ear="M17.5 27 C13 27.5 9.5 26 8 23 C11.5 22 15 22.5 18 24.5 Z")
