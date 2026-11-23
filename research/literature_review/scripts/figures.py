"""Stage 8b: static figures for the Word report (light print mode). Palette: the validated reference categorical
order (dataviz skill references/palette.md, light column); one hue for single-series charts; a single-hue
sequential ramp for the score heatmap. Writes final/figures/*.png.
"""
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "final" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})
stats = json.load(open(ROOT / "metadata" / "raw" / "stats.json", encoding="utf-8"))


def prisma():
    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    src = stats["raw_records_by_source"]
    pres = stats["prescreen"]
    rule_ex = sum(v for k, v in pres.items() if k.startswith("E"))
    gap_ex = pres.get("G0_gapcheck_result_without_boolean_match", 0)
    manual = stats["manual_screened"]
    inc = stats["included"]
    boxes = [
        (5, 86, 58, 11, f"Records identified: {stats['raw_records_total']:,}\nOpenAlex {src['openalex']:,} | Crossref {src['crossref']:,} | arXiv {src['arxiv']}\n"
                        f"Semantic Scholar {src['semanticscholar']} | citation chasing {src['snowball']} | seeds {src['seedrecords']}\nCrossref gap checks {src['gapcheck_crossref']:,} | Connected Papers 28 (cross-check)"),
        (5, 68, 58, 8, f"Unique records after deduplication: {stats['unique_records']:,}\n({stats['multi_version_groups']} preprint/journal version groups merged)"),
        (5, 51, 58, 9, f"Title pre-screen (documented keyword rules)\n{stats['unique_records']:,} records"),
        (5, 35, 58, 9, f"Manual title/abstract screening\n{manual:,} records"),
        (5, 18, 58, 9, f"Included: {inc} works\n{stats['core']} core (detailed extraction) + {stats['support']} supporting"),
        (5, 3, 58, 9, f"Analysis basis: full text {stats['basis'].get('Full text', 0)} | abstract {stats['basis'].get('Abstract only', 0)} | metadata {stats['basis'].get('Metadata only', 0)}\n"
                      f"Open-licence PDFs stored: {stats['downloads'].get('downloaded', 0)}  (+ {stats['institutional_extra']} institutional reports)"),
    ]
    side = [
        (68, 49, 30, 13, f"Excluded by rules: {rule_ex:,}\noff-topic title {pres.get('E0_off_topic_title', 0):,}\nelectricity/renewables {pres.get('E1_electricity_renewables', 0)}\nprice/financial {pres.get('E2_price_or_financial_target', 0)}; other {pres.get('E3_upstream_or_engineering', 0) + pres.get('E4_non_research_item', 0) + pres.get('E5_other_commodity_or_domain', 0)}"),
        (68, 66, 30, 9, f"Gap-check results without\nBoolean match: {gap_ex:,}"),
        (68, 33, 30, 11, f"Excluded at manual\nscreening: {manual - (inc - 3):,}\n(incl. 17 proposal seeds\noutside scope)"),
    ]
    for x, y, w, h, t in boxes + side:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=SURF, ec="#9a9893", lw=1))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.6, color=INK, linespacing=1.35)
    for y0, y1 in [(86, 76.8), (68, 60.8), (51, 44.8), (35, 27.8), (18, 12.8)]:
        ax.annotate("", (34, y1), (34, y0 - 0.6), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1))
    for ys in (55.5, 72, 39.5):
        ax.annotate("", (67.4, ys), (63.6, ys), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1))
    fig.savefig(OUT / "fig1_prisma.png", dpi=220, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def years():
    rows = list(csv.DictReader(open(ROOT / "metadata" / "papers_master.csv", encoding="utf-8-sig")))
    rows = [r for r in rows if r["theme"] != "Institutional report"]
    bins = [("before 2000", 0, 1999), ("2000-09", 2000, 2009), ("2010-14", 2010, 2014), ("2015-19", 2015, 2019),
            ("2020-22", 2020, 2022), ("2023-24", 2023, 2024), ("2025-26", 2025, 2026)]
    themes = ["Petroleum and trade-flow forecasting", "Energy security and early warning", "Geopolitical risk and sanctions",
              "Landlocked economies and Central Asia", "Global forecasting and forecast evaluation", "Deep learning versus gradient boosting",
              "Probabilistic forecasting"]
    counts = {t: [0] * len(bins) for t in themes}
    for r in rows:
        y = int(r["year"]) if str(r["year"]).isdigit() else 0
        for i, (_, a, b) in enumerate(bins):
            if a <= y <= b:
                counts[r["theme"]][i] += 1
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bottom = [0] * len(bins)
    for t, c in zip(themes, CAT):
        ax.bar(range(len(bins)), counts[t], bottom=bottom, color=c, width=0.62, label=t, edgecolor=SURF, linewidth=1.5)
        bottom = [b + v for b, v in zip(bottom, counts[t])]
    for i, b in enumerate(bottom):
        ax.text(i, b + 1, str(b), ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(len(bins)), [b[0] for b in bins])
    ax.set_ylabel("Included works")
    ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper left")
    ax.set_ylim(0, max(bottom) * 1.25)
    fig.savefig(OUT / "fig2_years_themes.png", dpi=220, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def methods_profile():
    rows = list(csv.DictReader(open(ROOT / "analysis" / "methodology_comparison.csv", encoding="utf-8-sig")))
    n = len(rows)
    checks = [("Pooled / global model across series", "global"), ("Probabilistic output (intervals, quantiles, probabilities)", "probabilistic"),
              ("Publication-lag or vintage-aware evaluation", "real_time"), ("Naive or no-change baseline reported", "naive_baseline"),
              ("Formal test of forecast-accuracy differences", "significance_test")]
    yes = [sum(1 for r in rows if r[c].startswith(("Yes", "Partly", "Compared"))) for _, c in checks]
    nr = [sum(1 for r in rows if r[c] in ("NR", "")) for _, c in checks]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    y = range(len(checks))[::-1]
    ax.barh(list(y), [v / n * 100 for v in yes], color=CAT[0], height=0.5)
    for yi, v, k in zip(y, yes, nr):
        ax.text(v / n * 100 + 1.2, yi, f"{v} of {n}  (not reported: {k})", va="center", fontsize=8, color=INK)
    ax.set_yticks(list(y), [c[0] for c in checks], fontsize=8)
    ax.set_xlim(0, 100); ax.set_xlabel("% of coded forecasting and early-warning studies (yes or partly)")
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    fig.savefig(OUT / "fig3_methods_profile.png", dpi=220, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def gap_scores():
    rows = list(csv.DictReader(open(ROOT / "analysis" / "research_gaps.csv", encoding="utf-8-sig")))
    rows.sort(key=lambda r: int(r["rank"]))
    crit = ["novelty", "practical", "evidence", "data", "experiment", "publication"]
    labels = ["Novelty", "Practical\nsignificance", "Evidence\nfrom literature", "Data\nfeasibility", "Experimental\nfeasibility", "Publication\nvalue"]
    data = [[int(r[f"score_{c}"]) for c in crit] for r in rows]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue_seq", ["#eef4fc", "#2a78d6", "#123f78"])
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.imshow(data, cmap=cmap, vmin=1, vmax=5, aspect="auto")
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=9, color=SURF if v >= 3 else INK)
        ax.text(len(crit) - 0.35, i, f"  total {sum(row)}", ha="left", va="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(crit)), labels, fontsize=7.5)
    ax.set_yticks(range(len(rows)), [f"{r['gap']}. {r['name'][:52]}{'...' if len(r['name']) > 52 else ''}" for r in rows], fontsize=7.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlim(-0.5, len(crit) + 0.6)
    fig.savefig(OUT / "fig4_gap_scores.png", dpi=220, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


if __name__ == "__main__":
    prisma(); years(); methods_profile(); gap_scores()
    print(sorted(p.name for p in OUT.glob("*.png")))
