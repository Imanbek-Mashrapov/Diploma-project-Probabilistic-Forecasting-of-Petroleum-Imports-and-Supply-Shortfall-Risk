# Kyrgyz series audit: reconciliation with the energy balance, supplier structure, 2026 episode, shortfall events
import site; site.addsitedir("C:/Users/User/AppData/Roaming/Python/Python311/site-packages")
import json, sys
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.width', 230, 'display.max_columns', 40, 'display.max_rows', 300)

d = pd.read_csv('kg_long.csv', dtype={'cmd': str})
M = d[d.flow == 'M'].copy()
M['year'] = M.period // 100
W = M[M.partner == 'World'].copy()
GAS, MID = ['271011', '271012'], ['271019']
LPG = ['271112', '271113', '271119']


def series(c):
    s = W[W.cmd.isin(c)].groupby('period')[['kg', 'usd']].sum()
    s.index = pd.to_datetime(s.index.astype(str), format='%Y%m')
    return s


g, m, l = series(GAS), series(MID), series(LPG)
teb_gas = {2015: 625.3, 2016: 532.9, 2017: 468.5, 2018: 632.2, 2019: 485.3, 2020: 550.7, 2021: 618.6, 2022: 578.4, 2023: 494.1, 2024: 522.1}
teb_dsl = {2015: 514.9, 2016: 347.4, 2017: 541.3, 2018: 706.1, 2019: 535.3, 2020: 533.0, 2021: 536.3, 2022: 490.6, 2023: 417.0, 2024: 646.1}
months = W[W.cmd == '2710'].groupby('year').period.nunique()
rec = pd.DataFrame({'months': months, 'gas_ct': g.kg.groupby(g.index.year).sum() / 1e6, 'gas_teb': pd.Series(teb_gas),
                    'mid_ct': m.kg.groupby(m.index.year).sum() / 1e6, 'dsl_teb': pd.Series(teb_dsl)})
rec['gas_ratio'] = rec.gas_ct / rec.gas_teb; rec['mid_ratio'] = rec.mid_ct / rec.dsl_teb
print(rec.round(2).to_string())
full = rec.loc[[y for y in teb_gas if rec.months.get(y, 0) == 12]]
print('full years', list(full.index))
print('gas MAPE', (abs(full.gas_ct - full.gas_teb) / full.gas_teb).mean().round(3), 'median ratio', full.gas_ratio.median().round(3), 'corr', full.gas_ct.corr(full.gas_teb).round(3))
print('mid median ratio', full.mid_ratio.median().round(3), 'corr', full.mid_ct.corr(full.dsl_teb).round(3))
print('ge2018 gas MAPE', (abs(full.gas_ct - full.gas_teb) / full.gas_teb)[full.index >= 2018].mean().round(3))

idx = pd.date_range('2015-01-01', '2026-08-01', freq='MS')
ml = pd.DataFrame({'gas_t': g.kg.reindex(idx) / 1000, 'mid_t': m.kg.reindex(idx) / 1000, 'lpg_t': l.kg.reindex(idx) / 1000,
                   'gas_usd': g.usd.reindex(idx), 'mid_usd': m.usd.reindex(idx)})
print('missing months since 2015', [str(x)[:7] for x in idx[ml.gas_t.isna()]])
print(ml.tail(16).round(0).to_string())
print('describe\n', ml[['gas_t', 'mid_t', 'lpg_t']].describe().round(0).to_string())
print('CV', (ml[['gas_t', 'mid_t']].std() / ml[['gas_t', 'mid_t']].mean()).round(2).to_dict())
ml.to_csv('kg_monthly.csv')

# supplier structure
P = M[(M.partner != 'World') & M.period.ge(201501)].copy()
P['prod'] = np.where(P.cmd.isin(GAS), 'gas', np.where(P.cmd.isin(MID), 'mid', 'x'))
P = P[P['prod'] != 'x']


def hhi(x):
    s = x / x.sum()
    return (s ** 2).sum()


