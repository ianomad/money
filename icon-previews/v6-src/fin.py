exec(open('r3.py').read().split("sheet(")[0])
O='/workspace/money/icon-previews/';rows=[]
for k in 'ABC':
    p=F[k];n=k.lower()
    open(O+f'bull-v6{n}.svg','w').write(icon(p));open(O+f'bull-v6{n}-avatar.svg','w').write(icon(p,True))
    R(icon(p,True),1000).save(O+f'bull-v6{n}-avatar.png');rows.append((k,icon(p),icon(p,True)))
sheet(rows,O+'bull-v6-preview.png')
