"""Exploratory analysis. Descriptive only: nothing here is fitted for prediction.

STL and change-point detection are applied to gap-free stretches or to observed points only, so
no target value is interpolated. Correlations use year-on-year log changes, which removes
seasonality but overlaps in time, so their p-values are optimistic.
"""
import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.seasonal import STL

from src.utils.config import REPORTS

log = logging.getLogger(__name__)
OUT = REPORTS / "phase2"
FIG = OUT / "figures"
TABLES = OUT / "tables"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, SURFACE, BAND = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#ecebe6"
SEQ = LinearSegmentedColormap.from_list("seq", ["#eef4fb", "#9cc3ef", "#2a78d6", "#123f75"])
DIV = LinearSegmentedColormap.from_list("div", ["#eb6834", "#f6c9b4", "#efeeea", "#a9cbf0", "#2a78d6"])
PRODUCT_NAMES = {"gasoline": "Gasoline proxy", "middle_heavy": "Distillates (HS 271019)", "middle_incl_blends": "Distillates with blends"}
FUELS = ["gasoline", "middle_incl_blends"]


def style():
    plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "font.size": 10, "text.color": INK, "axes.labelcolor": MUTED,
                         "axes.edgecolor": GRID, "axes.titlesize": 11, "axes.titlelocation": "left", "axes.grid": True, "grid.color": GRID, "grid.linewidth": .7, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "legend.frameon": False, "font.family": "DejaVu Sans"})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=150)
    plt.close(fig)


def series(monthly, iso3, product):
    s = monthly[(monthly.iso3 == iso3) & (monthly.product_group == product)].set_index("month").sort_index()
    return s.import_mass_t, s


