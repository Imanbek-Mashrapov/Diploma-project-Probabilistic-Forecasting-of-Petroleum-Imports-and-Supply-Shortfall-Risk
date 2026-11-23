# Pilot rolling-origin backtest: naive baselines vs LightGBM vs small global neural nets
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json, glob, sys, os, warnings
import numpy as np, pandas as pd, lightgbm as lgb, torch, torch.nn as nn
warnings.filterwarnings('ignore'); sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.width', 220, 'display.max_columns', 40, 'display.max_rows', 300)
torch.set_num_threads(6); torch.manual_seed(0); np.random.seed(0)

MAP = {'271011': 'gasoline', '271012': 'gasoline', '271019': 'middle_heavy'}
NAME = {v['code']: k for k, v in json.load(open('dl_comtrade/panel_avail.json')).items()}
rows = []
for f in sorted(glob.glob('dl_comtrade/panel/*.json')):
    for r in (json.load(open(f, encoding='utf-8')).get('data') or []):
        rows.append((r['reporterCode'], NAME[r['reporterCode']], r['period'], MAP[r['cmdCode']], r['netWgt'], r['primaryValue']))
df = pd.DataFrame(rows, columns=['rc', 'country', 'period', 'prod', 'kg', 'usd'])
print('raw', df.shape, df.country.nunique())
df['kg'] = pd.to_numeric(df.kg); df = df[df.kg.notna()]
g = df.groupby(['country', 'prod', 'period'], as_index=False)[['kg', 'usd']].sum()
g['t'] = pd.to_datetime(g.period.astype(str), format='%Y%m')
idx = pd.date_range('2015-01-01', '2026-08-01', freq='MS'); N = len(idx)
Y = {k: d.set_index('t').kg.reindex(idx) / 1000.0 for k, d in g.groupby(['country', 'prod'])}
kl = pd.read_csv('kg_long.csv', dtype={'cmd': str}); kl = kl[(kl.flow == 'M') & (kl.partner != 'World') & kl.cmd.isin(MAP)]
kl['prod'] = kl.cmd.map(MAP); kl['t'] = pd.to_datetime(kl.period.astype(str), format='%Y%m')
for p, x in kl.groupby('prod'):
    Y[('Kyrgyzstan', p)] = (x.groupby('t').kg.sum() / 1000.0).reindex(idx)
zero_months = {str(k): int((v == 0).sum()) for k, v in Y.items() if (v == 0).any()}
print('zero months set to missing', zero_months)
Y = {k: v.where(v > 0) for k, v in Y.items()}

tab = pd.DataFrame({k: v.notna().sum() for k, v in Y.items()}, index=['obs']).T
tab['last'] = [v.last_valid_index() for v in Y.values()]
tab['zero'] = [(v == 0).sum() for v in Y.values()]
tab['mean_t'] = [v.mean() for v in Y.values()]
print(tab.sort_values('obs', ascending=False).to_string())
tab.to_csv('panel_cov.csv')

keep = [k for k, v in Y.items() if v.notna().sum() >= 84 and (v.dropna() > 0).mean() > 0.9]
print('kept series', len(keep), 'countries', len({k[0] for k in keep}), 'obs', sum(Y[k].notna().sum() for k in keep))
L = np.log1p(pd.DataFrame({k: Y[k] for k in keep}))  # log tonnes
G_ = {'Central Asia and Caucasus': ['Kyrgyzstan', 'Kazakhstan', 'Uzbekistan', 'Armenia', 'Azerbaijan', 'Mongolia'],
      'Eastern Europe and Balkans': ['Moldova', 'Rep. of Moldova', 'North Macedonia', 'Serbia'],
      'Central Europe': ['Czechia', 'Hungary', 'Luxembourg', 'Slovakia', 'Switzerland'],
      'Africa': ['Botswana', 'Burkina Faso', 'Burundi', 'Malawi', 'Rwanda', 'Zambia', 'Zimbabwe'],
      'South America and Asia': ['Bolivia', 'Bolivia (Plurinational State of)', 'Paraguay', 'Lao People\'s Dem. Rep.', 'Lao PDR']}
