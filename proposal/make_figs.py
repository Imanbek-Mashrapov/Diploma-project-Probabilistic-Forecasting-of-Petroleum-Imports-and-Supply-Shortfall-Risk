import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import sys
FONT = sys.argv[1] if len(sys.argv)>1 else "Times New Roman"
SUF = sys.argv[2] if len(sys.argv)>2 else ""
plt.rcParams["font.family"] = FONT
NAVY="#1F3A5F"; BLUE="#3B6EA8"; LIGHT="#E8EEF6"; ORANGE="#C8642B"; GREY="#5A5A5A"

def box(ax,x,y,w,h,title,lines,fc=LIGHT,ec=BLUE,tc=NAVY):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.008,rounding_size=0.015",fc=fc,ec=ec,lw=1.4))
    ax.text(x+w/2,y+h-0.035,title,ha="center",va="top",fontsize=11,fontweight="bold",color=tc)
    for i,l in enumerate(lines):
        ax.text(x+0.015,y+h-0.095-i*0.052,"• "+l,ha="left",va="top",fontsize=9,color="#222")

def arrow(ax,x1,y1,x2,y2,c=GREY,label=None):
    ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle="-|>",color=c,lw=1.6))
    if label: ax.text((x1+x2)/2,(y1+y2)/2+0.02,label,ha="center",fontsize=8.5,color=c,style="italic")

# Conceptual framework
fig,ax=plt.subplots(figsize=(11,6.2)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
box(ax,0.01,0.55,0.29,0.40,"Inputs (information set at origin)",["Own import history (lags 1-12)","Supplier structure (HHI, Russia share)","Shock calendar (announced bans)","Prices & risk (Brent, GPR, FX, CPI)","Release dates (as-of masking)"])
box(ax,0.01,0.08,0.29,0.34,"Moderating conditions",["Publication lag & revisions","Panel heterogeneity","Structural breaks 2022-2026","Data quality (mass, HS 2710.19)"],fc="#F6EFE9",ec=ORANGE,tc=ORANGE)
box(ax,0.37,0.50,0.27,0.45,"Forecasting process",["Baselines, boosted trees, neural nets","Training scope: local vs global","Quantile output (pinball loss)","Conformal calibration","Rolling-origin, as-of replay"])
box(ax,0.37,0.08,0.27,0.30,"Hypotheses tested",["H1  global pooling vs local","H2  neural vs gradient boosting","H3  supplier & shock information","H4  probability vs HHI screening"],fc="white",ec=NAVY)
box(ax,0.71,0.66,0.28,0.29,"Outputs (dependent)",["Monthly import mass (t)","Quantiles & intervals","Shortfall probability"])
box(ax,0.71,0.08,0.28,0.40,"Evaluation & use",["Accuracy: MASE, WAPE","Calibration: coverage, CRPS","Warning: PR-AUC, recall","vs. HHI screening","Risk monitor for planners"])
arrow(ax,0.31,0.75,0.36,0.75)
arrow(ax,0.31,0.30,0.40,0.49,c=ORANGE)
arrow(ax,0.65,0.78,0.70,0.80)
arrow(ax,0.85,0.65,0.85,0.49)
arrow(ax,0.505,0.49,0.505,0.39,c=NAVY)
plt.savefig(f"figures/fig_conceptual{SUF}.png",dpi=220,bbox_inches="tight",facecolor="white"); plt.close()

# Research flow
stages=[("1. Data acquisition","Comtrade API, official\nand external sources","done"),
("2. Cleaning &\nvalidation","Density, unit value,\nenergy-balance checks","done"),
("3. Rule freeze","Supervisor review,\nsecond snapshot","next"),
("4. As-of feature\nstore","Release-date masking,\nlagged features","plan"),
("5. Model\nbenchmark","Baselines, boosting,\nglobal neural models","plan"),
("6. Calibration &\nshortfall risk","Conformal step,\nexceedance probability","plan"),
("7. Evaluation &\nablation","Tests, effect sizes,\nRQ1-RQ4","plan"),
("8. Risk monitor &\nthesis","Prototype, user\nfeedback, write-up","plan")]
fig,ax=plt.subplots(figsize=(12,4.6)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
w=0.215; h=0.36
for i,(t,d,s) in enumerate(stages):
    r,c=divmod(i,4); cc=c if r==0 else 3-c; x=0.01+cc*0.25; y=0.56 if r==0 else 0.06
    fc={"done":"#D6E4F2","next":"#FBE7D6","plan":"white"}[s]; ec={"done":BLUE,"next":ORANGE,"plan":GREY}[s]
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.008,rounding_size=0.02",fc=fc,ec=ec,lw=1.4))
    ax.text(x+w/2,y+h-0.04,t,ha="center",va="top",fontsize=10.5,fontweight="bold",color=NAVY)
    ax.text(x+w/2,y+0.05,d,ha="center",va="bottom",fontsize=9,color="#333")
    if c<3 and r==0: arrow(ax,x+w+0.005,y+h/2,x+0.25-0.005,y+h/2)
    if c<3 and r==1: arrow(ax,x-0.005,y+h/2,x-0.25+w+0.005,y+h/2)
arrow(ax,0.01+3*0.25+w/2,0.555,0.01+3*0.25+w/2,0.43)
ax.set_ylim(-0.1,1)
# row 2 should read right-to-left? keep left-to-right with return arrow
for lab,fc,ec,xx in [("Completed",'#D6E4F2',BLUE,0.30),("Next step",'#FBE7D6',ORANGE,0.45),("Planned","white",GREY,0.60)]:
    ax.add_patch(FancyBboxPatch((xx,-0.06),0.025,0.04,boxstyle="square,pad=0",fc=fc,ec=ec)); ax.text(xx+0.032,-0.04,lab,va="center",fontsize=9)
plt.savefig(f"figures/fig_flow{SUF}.png",dpi=220,bbox_inches="tight",facecolor="white"); plt.close()
print("ok")