def kyrgyz_monthly(monthly):
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for ax, product, color in zip(axes, ["gasoline", "middle_heavy"], [BLUE, ORANGE]):
        mass, s = series(monthly, "KGZ", product)
        ax.plot(mass.index, mass / 1000, color=color, lw=2, solid_capstyle="round")
        rejected = s[s.data_status == "mass_rejected_by_check"]
        for month in s[s.data_status.isin(["reporting_interruption", "mass_rejected_by_check"])].index:
            ax.axvspan(month - pd.Timedelta(days=15), month + pd.Timedelta(days=15), color=BAND, lw=0)
        ax.axvspan(pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-31"), color="#f9e0d4", lw=0)
        ax.set_title(PRODUCT_NAMES[product] + ", imports in thousand tonnes")
        ax.set_ylim(bottom=0)
        ax.grid(axis="x", visible=False)
        if len(rejected):
            log.info("%s rejected: %s", product, [str(d)[:7] for d in rejected.index])
    axes[0].set_ylim(0, 108)
    axes[0].annotate("Orange band: Russian gasoline export ban, Oct-Dec 2025", (pd.Timestamp("2025-09-01"), 99), ha="right", color=MUTED, fontsize=8.5)
    axes[0].annotate("Grey bands: month missing or mass rejected", (pd.Timestamp("2015-01-01"), 99), color=MUTED, fontsize=8.5)
    save(fig, "fig01_kyrgyz_monthly_imports")


def annual_trends(monthly):
    rows = []
    for product in ["gasoline", "middle_heavy", "lpg"]:
        mass, s = series(monthly, "KGZ", product)
        y = s.assign(year=s.index.year).groupby("year").agg(kt=("import_mass_t", lambda v: v.sum() / 1000), months=("import_mass_t", "count"), usd_m=("import_value_usd", lambda v: v.sum() / 1e6))
        y["product_group"] = product
        y["kt_per_observed_month"] = y.kt / y.months
        y["yoy_pct_full_years"] = (y.kt.where(y.months == 12).pct_change(fill_method=None) * 100).where(y.months.shift(1) == 12)
        rows.append(y.reset_index())
    t = pd.concat(rows)
    t.to_csv(TABLES / "kyrgyz_annual_trends.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, product, color in zip(axes, ["gasoline", "middle_heavy"], [BLUE, ORANGE]):
        d = t[t.product_group == product]
        full = d[d.months == 12]
        ax.bar(full.year, full.kt, color=color, width=.65)
        partial = d[d.months < 12]
        ax.bar(partial.year, partial.kt, color=color, alpha=.35, width=.65)
        ax.set_title(PRODUCT_NAMES[product] + ", thousand tonnes")
        ax.grid(axis="x", visible=False)
    axes[0].annotate("Pale bars: fewer than 12 usable months", (2015, 1010), color=MUTED, fontsize=8.5)
    axes[0].set_ylim(0, 1100)
    save(fig, "fig02_kyrgyz_annual_imports")
    return t


def seasonality(monthly, cov):
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, product, color in zip(axes, ["gasoline", "middle_heavy"], [BLUE, ORANGE]):
        mass, s = series(monthly, "KGZ", product)
        m = mass.dropna()
        index = m / m.groupby(m.index.year).transform("mean")
        full = index[m.groupby(m.index.year).transform("size") >= 10]
        groups = [full[full.index.month == k].values for k in range(1, 13)]
        h, p = stats.kruskal(*groups)
        rows.append({"series": f"KGZ {product}", "kruskal_h": h, "p": p, **{f"m{k:02d}": float(np.median(groups[k - 1])) for k in range(1, 13)}})
        box = ax.boxplot(groups, patch_artist=True, widths=.55, medianprops={"color": INK, "lw": 1.6}, whiskerprops={"color": MUTED}, capprops={"color": MUTED}, flierprops={"marker": "o", "ms": 3, "mfc": MUTED, "mec": MUTED})
        for patch in box["boxes"]:
            patch.set(facecolor=color, alpha=.45, edgecolor=color)
        ax.axhline(1, color=MUTED, lw=1)
        ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
        ax.set_title(f"{PRODUCT_NAMES[product]}: Kruskal-Wallis p {'< 0.001' if p < .001 else f'= {p:.2f}'}")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Month relative to its year's mean")
    save(fig, "fig03_kyrgyz_seasonality")
    return pd.DataFrame(rows)


def longest_run(mass):
    """Longest gap-free stretch; STL cannot take missing values and targets are not interpolated."""
    obs = mass.notna()
    groups = (obs != obs.shift()).cumsum()
    runs = mass[obs].groupby(groups[obs])
    return max(runs, key=lambda kv: len(kv[1]))[1] if obs.any() else mass.iloc[0:0]


def stl_strengths(monthly, cov):
    rows = []
    usable = cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)]
    for r in usable.itertuples():
        run = longest_run(series(monthly, r.iso3, r.product_group)[0])
        if len(run) < 36:
            rows.append({"iso3": r.iso3, "product_group": r.product_group, "run_months": len(run), "seasonal_strength": np.nan, "trend_strength": np.nan})
            continue
        fit = STL(np.log(run.asfreq("MS")), period=12, robust=True).fit()
        rows.append({"iso3": r.iso3, "product_group": r.product_group, "run_months": len(run), "run_start": run.index[0].strftime("%Y-%m"),
                     "seasonal_strength": max(0.0, 1 - fit.resid.var() / (fit.seasonal + fit.resid).var()), "trend_strength": max(0.0, 1 - fit.resid.var() / (fit.trend + fit.resid).var())})
    return pd.DataFrame(rows)


def stl_kyrgyz(monthly):
    run = longest_run(series(monthly, "KGZ", "gasoline")[0]).asfreq("MS")
    fit = STL(np.log(run), period=12, robust=True).fit()
    fig, axes = plt.subplots(4, 1, figsize=(10, 6.5), sharex=True)
    for ax, values, title in zip(axes, [np.log(run), fit.trend, fit.seasonal, fit.resid], ["Observed log mass", "Trend", "Seasonal", "Remainder"]):
        ax.plot(values.index, values, color=BLUE, lw=1.8)
        ax.set_title(title, fontsize=9.5)
        ax.grid(axis="x", visible=False)
    fig.suptitle(f"Kyrgyz gasoline STL, longest gap-free stretch ({run.index[0]:%b %Y} to {run.index[-1]:%b %Y})", x=.01, ha="left", fontsize=11)
    save(fig, "fig04_kyrgyz_gasoline_stl")
    return run


def breaks(mass):
    """PELT with an L2 cost on observed log mass. Penalty 3 log(n) sigma^2 with a robust sigma."""
    m = np.log(mass.dropna())
    if len(m) < 36:
        return [], m
    sigma = 1.4826 * np.median(np.abs(np.diff(m) - np.median(np.diff(m)))) / np.sqrt(2)
    points = rpt.Pelt(model="l2", min_size=6, jump=1).fit(m.values).predict(pen=3 * np.log(len(m)) * sigma ** 2)
    return [m.index[i] for i in points[:-1]], m


