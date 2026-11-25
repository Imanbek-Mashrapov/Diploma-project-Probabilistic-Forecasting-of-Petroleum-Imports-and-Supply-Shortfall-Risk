"""Streamlit client for the Fuel Import Risk Monitor. Talks to the API only.

Run: streamlit run src/monitor/dashboard.py   (API address from MONITOR_API_URL, default http://localhost:8000)
"""
import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API = os.getenv("MONITOR_API_URL", "http://localhost:8000")
COLORS = {"green": "#2e7d32", "amber": "#ef8f00", "red": "#c62828", "unknown": "#757575"}

st.set_page_config(page_title="Fuel Import Risk Monitor", layout="wide")


@st.cache_data(ttl=300)
def get(path, **params):
    r = requests.get(f"{API}{path}", params=params, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


try:
    health = get("/health")
except requests.RequestException as e:
    st.error(f"The monitor API at {API} is not reachable: {e}")
    st.stop()

st.title("Fuel Import Risk Monitor")
st.caption(f"Origin {health['latest_origin']} · model {health['model']} · research prototype. Customs data are published "
           "with a lag of 2-4 months, so this is an early warning based on the latest released data, not a live feed.")

risk = get("/risk")
table = pd.DataFrame(risk["rows"])
series = pd.DataFrame(get("/series"))
table = table.merge(series[["iso3", "product", "country", "tier"]], on=["iso3", "product"], how="left")

left, right = st.columns([2, 3])
with left:
    st.subheader("Import-shortfall signal, next three months (watch-list)")
    st.caption("Signal that imports fall below 75% of the seasonal baseline over the next three months (recalibrated on past outcomes). "
               "Amber ≥ 20%, red ≥ 40%. The score ranks series by how unusual the forecast import decline is against the seasonal baseline. "
               "In backtests it beat a supplier-concentration index but was not significantly better than simple forecasts. "
               "It is not a probability of physical shortage: domestic production, stocks and FX are not observed.")
    show = table[["country", "product", "tier", "p_shortfall", "status", "hhi_12m", "months_since_data"]].copy()
    show["p_shortfall"] = (show.p_shortfall * 100).round(0)
    st.dataframe(show.rename(columns={"p_shortfall": "signal %", "hhi_12m": "HHI", "months_since_data": "data age (months)"}),
                 hide_index=True, use_container_width=True,
                 column_config={"status": st.column_config.TextColumn("status")})

with right:
    options = table.sort_values(["country", "product"])
    labels = [f"{r.country} · {r.product}" for r in options.itertuples()]
    default = next((i for i, r in enumerate(options.itertuples()) if r.iso3 == "KGZ" and r.product == "gasoline"), 0)
    choice = st.selectbox("Series", range(len(labels)), index=default, format_func=lambda i: labels[i])
    pick = options.iloc[choice]
    fc = get(f"/forecast/{pick.iso3}/{pick['product']}")
    hist = pd.DataFrame(fc["history"])
    f = pd.DataFrame([x for x in fc["forecasts"] if x["task"] != "sum3"])
    status = pick.status
    st.markdown(f"**Status:** <span style='color:{COLORS[status]};font-weight:600'>{status.upper()}</span> · "
                f"import-shortfall signal {pick.p_shortfall:.0%}" if pd.notna(pick.p_shortfall) else "**Status:** unknown",
                unsafe_allow_html=True)
    age = pick.get("months_since_data")
    st.markdown("**Data age:** " + (f"{int(age)} months since the last released data" if pd.notna(age) else "unknown")
                + " (customs data are released with a lag; the signal reflects data up to that month).")
    fig = go.Figure()
    seen = hist[hist.public_at_origin]
    later = hist[~hist.public_at_origin & hist.mass_t.notna()]
    fig.add_trace(go.Scatter(x=seen.month, y=seen.mass_t / 1000, mode="lines+markers", name="released", line=dict(color="black")))
    if not later.empty:
        fig.add_trace(go.Scatter(x=later.month, y=later.mass_t / 1000, mode="markers", name="released after origin",
                                 marker=dict(color="grey", symbol="circle-open")))
    if not f.empty:
        fig.add_trace(go.Scatter(x=list(f.target_month) + list(f.target_month[::-1]), y=list(f.q975_t / 1000) + list(f.q025_t[::-1] / 1000),
                                 fill="toself", mode="lines", fillcolor="rgba(30,100,200,0.12)", line=dict(width=0), name="95% interval"))
        fig.add_trace(go.Scatter(x=list(f.target_month) + list(f.target_month[::-1]), y=list(f.q900_t / 1000) + list(f.q100_t[::-1] / 1000),
                                 fill="toself", mode="lines", fillcolor="rgba(30,100,200,0.25)", line=dict(width=0), name="80% interval"))
        fig.add_trace(go.Scatter(x=f.target_month, y=f.q500_t / 1000, mode="lines+markers", name="median forecast", line=dict(color="#1e64c8")))
    fig.update_layout(yaxis_title="thousand tonnes", height=380, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Supplier mix, last 12 months")
        sup = get(f"/suppliers/{pick.iso3}/{pick['product']}")
        if sup:
            s = pd.DataFrame(sup["suppliers"]).head(6)
            st.caption(sup["window"])
            st.bar_chart(s.set_index("name").share)
        else:
            st.info("No partner-level data for this series.")
    with c2:
        st.subheader("Documented events")
        evs = pd.DataFrame(get(f"/events/{pick.iso3}"))
        if evs.empty:
            st.info("No events in the calendar for this country.")
        else:
            st.dataframe(evs[["start", "end", "title", "role"]].sort_values("start", ascending=False), hide_index=True, use_container_width=True)

with st.expander("Backtest performance (origins 2023 onward)"):
    perf = pd.DataFrame(get("/performance") or [])
    if not perf.empty:
        st.dataframe(perf.pivot(index="model", columns="task", values="MASE").round(3), use_container_width=True)
        st.caption("MASE below 1 beats the historical seasonal-naive error. Full results: reports/phase3/results.md.")
