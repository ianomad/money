import cairosvg,io,re
def mir(d):
    out=[];nums=[]
    toks=re.findall(r'[A-Za-z]|-?[\d.]+',d);i=0;res=[]
    k=0
    for t in toks:
        if t.isalpha(): res.append(t);k=0
        else:
            v=float(t)
            if k%2==0: v=64-v
            res.append(f'{v:g}');k+=1
    return ' '.join(res)
from PIL import Image,ImageDraw
HALF="M32 19.5 L21 19.5 C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5 L20.3 26.8 C16 27 12.5 28.2 11 29.5 C14 31 17.5 31 20.6 30.5 C21 35 22.3 38.5 23 41 C21.4 43 21 46 21.2 49 C21.5 53 24 55.5 28 55.5 L32 55.5 Z"
HORN="M21 19.5 C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5 Z"
DEFS='<defs><linearGradient id="au" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" stop-color="#F5D77A"/><stop offset=".22" stop-color="#B8862B"/><stop offset=".36" stop-color="#F5D77A"/><stop offset=".42" stop-color="#FFF6D5"/><stop offset=".5" stop-color="#F5D77A"/><stop offset=".68" stop-color="#B8862B"/><stop offset="1" stop-color="#6B4A0E"/></linearGradient><linearGradient id="hl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFF6D5" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".85"/><stop offset="1" stop-color="#FFF6D5" stop-opacity="0"/></linearGradient><radialGradient id="sh" cx=".5" cy=".18" r=".6"><stop offset="0" stop-color="#2E8C66" stop-opacity=".55"/><stop offset="1" stop-color="#2E8C66" stop-opacity="0"/></radialGradient><radialGradient id="em" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="#11593E"/><stop offset="1" stop-color="#08301F"/></radialGradient></defs>'
def bull(fill,cut,horn=None,half=HALF):
    m='transform="matrix(-1 0 0 1 64 0)"'
    s=f'<path d="{half}" fill="{fill}"/><path d="{half}" fill="{fill}" {m}/>'
    if fill=='url(#au)' or horn:
        clipd=(HORN if horn and fill!='url(#au)' else half)
        cp=f'<clipPath id="bc"><path d="{clipd}"/><path d="{clipd}" {m}/></clipPath>'
        full=clipd+' '+mir(clipd)
        comp='M-10 -10H74V74H-10Z '+full
        sh=(f'{cp}<g clip-path="url(#bc)">'
            f'<path d="{comp}" fill-rule="evenodd" fill="#6B4A0E" fill-opacity=".6" transform="translate(0 -1.1)"/>'
            f'<path d="{comp}" fill-rule="evenodd" fill="#FFF6D5" fill-opacity=".75" transform="translate(0 .55)"/>'
            f'<path d="M4 13.5 C18 17.5 46 17.5 60 13.5 L60 15.3 C46 19.6 18 19.6 4 15.3 Z" fill="url(#hl)"/>'
            f'<path d="M24 22.6 C29 21.8 35 21.8 40 22.6 L40 23.5 C35 22.8 29 22.8 24 23.5 Z" fill="#FFFFFF" fill-opacity=".55"/></g>')
    else: sh=''
    if horn: s+=f'<path d="{HORN}" fill="{horn}"/><path d="{HORN}" fill="{horn}" {m}/>'
    if horn: s+=sh
    elif fill=='url(#au)': s+=sh
    if cut: s+=f'<ellipse cx="27.6" cy="49.6" rx="1.3" ry="1.85" fill="{cut}"/><ellipse cx="36.4" cy="49.6" rx="1.3" ry="1.85" fill="{cut}"/><path d="M24 33.2 Q26 32 28 33.2 Q26 34.2 24 33.2Z M40 33.2 Q38 32 36 33.2 Q38 34.2 40 33.2Z" fill="{cut}"/>'
    return s
def svg(bg,body,rx=14,ring=None,sc=.92,cy=33.5):
    r=f'<circle cx="32" cy="32" r="{ring[0]}" fill="none" stroke="url(#au)" stroke-width="{ring[1]}"/>' if ring else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{DEFS}<rect width="64" height="64" rx="{rx}" fill="{bg}"/><rect width="64" height="64" rx="{rx}" fill="url(#sh)"/>{r}<g transform="translate(32 32) scale({sc}) translate(-32 -{cy})">{body}</g></svg>'
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