def structural_breaks(monthly, cov):
    rows = []
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.4), sharex=True)
    for ax, product, color in zip(axes, ["gasoline", "middle_heavy"], [BLUE, ORANGE]):
        points, m = breaks(series(monthly, "KGZ", product)[0])
        ax.plot(m.index, m, color=color, lw=1.2, alpha=.5)
        edges = [m.index[0], *points, m.index[-1] + pd.Timedelta(days=31)]
        for a, b in zip(edges[:-1], edges[1:]):
            part = m[(m.index >= a) & (m.index < b)]
            ax.hlines(part.mean(), a, b, color=color, lw=2.4)
            rows.append({"iso3": "KGZ", "product_group": product, "start": a.strftime("%Y-%m"), "months": len(part), "mean_kt": float(np.exp(part.mean()) / 1000)})
        for i, p in enumerate(points):
            ax.axvline(p, color=MUTED, lw=1, ls="--")
            ax.annotate(p.strftime("%b %Y"), (p, m.min()), xytext=(3, 12 * (i % 2)), textcoords="offset points", fontsize=8, color=MUTED)
        ax.set_title(PRODUCT_NAMES[product] + ", log tonnes with detected level shifts")
        ax.grid(axis="x", visible=False)
    save(fig, "fig05_kyrgyz_structural_breaks")
    pooled = []
    for r in cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)].itertuples():
        points, _ = breaks(series(monthly, r.iso3, r.product_group)[0])
        pooled += [{"iso3": r.iso3, "product_group": r.product_group, "break_month": p.strftime("%Y-%m"), "year": p.year} for p in points]
    return pd.DataFrame(rows), pd.DataFrame(pooled)


def scale_comparison(monthly, cov, annual):
    pop = annual.sort_values("year").groupby("iso3").population.last()
    gdp = annual.sort_values("year").groupby("iso3").gdp_per_capita_usd.last()
    usable = cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)]
    rows = []
    for r in usable.itertuples():
        mass = series(monthly, r.iso3, r.product_group)[0].dropna()
        recent = mass[mass.index >= mass.index[-1] - pd.DateOffset(months=35)]
        change = np.log(mass).diff().where(mass.index.to_series().diff().dt.days.between(27, 32))
        rows.append({"iso3": r.iso3, "product_group": r.product_group, "tier": r.quality_tier, "median_kg_per_person_month": recent.median() * 1000 / pop.get(r.iso3, np.nan),
                     "cv_detrended": (mass / mass.rolling(13, center=True, min_periods=7).mean()).std(), "sd_dlog": change.std(),
                     "robust_sd_dlog": 1.4826 * (change - change.median()).abs().median(), "acf1_log": np.log(mass).autocorr(1), "acf12_log": np.log(mass).autocorr(12), "gdp_per_capita_usd": gdp.get(r.iso3, np.nan)})
    t = pd.DataFrame(rows)
    t.to_csv(TABLES / "country_scale_and_volatility.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 6.2), sharey=False)
    d = t[t.product_group == "gasoline"].sort_values("median_kg_per_person_month")
    for ax, col, title in zip(axes, ["median_kg_per_person_month", "robust_sd_dlog"], ["Gasoline imports, kg per person per month", "Volatility: robust sd of monthly log change"]):
        d = t[t.product_group == "gasoline"].sort_values(col)
        colors = [ORANGE if i == "KGZ" else BLUE for i in d.iso3]
        ax.hlines(d.iso3, 0, d[col], color=GRID, lw=1.5)
        ax.scatter(d[col], d.iso3, color=colors, s=46, zorder=3, edgecolor=SURFACE, linewidth=1)
        ax.set_title(title)
        ax.grid(False)
        ax.set_xlim(left=0)
    save(fig, "fig06_country_scale_and_volatility")
    return t


def concentration_views(monthly, conc, cov):
    usable = cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)][["iso3", "product_group", "quality_tier"]]
    c = conc.merge(usable, on=["iso3", "product_group"])
    t = c.groupby(["iso3", "product_group", "quality_tier"], as_index=False).agg(hhi_median=("hhi", "median"), hhi_12m_median=("hhi_12m", "median"), largest_share=("largest_supplier_share", "median"), top3_share=("top3_supplier_share", "median"),
                                                                                   suppliers=("active_suppliers", "median"), russia_share=("russia_share", "median"), top=("largest_supplier_iso", lambda s: s.value_counts().index[0]), months=("period", "size"), hhi_sd=("hhi", "std"))
    t.to_csv(TABLES / "supplier_concentration_summary.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 6.2))
    for ax, product in zip(axes, FUELS):
        d = t[t.product_group == product].sort_values("hhi_12m_median")
        colors = [ORANGE if i == "KGZ" else BLUE for i in d.iso3]
        ax.hlines(d.iso3, 0, d.hhi_12m_median, color=GRID, lw=1.5)
        ax.scatter(d.hhi_12m_median, d.iso3, color=colors, s=46, zorder=3, edgecolor=SURFACE, linewidth=1)
        ax.axvline(.25, color=MUTED, lw=1, ls="--")
        ax.set_xlim(0, 1)
        ax.grid(False)
        ax.set_title(f"{PRODUCT_NAMES[product]}: median 12-month HHI")
    save(fig, "fig07_supplier_concentration_by_country")
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.4), sharex=True, sharey=True)
    for ax, product in zip(axes, ["gasoline", "middle_heavy"]):
        k = conc[(conc.iso3 == "KGZ") & (conc.product_group == product) & (conc.period >= 201501)].set_index("month")
        ax.plot(k.index, k.russia_share, color=ORANGE, lw=1.2, alpha=.55, label="Russia's monthly share")
        ax.plot(k.index, k.hhi_12m, color=BLUE, lw=2.2, label="HHI, trailing 12 months")
        ax.set_ylim(0, 1.04)
        ax.grid(axis="x", visible=False)
        ax.set_title(PRODUCT_NAMES[product])
    axes[0].legend(loc="lower left", ncol=2)
    save(fig, "fig08_kyrgyz_supplier_concentration")
    return t


