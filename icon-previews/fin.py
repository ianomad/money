exec(open('r5.py').read().replace("sheet([A,B],'r5.png')",""))
O='/workspace/money/icon-previews/'
for n,p in (('a',A),('b',B)):
    open(O+f'bull-v3{n}.svg','w').write(icon(p)); open(O+f'bull-v3{n}-avatar.svg','w').write(icon(p,True))
    R(icon(p,True),1000).save(O+f'bull-v3{n}-avatar.png')
cur=open(O+'bull-polished.svg').read();cura=open(O+'bull-avatar.svg').read()
W=Image.new('RGB',(600,700),'white');d=ImageDraw.Draw(W);m=Image.new('L',(200,200),0);ImageDraw.Draw(m).ellipse((0,0,199,199),fill=255)
for i,(lab,s,a) in enumerate((('CURRENT',cur,cura),('A',icon(A),icon(A,True)),('B',icon(B),icon(B,True)))):
    y=15+i*228;d.text((8,y),lab,fill='black')
    W.paste(R(s,180),(70,y));W.paste(R(s,32),(265,y));W.paste(R(s,16),(310,y));W.paste(R(s,32).resize((96,96),Image.NEAREST),(265,y+60));W.paste(R(a,200),(390,y),m)
W.save(O+'bull-v3-preview.png')
