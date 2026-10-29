import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
bg="#f5efe3"; ink="#2b2724"; red="#b5493c"; gold="#c9a32a"
labels=["Alphabet (GOOGL)","Nasdaq Composite","S&P 500","Small caps (IWM)","Equal-weight S&P (RSP)"]
vals=[-12.64,-1.38,-0.30,0.97,1.20]
fig,ax=plt.subplots(figsize=(10.24,5.76),dpi=100); fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
y=list(range(len(labels)))[::-1]
ax.barh(y,vals,color=[red if v<0 else gold for v in vals],height=0.6)
for yi,v in zip(y,vals):
    ax.text(v+(0.25 if v>=0 else -0.25),yi,f"{v:+.1f}%",va="center",ha="left" if v>=0 else "right",fontsize=17,fontweight="bold",color=ink)
ax.set_yticks(y); ax.set_yticklabels(labels,fontsize=14,color=ink)
ax.axvline(0,color=ink,lw=1.2); ax.set_xlim(-16,4)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([]); ax.tick_params(left=False)
fig.text(0.05,0.92,"The index fell. The average stock rose.",fontsize=24,fontweight="bold",color=ink)
fig.text(0.05,0.86,"Thu Oct 29, 2026 close. 9 of 11 S&P sectors finished green; VIX fell to 16.4.",fontsize=13,color="#5c554e")
fig.text(0.05,0.03,"Source: Yahoo Finance closing prices, Oct 29, 2026   |   @MoneyBeastHQ",fontsize=10,color="#5c554e")
plt.subplots_adjust(left=0.27,right=0.95,top=0.80,bottom=0.10)
fig.savefig("docs/x/index-vs-average-2026-10-29.png",facecolor=bg)
