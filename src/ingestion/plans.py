"""Build Comtrade task lists. Requests stay in classic mode with the total
partner2/transport/customs filters, so one row is one reporter-product-partner-month."""
from src.utils.config import months_between

TOTAL_FILTERS = {"partner2Code": 0, "motCode": 0, "customsCode": "C00"}


def _chunks(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


def bilateral_tasks(reporters, periods, codes, flows, periods_per_call):
    """Partner-level records; partnerCode stays open so World rows arrive alongside partners."""
    code_list = ",".join(codes)
    return [{"reporterCode": int(r), "period": ",".join(map(str, chunk)), "cmdCode": code_list, "flowCode": flows, **TOTAL_FILTERS}
            for r in reporters for chunk in _chunks(list(periods), periods_per_call)]


def world_tasks(reporters, periods, codes, flow="M"):
    """World-level audit, one call per month across all candidates."""
    reporter_list = ",".join(str(r) for r in reporters)
    return [{"reporterCode": reporter_list, "period": str(p), "cmdCode": ",".join(codes), "flowCode": flow, "partnerCode": 0, **TOTAL_FILTERS}
            for p in periods]


def window(cfg):
    return months_between(cfg["start"], cfg["end"])
