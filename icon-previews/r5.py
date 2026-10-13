exec(open('gen.py').read())
import json;F=json.load(open('final.json'));A=F['A']
s=open('gen.py').read()
B=dict(A,shade="M0 0",coy=-20,ring='#28C878')
def iconB(p,avatar=False):
    return oldicon(p,avatar).replace(f'<path d="{p["horn"]}" fill="{G}"/>',f'<path d="{p["horn"]}" fill="{AU}"/>')
import types
oldicon=icon
def icon(p,avatar=False):
    return iconB(p,avatar) if p.get('gold') else oldicon(p,avatar)
B['gold']=1
sheet([A,B],'r5.png')
json.dump({'A':A,'B':B},open('final.json','w'))
