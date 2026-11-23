"""Logging setup. A filter masks API keys so they can never reach a log line."""
import logging
import os
import sys
from pathlib import Path


class SecretFilter(logging.Filter):
    def __init__(self, secrets):
        super().__init__()
        self.secrets = [s for s in secrets if s]

    def filter(self, record):
        msg = record.getMessage()
        for secret in self.secrets:
            msg = msg.replace(secret, "***")
        record.msg, record.args = msg, None
        return True


def setup_logging(name="pipeline", log_dir="logs"):
    Path(log_dir).mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    secret_filter = SecretFilter([os.getenv("UN_COMTRADE_PRIMARY_KEY"), os.getenv("UN_COMTRADE_SECONDARY_KEY")])
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(f"{log_dir}/{name}.log", encoding="utf-8")):
        handler.setFormatter(fmt)
        handler.addFilter(secret_filter)
        root.addHandler(handler)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger(name)
