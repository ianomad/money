exec(open('gen.py').read())
import math
def crescent(cA,cB,rA,rB):
    # tips: intersection of circles
    d=cA-cB; y=(rB**2-rA**2+ (cA**2-cB**2))/(2*d) # solve
    # circle eq: x^2+(y-c)^2=r^2 -> intersection y
    y=(rB**2-rA**2+cA**2-cB**2)/(2*(cA-cB)); x=math.sqrt(rA**2-(y-cA)**2)
    return f"M{32-x:.2f} {y:.2f} A{rA} {rA} 0 {1 if y<cA else 0} 0 {32+x:.2f} {y:.2f} A{rB} {rB} 0 {1 if y<cB else 0} 1 {32-x:.2f} {y:.2f} Z"
P=[]
for cA,cB,rA,rB in [(20,12,26,26),(18,6,26,28),(14,2,25,29)]:
    P.append(dict(horn=crescent(cA,cB,rA,rB),
 head="M19 22 H45 L41.5 43 L36.5 54 H27.5 L22.5 43 Z",
 shade="M32 22 H45 L41.5 43 L36.5 54 H32 Z",
 eyes="M22.5 30 L30 34 L24 35.5 Z M41.5 30 L34 34 L40 35.5 Z",
 nos="M27.8 49.5 a1.5 1.5 0 1 0 3 0 a1.5 1.5 0 1 0 -3 0 M33.2 49.5 a1.5 1.5 0 1 0 3 0 a1.5 1.5 0 1 0 -3 0",
 coy=55.5,cor=3.6))
sheet(P,'r2.png')
