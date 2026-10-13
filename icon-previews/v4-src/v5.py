exec(open('g.py').read())
import json;F=json.load(open('F.json'));O='/workspace/money/icon-previews/'
V={k.lower():dict(F[k],nocoin=1,cy=35) for k in 'ABC'}
V['a-gold']=dict(V['a'],tips=1)
rows=[]
for n,p in V.items():
    open(O+f'bull-v5{n}.svg','w').write(icon(p));open(O+f'bull-v5{n}-avatar.svg','w').write(icon(p,True))
    R(icon(p,True),1000).save(O+f'bull-v5{n}-avatar.png');rows.append((n.upper(),icon(p),icon(p,True)))
sheet(rows,O+'bull-v5-preview.png');json.dump(V,open('V5.json','w'))