kc = sorted({k[0] for k in keep})
groups = [[g, ', '.join(c for c in kc if c in m)] for g, m in G_.items() if any(c in m for c in kc)]
other = [c for c in kc if not any(c in m for m in G_.values())]
if other: groups.append(['Other', ', '.join(other)])
json.dump(dict(series=len(keep), countries=len(kc), obs=int(sum(Y[k].notna().sum() for k in keep)), groups=groups), open('pilot_meta.json', 'w', encoding='utf-8'), ensure_ascii=False)
H = (1, 3, 'c3'); LB = 12
br = pd.read_excel('dl_misc/brent_eia.xls', sheet_name=1, header=2); br.columns = ['d', 'p']; br['d'] = pd.to_datetime(br.d)
brent = np.log(br.set_index('d').p.resample('MS').mean()).reindex(idx)
gp = pd.read_excel('dl_misc/gpr.xls'); gp['month'] = pd.to_datetime(gp.month); gp = gp.set_index('month')
gpr = np.log(gp['GPR'].astype(float)).reindex(idx); gpru = np.log(gp['GPRC_RUS'].astype(float).clip(lower=.01)).reindex(idx)
test_start = pd.Timestamp('2024-09-01')
sid = {k: i for i, k in enumerate(keep)}


def feats(s, i, h):
    v = s.values; tgt = i + (3 if h == 'c3' else h)
    if i - LB + 1 < 0 or tgt >= N:
        return None
    w = v[i - LB + 1:i + 1]
    if np.isnan(w).mean() > 0.34:
        return None
    d = dict(zip([f'l{j}' for j in range(LB)], w[::-1]))
    d['sl'] = v[tgt - 12] if tgt - 12 >= 0 else np.nan
    d['brent'] = brent.values[i]; d['brent3'] = brent.values[i] - brent.values[max(i - 3, 0)]; d['gpr'] = gpr.values[i]; d['gpru'] = gpru.values[i]
    d['r3'] = np.nanmean(w[-3:]); d['r6'] = np.nanmean(w[-6:]); d['r12'] = np.nanmean(w); d['sd'] = np.nanstd(w)
    m = idx[tgt].month
    d['ms'] = np.sin(2 * np.pi * m / 12); d['mc'] = np.cos(2 * np.pi * m / 12); d['m'] = m
    return d


def table(h):
    R = []
    for k in keep:
        s = L[k]
        for i in range(N):
            f = feats(s, i, h)
            if f is None:
                continue
            step = 3 if h == 'c3' else h
            yy = s.values[i + step]
            if h == 'c3':
                yy = np.log1p(np.expm1(s.values[i + 1:i + 4]).sum()) if not np.isnan(s.values[i + 1:i + 4]).any() else np.nan
                ll = s.values[i - 11:i - 8] if i >= 11 else np.array([np.nan])  # same three months one year earlier
                f['sl'] = np.log1p(np.expm1(ll).sum()) if not np.isnan(ll).any() else np.nan
                f['cum_last'] = np.log1p(np.nansum(np.expm1(s.values[i - 2:i + 1])))
                f['cum_mean'] = np.log1p(3 * np.nanmean(np.expm1(s.values[i - 11:i + 1])))
            f.update(key=k, sid=sid[k], prod=int(k[1] == 'gasoline'), i=i, tgt=i + step, date=idx[i + step], y=yy)
            R.append(f)
    return pd.DataFrame(R)


FE = [f'l{j}' for j in range(LB)] + ['sl', 'r3', 'r6', 'r12', 'sd', 'ms', 'mc', 'm', 'sid', 'prod']
FX = FE + ['brent', 'brent3', 'gpr', 'gpru']


class G(nn.Module):
    def __init__(s, n):
        super().__init__()
        s.e = nn.Embedding(n, 8); s.g = nn.GRU(3, 32, batch_first=True); s.d = nn.Dropout(.2); s.o = nn.Linear(32 + 8 + 2, 1)

    def forward(s, x, i, c):
        _, h = s.g(x)
        return s.o(torch.cat([s.d(h[-1]), s.e(i), c], 1)).squeeze(1)


