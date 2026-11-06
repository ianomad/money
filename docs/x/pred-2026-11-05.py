from PIL import Image, ImageDraw, ImageFont
W,H=1600,900
im=Image.new("RGB",(W,H),(11,20,17)); d=ImageDraw.Draw(im)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f=lambda p,s: ImageFont.truetype(p,s)
G=(46,204,113); Wt=(240,245,242); Gr=(150,165,158)
d.text((90,70),"TOMORROW'S CALLS",font=f(B,46),fill=G)
d.text((90,130),"Fri Nov 6 before the open · graded Fri close",font=f(R,34),fill=Gr)
def card(y,num,title,sub):
    d.rounded_rectangle((90,y,1510,y+250),28,fill=(20,36,30),outline=(40,70,58),width=3)
    d.text((130,y+40),num,font=f(B,120),fill=G)
    d.text((290,y+55),title,font=f(B,64),fill=Wt)
    d.text((290,y+150),sub,font=f(R,34),fill=Gr)
card(230,"1","$VST moves less than ±6.9%","Thu close → Fri close · options ±6.9% · 0 of last 4 beat it")
card(530,"2","$MRNA moves less than ±8.3%","Thu close → Fri close · options ±8.3% · 0 of last 4 beat it")
d.text((90,820),"@MoneyBeastHQ",font=f(B,30),fill=Gr)
im.save("pred-2026-11-05.png")
