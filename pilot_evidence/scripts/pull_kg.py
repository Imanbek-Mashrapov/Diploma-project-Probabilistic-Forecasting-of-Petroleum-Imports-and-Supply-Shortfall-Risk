# Pull all KGZ monthly fuel records (imports, exports) from the keyless Comtrade preview API
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json,time,sys,os,requests
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
avail=json.load(open(sys.argv[2]))['data']
periods=sorted({x['period'] for x in avail})
codes='2709,2710,271011,271012,271019,271020,271091,271099,271111,271112,271113,271119,271121'
for flow in sys.argv[3:]:
    for p in periods:
        f=f'{out}/{flow}_{p}.json'
        if os.path.exists(f): continue
        for attempt in range(8):
            r=requests.get('https://comtradeapi.un.org/public/v1/preview/C/M/HS',params=dict(reporterCode=417,period=p,cmdCode=codes,flowCode=flow,includeDesc='true'),timeout=60)
            if r.status_code==200:
                open(f,'w',encoding='utf-8').write(r.text); break
            time.sleep(5+attempt*3)
        else:
            print('FAILED',flow,p,r.status_code,flush=True)
        time.sleep(2.5)
    print('done',flow,flush=True)