class M(nn.Module):
    def __init__(s, n, dim):
        super().__init__()
        s.e = nn.Embedding(n, 8)
        s.n = nn.Sequential(nn.Linear(dim + 8, 64), nn.ReLU(), nn.Dropout(.2), nn.Linear(64, 1))

    def forward(s, x, i):
        return s.n(torch.cat([x, s.e(i)], 1)).squeeze(1)


def seqs(T, off=0.0):
    W = T[[f'l{j}' for j in range(LB)]].values[:, ::-1].astype(float).copy()
    mu = np.nanmean(W, 1, keepdims=True); sd = np.maximum(np.nanstd(W, 1, keepdims=True), .1)
    Z = np.nan_to_num((W - mu) / sd)
    mon = ((T.date.dt.month.values - 1)[:, None] - np.arange(LB - 1, -1, -1)[None, :]) % 12
    S = np.stack([Z, np.sin(2 * np.pi * mon / 12), np.cos(2 * np.pi * mon / 12)], 2)
    sl = np.nan_to_num((T.sl.values.astype(float) - off - mu[:, 0]) / sd[:, 0])
    C = np.stack([sl, T['prod'].values], 1)
    return S.astype('f4'), C.astype('f4'), mu[:, 0], sd[:, 0]


def fit_nn(tr, te, kind, seed, off=0.0):
    torch.manual_seed(seed); np.random.seed(seed)
    S, C, mu, sd = seqs(tr, off); St, Ct, mut, sdt = seqs(te, off)
    y = ((tr.y.values - off - mu) / sd).astype('f4'); ok = ~np.isnan(y)
    S, C, y, ids = S[ok], C[ok], y[ok], tr.sid.values[ok]
    Xf = np.concatenate([S[:, :, 0], C], 1); Xt = np.concatenate([St[:, :, 0], Ct], 1)
    net = G(len(keep)) if kind == 'gru' else M(len(keep), Xf.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-3)
    n = len(y); bs = 128
    for ep in range(40):
        net.train(); p = np.random.permutation(n)
        for b in range(0, n, bs):
            j = p[b:b + bs]; opt.zero_grad()
            pr = net(torch.tensor(S[j]), torch.tensor(ids[j]), torch.tensor(C[j])) if kind == 'gru' else net(torch.tensor(Xf[j]), torch.tensor(ids[j]))
            nn.functional.l1_loss(pr, torch.tensor(y[j])).backward(); opt.step()
    net.eval()
    with torch.no_grad():
        ii = torch.tensor(te.sid.values)
        pr = net(torch.tensor(St), ii, torch.tensor(Ct)) if kind == 'gru' else net(torch.tensor(Xt), ii)
    return pr.numpy() * sdt + mut + off


out = []
for h in H:
    T = table(h); print('h', h, 'rows', len(T), flush=True)
    dates = sorted(d for d in T.date.unique() if d >= test_start)
    P = T[T.date >= test_start].copy()
    for c in ['naive', 'snaive', 'mean12', 'lgb', 'lgbx', 'lgb_local', 'lgb_q10', 'lgb_q90', 'gru', 'mlp']:
        P[c] = np.nan
    P['naive'] = P.cum_last if h == 'c3' else P.l0; P['snaive'] = P.sl; P['mean12'] = P.cum_mean if h == 'c3' else P.r12
    step = 3 if h == 'c3' else h
    for dt in dates:
        cut = pd.Timestamp(dt)
        tr = T[(T.date <= cut - pd.DateOffset(months=step)) & T.y.notna()]  # targets known at the forecast origin
        te = T[T.date == dt]
        mx = lgb.LGBMRegressor(objective='l1', n_estimators=250, learning_rate=.03, num_leaves=15, min_child_samples=20, subsample=.8, subsample_freq=1, colsample_bytree=.8, verbose=-1)
        mx.fit(tr[FX], tr.y, categorical_feature=['sid']); P.loc[te.index, 'lgbx'] = mx.predict(te[FX])
        for kk in [('Kyrgyzstan', 'gasoline'), ('Kyrgyzstan', 'middle_heavy')]:
            a, b = tr[tr.sid == sid[kk]], te[te.sid == sid[kk]]
            if len(b):
                ml = lgb.LGBMRegressor(objective='l1', n_estimators=150, learning_rate=.05, num_leaves=7, min_child_samples=5, verbose=-1)
                cols = [c for c in FE if c not in ('sid', 'prod')]
                ml.fit(a[cols], a.y); P.loc[b.index, 'lgb_local'] = ml.predict(b[cols])
        for name, par in [('lgb', dict(objective='l1')), ('lgb_q10', dict(objective='quantile', alpha=.1)), ('lgb_q90', dict(objective='quantile', alpha=.9))]:
            m = lgb.LGBMRegressor(n_estimators=250, learning_rate=.03, num_leaves=15, min_child_samples=20, subsample=.8, subsample_freq=1, colsample_bytree=.8, verbose=-1, **par)
            m.fit(tr[FE], tr.y, categorical_feature=['sid']); P.loc[te.index, name] = m.predict(te[FE])
    for b in range(0, len(dates), 6):  # neural refit every six origins
        seg = dates[b:b + 6]; cut = pd.Timestamp(seg[0])
        tr = T[(T.date <= cut - pd.DateOffset(months=step)) & T.y.notna()]; te = T[T.date.isin(seg)]
        for kind in ['gru', 'mlp']:
            P.loc[te.index, kind] = np.mean([fit_nn(tr, te, kind, s, np.log(3) if h == 'c3' else 0.0) for s in range(3)], 0)
        print(' nn refit', seg[0], len(tr), flush=True)
    P['h'] = str(h); out.append(P)