def coverage_heatmap(cov, monthly):
    order = cov[cov.product_group == "gasoline"].sort_values(["quality_tier", "observed_months"], ascending=[True, False]).iso3.tolist()
    g = monthly[(monthly.product_group == "gasoline") & monthly.import_mass_t.notna()]
    years = sorted(monthly.period.div(100).astype(int).unique())
    wide = g.assign(year=g.period // 100).pivot_table(index="iso3", columns="year", values="period", aggfunc="count").reindex(index=order, columns=years).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 8.6))
    im = ax.imshow(wide.values, cmap=SEQ, vmin=0, vmax=12, aspect="auto")
    ax.set_xticks(range(len(years)), years)
    ax.set_yticks(range(len(order)), order, fontsize=8)
    tiers = cov[cov.product_group == "gasoline"].set_index("iso3").quality_tier
    for i, code in enumerate(order[:-1]):
        if tiers[code] != tiers[order[i + 1]]:
            ax.axhline(i + .5, color=INK, lw=1.2)
    ax.grid(False)
    ax.set_title("Observed gasoline months per year, grouped by tier (lines separate Tier 1, 2, 3)")
    fig.colorbar(im, ax=ax, shrink=.5, label="Months")
    save(fig, "fig09_coverage_heatmap")


def external_correlations(monthly, external, cov):
    glob = external[external.scope == "global"].pivot_table(index="month", columns="indicator", values="value")
    country = external[external.scope == "country"].pivot_table(index=["iso3", "month"], columns="indicator", values="value")
    yoy = lambda s: np.log(s).diff(12)
    rows = []
    for r in cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)].itertuples():
        mass = series(monthly, r.iso3, r.product_group)[0]
        y = yoy(mass.asfreq("MS"))
        features = {"Brent": yoy(glob.brent_usd_bbl), "Global GPR": yoy(glob.GPR), "Russia GPR": yoy(glob.GPRC_RUS)}
        if r.iso3 in country.index.get_level_values(0):
            own = country.loc[r.iso3].asfreq("MS")
            if "fx_lcu_per_usd_avg" in own and own.fx_lcu_per_usd_avg.notna().sum() > 24:
                features["Exchange rate"] = yoy(own.fx_lcu_per_usd_avg)
            if "cpi_index" in own and own.cpi_index.notna().sum() > 24:
                features["Inflation"] = yoy(own.cpi_index)
        for name, x in features.items():
            for lag in [0, 1, 3, 6]:
                pair = pd.concat([y, x.shift(lag)], axis=1).dropna()
                if len(pair) >= 36:
                    rho, p = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
                    rows.append({"iso3": r.iso3, "product_group": r.product_group, "indicator": name, "lag_months": lag, "n": len(pair), "rho": rho, "p": p})
    t = pd.DataFrame(rows).dropna(subset=["rho", "p"])  # a constant series has no correlation, and NaN would void the correction
    t["p_bh"] = multipletests(t.p, method="fdr_bh")[1]
    t.to_csv(TABLES / "external_correlations.csv", index=False)
    summary = t.groupby(["indicator", "lag_months"]).agg(median_rho=("rho", "median"), series=("rho", "size"), positive=("rho", lambda s: int((s > 0).sum())), significant_bh=("p_bh", lambda s: int((s < .05).sum()))).reset_index()
    summary.to_csv(TABLES / "external_correlation_summary.csv", index=False)
    order = ["Brent", "Global GPR", "Russia GPR", "Exchange rate", "Inflation"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), sharey=True)
    panels = [("Panel median", summary.pivot(index="indicator", columns="lag_months", values="median_rho")),
              ("Kyrgyz gasoline", t[(t.iso3 == "KGZ") & (t.product_group == "gasoline")].pivot(index="indicator", columns="lag_months", values="rho")),
              ("Kyrgyz distillates", t[(t.iso3 == "KGZ") & (t.product_group == "middle_incl_blends")].pivot(index="indicator", columns="lag_months", values="rho"))]
    for ax, (title, wide) in zip(axes, panels):
        wide = wide.reindex(order)
        ax.imshow(wide.values, cmap=DIV, vmin=-.6, vmax=.6, aspect="auto")
        ax.set_xticks(range(wide.shape[1]), [f"{c}m" for c in wide.columns])
        ax.set_yticks(range(len(order)), order)
        ax.set_title(title)
        ax.grid(False)
        for (i, j), v in np.ndenumerate(wide.values):
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.5, color=INK)
    fig.suptitle("Spearman correlation of year-on-year log changes, by indicator lead", x=.01, ha="left", fontsize=11)
    save(fig, "fig10_external_correlations")
    return t, summary