A = P.groupby(['prod', 'year', 'partner']).kg.sum().reset_index()
out = []
for (pr, y), x in A.groupby(['prod', 'year']):
    t = x.kg.sum(); top = x.sort_values('kg', ascending=False).head(3)
    out.append(dict(prod=pr, year=y, kt=t / 1e6, hhi=hhi(x.kg), ru=x[x.partner == 'Russian Federation'].kg.sum() / t,
                    kz=x[x.partner == 'Kazakhstan'].kg.sum() / t, top=', '.join(f'{a} {b / t:.0%}' for a, b in zip(top.partner, top.kg))))
S = pd.DataFrame(out); print(S.round(3).to_string()); S.to_csv('kg_suppliers.csv', index=False)
Mo = P.groupby(['prod', 'period']).apply(lambda x: pd.Series({'kt': x.kg.sum() / 1e6, 'hhi': hhi(x.kg), 'ru': x[x.partner == 'Russian Federation'].kg.sum() / x.kg.sum()})).reset_index()
print(Mo[Mo.period >= 202510].round(3).to_string())
Mo.to_csv('kg_suppliers_monthly.csv', index=False)
print('partners last 6 months', P[P.period >= 202601].groupby(['prod', 'partner']).kg.sum().div(1e6).round(1).sort_values(ascending=False).head(14).to_string())
print('partners count per month median', P.groupby(['prod', 'period']).partner.nunique().groupby('prod').median().to_dict())

# shortfall definition: quantity below 70% of the same calendar-month mean of the prior three years, plus unit-value z>0
ev = []
for name, q, v in [('gas', ml.gas_t, ml.gas_usd), ('mid', ml.mid_t, ml.mid_usd)]:
    uv = v / (q * 1000)
    base = pd.concat([q.shift(12), q.shift(24), q.shift(36)], axis=1).mean(axis=1, skipna=True)
    ratio = q / base
    z = (uv - uv.rolling(12, min_periods=6).mean().shift(1)) / uv.rolling(12, min_periods=6).std().shift(1)
    e = pd.DataFrame({'q': q, 'base': base, 'ratio': ratio, 'uvz': z})
    e['S'] = e.ratio < .7; e['SP'] = e.S & (e.uvz > 0)
    print(name, 'evaluable', e.ratio.notna().sum(), 'shortfall', int(e.S.sum()), 'with price rise', int(e.SP.sum()))
    print(e[e.S].round(2).to_string())


# persistent shortfall: trailing three-month volume against the same three months of the prior three years
print('--- persistent definition, partner-sum series')
kl = M[(M.partner != 'World') & M.cmd.isin(GAS + MID)].copy(); kl['t'] = pd.to_datetime(kl.period.astype(str), format='%Y%m')
for name, c in [('gas', GAS), ('mid', MID)]:
    x = kl[kl.cmd.isin(c)].groupby('t')[['kg', 'usd']].sum().reindex(idx); x = x.where(x.kg > 0)
    q = x.kg / 1000; r3 = q.rolling(3).sum()
    base = pd.concat([r3.shift(12), r3.shift(24), r3.shift(36)], axis=1).mean(axis=1)
    uv = (x.usd.rolling(3).sum() / (x.kg.rolling(3).sum())); z = (uv - uv.shift(3).rolling(12, min_periods=6).mean()) / uv.shift(3).rolling(12, min_periods=6).std()
    e = pd.DataFrame({'q3': r3, 'base': base, 'ratio': r3 / base, 'uvz': z})
    for th in (.8, .75, .7):
        s = e.ratio < th
        print(name, 'th', th, 'evaluable', int(e.ratio.notna().sum()), 'months', int(s.sum()), 'episodes', int((s & ~s.shift(1, fill_value=False)).sum()), 'with uv', int((s & (e.uvz > 0)).sum()))
    print(e[e.ratio < .75].round(2).to_string())
    e.to_csv(f'kg_shortfall_{name}.csv')
