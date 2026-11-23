# World-level monthly fuel imports for a landlocked panel, one call per month (keyless preview)
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json, time, sys, os, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
R = '51,31,68,72,854,108,398,417,418,454,498,496,807,600,646,860,894,716,203,348,442,688,703,757'
for y in range(2015, 2027):
    for m in range(1, 13):
        p = y * 100 + m
        if p > 202608:
            break
        f = f'{out}/{p}.json'
        if os.path.exists(f):
            continue
        ok = False
        for a in range(8):
            try:
                r = requests.get('https://comtradeapi.un.org/public/v1/preview/C/M/HS', params=dict(reporterCode=R, period=p, cmdCode='271011,271012,271019', flowCode='M', partnerCode=0, partner2Code=0, motCode=0, customsCode='C00'), timeout=90)
                if r.status_code == 200:
                    open(f, 'w', encoding='utf-8').write(r.text); ok = True
                    break
                print('status', p, r.status_code, r.text[:90], flush=True)
                if r.status_code == 403:
                    time.sleep(300)
            except Exception as e:
                print('retry', p, type(e).__name__, flush=True)
            time.sleep(5 + a * 3)
        if not ok:
            print('FAILED', p, flush=True)
        time.sleep(2.5)
print('panel done', len(os.listdir(out)), flush=True)