def gdp_correlations(monthly, annual, cov):
    rows = []
    for r in cov[(cov.quality_tier != "Tier 3") & cov.product_group.isin(FUELS)].itertuples():
        mass = series(monthly, r.iso3, r.product_group)[0]
        counts = mass.groupby(mass.index.year).agg(["sum", "count"])
        y = np.log(counts["sum"].where(counts["count"] == 12)).diff()
        g = annual[annual.iso3 == r.iso3].set_index("year").gdp_current_usd
        pair = pd.concat([y, np.log(g).diff()], axis=1).dropna()
        if len(pair) >= 6:
            rho, p = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
            rows.append({"iso3": r.iso3, "product_group": r.product_group, "years": len(pair), "rho": rho, "p": p})
    return pd.DataFrame(rows)


def shortfall_recount(monthly):
    """Re-derive the proposal's descriptive rule on cleaned mass. These remain labels, not validated events."""
    out, episodes = [], []
    for product in ["gasoline", "middle_heavy"]:
        mass, s = series(monthly, "KGZ", product)
        for basis, m in [("clean", mass.asfreq("MS")), ("as_in_proposal", s.import_mass_t_original.asfreq("MS").where(lambda v: v > 0))]:
            q = m.rolling(3, min_periods=3).sum()
            base = pd.concat([q.shift(12), q.shift(24), q.shift(36)], axis=1).mean(axis=1)  # skips missing years, as the proposal did
            ratio = q / base
            flag = ratio < .75
            starts = flag & ~flag.shift(1, fill_value=False)
            out.append({"product_group": product, "mass_basis": basis, "evaluable_months": int(ratio.notna().sum()), "flagged_months": int(flag.sum()), "episodes": int(starts.sum()), "first_months": ", ".join(d.strftime("%Y-%m") for d in flag[starts].index)})
    return pd.DataFrame(out)


