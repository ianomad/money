exec(open('g.py').read())
import json;F=json.load(open('F.json'));O='/workspace/money/icon-previews/'
v1=open(O+'bull-v1.svg').read();rows=[('v1',v1,v1)]
for k in 'ABC':
    p=F[k];n=k.lower()
    open(O+f'bull-v4{n}.svg','w').write(icon(p));open(O+f'bull-v4{n}-avatar.svg','w').write(icon(p,True))
    R(icon(p,True),1000).save(O+f'bull-v4{n}-avatar.png');rows.append((k,icon(p),icon(p,True)))
sheet(rows,O+'bull-v4-preview.png')
