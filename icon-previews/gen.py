import cairosvg,io,sys
from PIL import Image,ImageDraw
G='#28C878';D='#1A9A5C';K='#0B0D0C';AU='#E3B341'
def mark(p):
    # p: dict of params
    return f'''<path d="{p['horn']}" fill="{G}"/>
<path d="{p['head']}" fill="{G}"/>
<path d="{p['shade']}" fill="{D}"/>
<path d="{p['eyes']}" fill="{K}"/>
<path d="{p['nos']}" fill="{K}"/>
<circle cx="32" cy="{p['coy']}" r="{p['cor']}" fill="{AU}" stroke="{K}" stroke-width="1.4"/>'''
def icon(p,avatar=False):
    if avatar: return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="{K}"/><circle cx="32" cy="32" r="29.5" fill="none" stroke="{p.get("ring",AU)}" stroke-width=".7"/><g transform="translate(32 32) scale(.64) translate(-32 -33.5)">{mark(p)}</g></svg>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{K}"/><g transform="translate(32 32) scale({p.get("s",.92)}) translate(-32 -33.5)">{mark(p)}</g></svg>'
R=lambda s,n:Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(),output_width=n,output_height=n))).convert('RGB')
def sheet(ps,out):
    W=Image.new('RGB',(560,230*len(ps)),'#ffffff');m=Image.new('L',(200,200),0);ImageDraw.Draw(m).ellipse((0,0,199,199),fill=255)
    for i,p in enumerate(ps):
        y=15+i*230;s=icon(p);W.paste(R(s,180),(10,y));W.paste(R(s,32),(200,y));W.paste(R(s,16),(245,y));W.paste(R(s,32).resize((96,96),Image.NEAREST),(200,y+60));W.paste(R(icon(p,True),200),(350,y),m)
    W.save(out)
