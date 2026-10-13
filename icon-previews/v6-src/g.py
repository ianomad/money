import cairosvg,io,math
from PIL import Image,ImageDraw
EM='#0E4D36';EMD='#08301F';K='#0B0D0C'
GOLD='<linearGradient id="au" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E8D08E"/><stop offset=".5" stop-color="#C8A253"/><stop offset="1" stop-color="#A8843A"/></linearGradient>'
def crescent(cA,cB,rA,rB):
    y=(rB**2-rA**2+cA**2-cB**2)/(2*(cA-cB)); x=math.sqrt(rA**2-(y-cA)**2)
    return f"M{32-x:.2f} {y:.2f} A{rA} {rA} 0 {1 if y<cA else 0} 0 {32+x:.2f} {y:.2f} A{rB} {rB} 0 {1 if y<cB else 0} 1 {32-x:.2f} {y:.2f} Z"
def mark(p):
    horn=crescent(*p['cr']);head=p['head'];f=p['fill']
    ears=p.get('ears','');paths=[horn,head]+([ears,f'{ears}'] if ears else [])
    def all_(attr,tf=True):
        o=''.join(f'<path d="{d}" {attr}/>' for d in [horn,head]+([ears] if ears else []))
        if ears: o+=f'<path d="{ears}" {attr} transform="matrix(-1 0 0 1 64 0)"/>'
        return o
    if p.get('keyline'):
        return all_(f'fill="none" stroke="url(#au)" stroke-width="{p["keyline"]}" stroke-linejoin="round"')+all_(f'fill="{f}"')
    if p.get('engr'):
        return all_(f'fill="url(#au)" stroke="url(#au)" stroke-width="{p["engr"]*2+1.6}" stroke-linejoin="round"')+all_(f'fill="{p["bgc"]}" stroke="{p["bgc"]}" stroke-width="{p["engr"]*2}" stroke-linejoin="round"')+all_(f'fill="{p["bgc"]}"')
    if p.get('line'):
        sw=p['sw'];return f'<g fill="none" stroke="{f}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"><path d="{horn}"/><path d="{head}"/></g>'
    return all_(f'fill="{f}"')
def icon(p,av=False,size='i'):
    bg=p['bg'];ring=p.get('ring')
    sc=p.get('s',.95) if not av else p.get('as',.72)
    r=f'<circle cx="32" cy="32" r="{p.get("rr",27.5) if not av else 29.6}" fill="none" stroke="url(#au)" stroke-width="{p.get("rw",1.6) if not av else .55}"/>' if ring else ''
    shape='<rect width="64" height="64" fill="{}"/>'.format(bg) if av else f'<rect width="64" height="64" rx="14" fill="{bg}"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{GOLD}<radialGradient id="bgv" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="#11593E"/><stop offset="1" stop-color="{EMD}"/></radialGradient></defs>{shape}{r}<g transform="translate(32 32) scale({sc}) translate(-32 {-p.get("cy",33)})">{mark(p)}</g></svg>'
R=lambda s,n:Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(),output_width=n,output_height=n))).convert('RGB')
def sheet(rows,out):
    Wd=Image.new('RGB',(600,228*len(rows)),'white');d=ImageDraw.Draw(Wd);m=Image.new('L',(200,200),0);ImageDraw.Draw(m).ellipse((0,0,199,199),fill=255)
    for i,(lab,s,a) in enumerate(rows):
        y=14+i*228;d.text((8,y),lab,fill='black')
        Wd.paste(R(s,180),(70,y));Wd.paste(R(s,32),(265,y));Wd.paste(R(s,16),(310,y));Wd.paste(R(s,32).resize((96,96),Image.NEAREST),(265,y+60));Wd.paste(R(a,200),(390,y),m)
    Wd.save(out)
HEAD="M24.5 24.5 C29 23.2 35 23.2 39.5 24.5 L38 39 C37.2 45 35 49.5 32 51.5 C29 49.5 26.8 45 26 39 Z"
