exec(open('g8.py').read())
HALF2=HALF.replace("C13 19.5 8 17 5.5 11 C5 18 9 24.5 20 25.5","C13.5 19.8 9 16.5 7 8.8 C4.6 16.5 7.6 25 20 25.8")
HORN="M21 19.5 C13.5 19.8 9 16.5 7 8.8 C4.6 16.5 7.6 25 20 25.8 Z"
EM='#0D4A33';O='/workspace/money/icon-previews/'
ic=svg('url(#em)',bull('url(#au)',EM,half=HALF2),rx=14,sc=1.1,cy=32.2)
av=svg('url(#em)',bull('url(#au)',EM,half=HALF2),rx=0,sc=1.0,cy=26.6)
open(O+'bull-v8a-big.svg','w').write(ic);open(O+'bull-v8a-big-avatar.svg','w').write(av)
R(av,1000).save(O+'bull-v8a-big-avatar.png')
m=Image.new('L',(400,400),0);ImageDraw.Draw(m).ellipse((0,0,399,399),fill=255)
W=Image.new('RGB',(900,420),'white');a=R(av,400);W.paste(a,(10,10),m)
d=ImageDraw.Draw(W);d.ellipse((10,10,409,409),outline='red')
W.paste(R(ic,180),(440,10));W.paste(R(ic,32),(640,10));W.paste(R(ic,16),(690,10));W.paste(R(ic,32).resize((128,128),Image.NEAREST),(640,60))
W.save(O+'bull-v8a-big-check.png')
