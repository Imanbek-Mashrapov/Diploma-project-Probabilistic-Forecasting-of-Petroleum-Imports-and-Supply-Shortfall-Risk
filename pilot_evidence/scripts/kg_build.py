# Build the Kyrgyz monthly series from Comtrade preview files and reconcile with the energy balance
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json,glob,sys,os
import pandas as pd, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.width',220,'display.max_columns',40,'display.max_rows',300)
rows=[]
for f in sorted(glob.glob('dl_comtrade/kg/*.json')):
    flow=os.path.basename(f)[0]
    d=json.load(open(f,encoding='utf-8'))
    rows+= [dict(flow=flow,period=r['period'],cmd=r['cmdCode'],partner=r['partnerDesc'],pcode=r['partnerCode'],p2=r['partner2Code'],mot=r['motCode'],cust=r['customsCode'],kg=r['netWgt'],qty=r['qty'],unit=r['qtyUnitAbbr'],usd=r['primaryValue'],est=r['isNetWgtEstimated'],cl=r['classificationCode']) for r in (d.get('data') or [])]
df=pd.DataFrame(rows); df.to_csv('kg_long.csv',index=False)
print(df.shape, df.flow.value_counts().to_dict(), 'periods',df.period.nunique(), df.period.min(), df.period.max())
print('mot',df.mot.value_counts().head(4).to_dict(),'cust',df.cust.value_counts().head(3).to_dict(),'p2',df.p2.value_counts().head(3).to_dict())
print('cl',df.groupby('cl').period.agg(['min','max','nunique']))
print('null kg share',df.kg.isna().mean(),'zero kg',(df.kg==0).mean(),'est',df.est.mean())
print(df.groupby('cmd').size())
