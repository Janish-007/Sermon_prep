import logging
from logging_loki import LokiHandler
import uuid
import os
import contextvars

# Context variable for request ID
_request_id_ctx_var = contextvars.ContextVar("request_id", default=None)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        request_id = _request_id_ctx_var.get()
        record.request_id = request_id or "unknown"
        return True

def set_request_id(request_id=None):
    if not request_id:
        request_id = str(uuid.uuid4())
    _request_id_ctx_var.set(request_id)
    return request_id

logger_instance = None

def setup_console_handler(logger):
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(request_id)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def setup_loki_handler(logger):
    loki_url = os.getenv('LOKI_URL')
    loki_username = os.getenv('LOKI_USERNAME')
    loki_password = os.getenv('LOKI_PASSWORD')

    if not loki_url:
        print("No Loki URL configured, skipping Loki handler.")
        return

    try:
        if not loki_username:
            loki_handler = LokiHandler(
                url=loki_url,
                tags={"application": "ark-ai"},
                version="1",
            )
        else:
            loki_handler = LokiHandler(
                url=loki_url,
                tags={"application": "ark-ai"},
                auth=(loki_username, loki_password),
                version="1",
            )
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(request_id)s - %(message)s')
        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)
        print(f"Initialized Loki handler at {loki_url}")
    except Exception as e:
        print(f"Failed to initialize LokiHandler: {e}")

def get_logger():
    global logger_instance
    if logger_instance is None:
        logger_instance = logging.getLogger("ark-ai")
        logger_instance.setLevel(logging.DEBUG)
        logger_instance.addFilter(RequestIdFilter())
        setup_console_handler(logger_instance)
        setup_loki_handler(logger_instance)
        logger_instance.propagate = False
        print("Logger initialized")
    return logger_instance
