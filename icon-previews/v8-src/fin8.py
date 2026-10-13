exec(open('g8.py').read())
HALF2=HALF.replace("C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5","C13.5 19.8 9 16.5 7 8.8 C4.6 16.5 7.6 25 20 25.8")
HORN="M21 19.5 C13.5 19.8 9 16.5 7 8.8 C4.6 16.5 7.6 25 20 25.8 Z"
EM='#0D4A33'
V={
'a':(lambda av: svg('url(#em)',bull('url(#au)',EM,half=HALF2),rx=0 if av else 14,sc=.66 if av else .9)),
'b':(lambda av: svg('#0B0D0C',bull('#17855A','#0B0D0C','url(#au)',half=HALF2),rx=0 if av else 14,sc=.66 if av else .9)),
'c':(lambda av: svg('url(#em)',bull('url(#au)',EM,half=HALF2),rx=0 if av else 14,ring=(29.6,.7) if av else (28,1.4),sc=.6 if av else .74)),
}
O='/workspace/money/icon-previews/';rows=[]
for k,f in V.items():
    open(O+f'bull-v8{k}.svg','w').write(f(False));open(O+f'bull-v8{k}-avatar.svg','w').write(f(True));R(f(True),1000).save(O+f'bull-v8{k}-avatar.png')
    v7=open(O+f'bull-v7{k}.svg').read();v7a=open(O+f'bull-v7{k}-avatar.svg').read()
    rows+= [(f'v7 {k.upper()}',v7,v7a),(f'v8 {k.upper()}',f(False),f(True))]
sheet(rows,O+'bull-v8-preview.png')
