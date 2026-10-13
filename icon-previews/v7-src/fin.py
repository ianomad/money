exec(open('r2.py').read().replace("sheet(","_=(").replace(",'r2.png',sil(HALF2))",")"))
O='/workspace/money/icon-previews/'
for k,f in V.items():
    open(O+f'bull-v7{k}.svg','w').write(f(False));open(O+f'bull-v7{k}-avatar.svg','w').write(f(True));R(f(True),1000).save(O+f'bull-v7{k}-avatar.png')
sheet([(k.upper(),f(False),f(True)) for k,f in V.items()],O+'bull-v7-preview.png',sil(HALF2))
