from __future__ import annotations
import json, sys, os, logging
from logging.config import dictConfig
from uvicorn.config import LOG_LEVELS

SERVICE_NAME = os.getenv("SERVICE_NAME", "backend")
ENV = os.getenv("ENV", "production")

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
            "service": SERVICE_NAME,
            "env": ENV,
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if log_level not in LOG_LEVELS:
        log_level = "INFO"

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "plain": {"format": "%(levelname)s:%(name)s:%(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if ENV == "production" else "plain",
                "level": log_level,
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": log_level, "propagate": False},
            "fastapi": {"handlers": ["console"], "level": log_level, "propagate": False},
            "": {"handlers": ["console"], "level": log_level},  # root logger
        },
    })