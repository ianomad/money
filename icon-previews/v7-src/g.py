import cairosvg,io
from PIL import Image,ImageDraw
HALF="M32 19.5 L21 19.5 C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5 L20.3 26.8 C16 27 12.5 28.2 11 29.5 C14 31 17.5 31 20.6 30.5 C21 35 22.3 38.5 23 41 C21.4 43 21 46 21.2 49 C21.5 53 24 55.5 28 55.5 L32 55.5 Z"
HORN="M21 19.5 C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5 Z"
DEFS='<defs><linearGradient id="au" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E8D08E"/><stop offset=".5" stop-color="#C8A253"/><stop offset="1" stop-color="#A8843A"/></linearGradient><radialGradient id="em" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="#11593E"/><stop offset="1" stop-color="#08301F"/></radialGradient></defs>'
def bull(fill,cut,horn=None,half=HALF):
    m='transform="matrix(-1 0 0 1 64 0)"'
    s=f'<path d="{half}" fill="{fill}"/><path d="{half}" fill="{fill}" {m}/>'
    if horn: s+=f'<path d="{HORN}" fill="{horn}"/><path d="{HORN}" fill="{horn}" {m}/>'
    if cut: s+=f'<ellipse cx="27.6" cy="49.6" rx="1.3" ry="1.85" fill="{cut}"/><ellipse cx="36.4" cy="49.6" rx="1.3" ry="1.85" fill="{cut}"/><path d="M24 33.2 Q26 32 28 33.2 Q26 34.2 24 33.2Z M40 33.2 Q38 32 36 33.2 Q38 34.2 40 33.2Z" fill="{cut}"/>'
    return s
def svg(bg,body,rx=14,ring=None,sc=.92,cy=33.5):
    r=f'<circle cx="32" cy="32" r="{ring[0]}" fill="none" stroke="url(#au)" stroke-width="{ring[1]}"/>' if ring else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{DEFS}<rect width="64" height="64" rx="{rx}" fill="{bg}"/>{r}<g transform="translate(32 32) scale({sc}) translate(-32 -{cy})">{body}</g></svg>'
R=lambda s,n:Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(),output_width=n,output_height=n))).convert('RGB')
def sheet(rows,out,sil=None):
    H=228*len(rows)+(130 if sil else 0)
    Wd=Image.new('RGB',(600,H),'white');d=ImageDraw.Draw(Wd);m=Image.new('L',(200,200),0);ImageDraw.Draw(m).ellipse((0,0,199,199),fill=255)
    y0=0
    if sil:
        d.text((8,10),'SILHOUETTE',fill='black');Wd.paste(R(sil,110),(70,10));Wd.paste(R(sil,32),(200,10));Wd.paste(R(sil,16),(245,10));y0=130
    for i,(lab,s,a) in enumerate(rows):
        y=y0+14+i*228;d.text((8,y),lab,fill='black')
        Wd.paste(R(s,180),(70,y));Wd.paste(R(s,32),(265,y));Wd.paste(R(s,16),(310,y));Wd.paste(R(s,32).resize((96,96),Image.NEAREST),(265,y+60));Wd.paste(R(a,200),(390,y),m)
    Wd.save(out)
def sil(half=HALF): return svg('#ffffff',bull('#000',None,half=half),rx=0)
