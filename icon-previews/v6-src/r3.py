exec(open('g.py').read())
import json;F=json.load(open('F.json'))
H3="M25.4 24.8 C29.5 23.8 34.5 23.8 38.6 24.8 C38.5 31 37.3 35.5 37.3 40 C37 45.5 34.8 49.6 32 51.6 C29.2 49.6 27 45.5 26.7 40 C26.7 35.5 25.5 31 25.4 24.8 Z"
def ex(bgc): return f'<path d="M28 32.6 Q29.6 31.7 31.1 32.6 Q29.6 33.3 28 32.6Z M36 32.6 Q34.4 31.7 32.9 32.6 Q34.4 33.3 36 32.6Z" fill="{bgc}"/><path d="M30.1 47.2 a.9 .9 0 1 0 .1 0 Z M33.9 47.2 a.9 .9 0 1 0 .1 0Z" fill="{bgc}"/>'
out=[]
for k,bgc in (('A','#0D4A33'),('B','#0D4A33'),('C','#0B0D0C')):
    p=dict(F[k],head=H3,ears='');p['x']=ex(bgc);F[k]=p
s=open('g.py').read()
exec(s.replace("    return all_(f'fill=\"{f}\"')","    return all_(f'fill=\"{f}\"')+p.get('x','')").replace("+all_(f'fill=\"{f}\"')\n","+all_(f'fill=\"{f}\"')+p.get('x','')\n"))
sheet([(k,icon(F[k]),icon(F[k],True)) for k in 'ABC'],'r4.png');json.dump(F,open('F4.json','w'))
