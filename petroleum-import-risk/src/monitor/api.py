"""Fuel Import Risk Monitor API. Run: uvicorn src.monitor.api:app --port 8000 (docs at /docs).

Read-only. Forecasts are published with publication lag, so the monitor is an early warning
based on the latest released customs data, not a live feed.
"""
import logging
import time

from fastapi import FastAPI, HTTPException, Path, Query, Request

from src.monitor import service as svc

log = logging.getLogger("monitor.api")
app = FastAPI(title="Fuel Import Risk Monitor", version="1.0",
              description="Probabilistic forecasts of monthly refined-fuel imports and an import-shortfall signal "
                          "for landlocked economies. The p_shortfall fields are the import-shortfall signal probability "
                          "(imports below 75% of the seasonal baseline), not a probability of physical shortage; domestic "
                          "production, stocks and FX are not observed. Research prototype; data: UN Comtrade and public sources.")

ISO3 = Path(..., pattern="^[A-Za-z]{3}$", description="ISO3 country code, e.g. KGZ")
PRODUCT = Path(..., pattern="^(gasoline|distillates)$")
ORIGIN = Query("latest", pattern=r"^(latest|\d{4}-\d{2})$", description="forecast origin month, YYYY-MM")


@app.middleware("http")
async def access_log(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    log.info("%s %s %d %.0fms", request.method, request.url.path, response.status_code, 1000 * (time.perf_counter() - t0))
    return response


def _call(fn, *args):
    try:
        return fn(*args)
    except svc.NotFound as e:
        raise HTTPException(status_code=404, detail=str(e.args[0])) from None


@app.get("/health")
def health():
    o = svc.latest_origin()
    return {"status": "ok", "latest_origin": f"{o:%Y-%m}", "model": svc.settings()["monitor"]["model"]}


@app.get("/series")
def series():
    return svc.series_list()


@app.get("/risk")
def risk(origin: str = ORIGIN):
    return _call(svc.risk_table, origin)


@app.get("/forecast/{iso3}/{product}")
def forecast(iso3: str = ISO3, product: str = PRODUCT, origin: str = ORIGIN):
    return _call(svc.forecast, iso3, product, origin)


@app.get("/suppliers/{iso3}/{product}")
def suppliers(iso3: str = ISO3, product: str = PRODUCT, months: int = Query(12, ge=1, le=60)):
    return _call(svc.suppliers, iso3, product, months)


@app.get("/events/{iso3}")
def events(iso3: str = ISO3):
    return svc.events(iso3)


@app.get("/performance")
def performance():
    return _call(svc.performance)