P = pd.concat(out); P = P[P.y.notna()]; H = ('1', '3', 'c3')
P.to_pickle('pilot_pred.pkl')
MODELS = ['naive', 'snaive', 'mean12', 'lgb', 'lgbx', 'lgb_local', 'gru', 'mlp']
lev = lambda a: np.expm1(np.maximum(a, 0))
scale = {k: np.nanmean(np.abs(np.expm1(L[k])[idx < test_start].diff(12))) for k in keep}
scale3 = {k: np.nanmean(np.abs(np.expm1(L[k])[idx < test_start].rolling(3).sum().diff(12))) for k in keep}


def score(d):
    r = {}
    sc = scale3 if (len(d) and d.h.iloc[0] == 'c3') else scale
    for m in MODELS:
        x = d[d[m].notna()]
        if not len(x):
            r[m + '_wape'] = r[m + '_mase'] = np.nan
            continue
        e = np.abs(lev(x[m].values.astype(float)) - lev(x.y.values.astype(float)))
        r[m + '_wape'] = e.sum() / lev(x.y.values.astype(float)).sum() * 100
        r[m + '_mase'] = np.mean(e / np.array([sc[k] for k in x.key]))
    return pd.Series(r)


rep = []
for h in H:
    d = P[P.h == h]
    for name, sel in [('KG gasoline', d.key == ('Kyrgyzstan', 'gasoline')), ('KG middle/heavy', d.key == ('Kyrgyzstan', 'middle_heavy')), ('All series', d.y.notna())]:
        s = score(d[sel]); s['group'] = name; s['h'] = h; s['n'] = int(sel.sum()); rep.append(s)
R = pd.DataFrame(rep).set_index(['h', 'group', 'n']).round(2)
print(R[[c for c in R if 'wape' in c]].to_string()); print(R[[c for c in R if 'mase' in c]].to_string()); R.to_csv('pilot_scores.csv')

byser = []
for h in H:
    d = P[P.h == h]
    for k, x in d.groupby('key'):
        s = score(x); s['h'] = h; s['key'] = str(k); byser.append(s)
B = pd.DataFrame(byser)
print(B.groupby('h')[[m + '_mase' for m in MODELS]].median().round(3).to_string()); B.to_csv('pilot_byseries.csv', index=False)
for h in H:
    a = P[P.h == h]; kg = a[a.key.isin([('Kyrgyzstan', 'gasoline'), ('Kyrgyzstan', 'middle_heavy')])]
    print('h', h, 'KG 80% interval coverage', round(((kg.y >= kg.lgb_q10) & (kg.y <= kg.lgb_q90)).mean(), 3), len(kg),
          'panel', round(((a.y >= a.lgb_q10) & (a.y <= a.lgb_q90)).mean(), 3), len(a))