def panel_comovement(monthly, cov):
    wide = {}
    for r in cov[(cov.quality_tier != "Tier 3") & (cov.product_group == "gasoline")].itertuples():
        wide[r.iso3] = np.log(series(monthly, r.iso3, "gasoline")[0].asfreq("MS")).diff(12)
    frame = pd.DataFrame(wide)
    corr = frame.corr(min_periods=36, method="spearman")
    pairs = corr.where(np.triu(np.ones(corr.shape, bool), 1)).stack()
    return {"pairs": int(len(pairs)), "median_rho": float(pairs.median()), "kgz_median_rho": float(corr["KGZ"].drop("KGZ").median()), "kgz_top": corr["KGZ"].drop("KGZ").sort_values(ascending=False).head(3).round(2).to_dict()}


def kyrgyz_validation_figures(reconciliation, dependency, mirror, all_goods):
    r = reconciliation[reconciliation.gas_teb_kt.notna()]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    ax = axes[0]
    ax.bar(r.year - .2, r.gas_ct_with_volume_est_kt, .38, color=BLUE, label="Comtrade")
    ax.bar(r.year + .2, r.gas_teb_kt, .38, color=ORANGE, label="Energy balance")
    ax.set_title("Gasoline imports, thousand tonnes")
    ax.legend(loc="upper center", ncol=2)
    ax.set_ylim(0, 800)
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    m = mirror[(mirror.exporter == "RUS") & (mirror.iso3 == "KGZ") & (mirror.product_group == "gasoline")]
    ax.bar(m.year - .2, m.import_kt, .38, color=BLUE, label="Kyrgyz imports from Russia")
    ax.bar(m.year + .2, m.export_kt, .38, color=ORANGE, label="Russian exports to Kyrgyzstan")
    ax.set_title("Gasoline mirror check, thousand tonnes")
    ax.set_ylim(0, 1450)
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    save(fig, "fig11_kyrgyz_reconciliation")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    ax = axes[0]
    d = all_goods[all_goods.period >= 202501].assign(month=lambda x: pd.to_datetime(x.period.astype(str), format="%Y%m"))
    ax.plot(d.month, d.nsc_latest_usd_m, color=ORANGE, lw=2, label="National, latest figure")
    ax.plot(d.month, d.nsc_first_usd_m, color=AQUA, lw=2, label="National, first release")
    ax.plot(d.month, d.comtrade_total_usd_m, color=BLUE, lw=2, ls="--", label="Comtrade")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.set_title("All goods imports, USD million")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    for fuel, color, label in [("gasoline", BLUE, "Gasoline"), ("diesel", ORANGE, "Diesel")]:
        s = dependency[(dependency.fuel == fuel) & (dependency.year >= 2005)]
        ax.plot(s.year, s.net_import_dependency, color=color, lw=2, label=label)
    ax.axhline(1, color=MUTED, lw=1, ls="--")
    ax.set_title("Net imports as a share of domestic use")
    ax.set_xticks(range(2006, 2025, 3))
    ax.legend(loc="lower right")
    ax.grid(axis="x", visible=False)
    save(fig, "fig12_kyrgyz_vintage_and_dependency")


def run_all(data, reconciliation, dependency, mirror, all_goods, cov):
    FIG.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    style()
    monthly, conc, external, annual = data["monthly"], data["concentration"], data["external"], data["annual"]
    kyrgyz_monthly(monthly)
    trends = annual_trends(monthly)
    season = seasonality(monthly, cov)
    strengths = stl_strengths(monthly, cov)
    run = stl_kyrgyz(monthly)
    segments, pooled = structural_breaks(monthly, cov)
    scale = scale_comparison(monthly, cov, annual)
    conc_table = concentration_views(monthly, conc, cov)
    coverage_heatmap(cov, monthly)
    corr, corr_summary = external_correlations(monthly, external, cov)
    gdp = gdp_correlations(monthly, annual, cov)
    shortfall = shortfall_recount(monthly)
    comove = panel_comovement(monthly, cov)
    kyrgyz_validation_figures(reconciliation, dependency, mirror, all_goods)
    for name, table in [("seasonality_kruskal", season), ("stl_strength", strengths), ("kyrgyz_segments", segments), ("structural_breaks_panel", pooled), ("gdp_correlations", gdp), ("shortfall_recount", shortfall)]:
        table.to_csv(TABLES / f"{name}.csv", index=False)
    return {"trends": trends, "season": season, "strengths": strengths, "stl_run": run, "segments": segments, "pooled_breaks": pooled, "scale": scale, "concentration": conc_table,
            "correlations": corr, "correlation_summary": corr_summary, "gdp": gdp, "shortfall": shortfall, "comovement": comove}
