# Check monthly Comtrade availability for landlocked and comparison reporters
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json,time,sys,collections,requests
R={4:'Afghanistan',51:'Armenia',31:'Azerbaijan',64:'Bhutan',68:'Bolivia',72:'Botswana',854:'Burkina Faso',108:'Burundi',140:'CAR',148:'Chad',748:'Eswatini',231:'Ethiopia',398:'Kazakhstan',417:'Kyrgyzstan',418:'Lao PDR',426:'Lesotho',454:'Malawi',466:'Mali',498:'Moldova',496:'Mongolia',524:'Nepal',562:'Niger',807:'North Macedonia',600:'Paraguay',646:'Rwanda',762:'Tajikistan',795:'Turkmenistan',800:'Uganda',860:'Uzbekistan',894:'Zambia',716:'Zimbabwe',40:'Austria',112:'Belarus',203:'Czechia',348:'Hungary',442:'Luxembourg',688:'Serbia',703:'Slovakia',757:'Switzerland',643:'Russia'}
res={}
for c,n in R.items():
    for a in range(6):
        r=requests.get('https://comtradeapi.un.org/public/v1/getDA/C/M/HS',params=dict(reporterCode=c),timeout=60)
        if r.status_code==200: break
        time.sleep(5)
    d=r.json().get('data') or []
    ps=sorted({x['period'] for x in d})
    by=collections.Counter(p//100 for p in ps)
    since15=[p for p in ps if p>=201501]
    res[n]=dict(code=c,n=len(ps),first=ps[0] if ps else None,last=ps[-1] if ps else None,n2015=len(since15),miss_since15=[y for y in range(2015,2026) if by.get(y,0)<12])
    print(n,res[n],flush=True); time.sleep(1.5)
json.dump(res,open(sys.argv[1],'w'),indent=1)
