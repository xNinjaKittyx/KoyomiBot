import inspect
import logging


class FStringFormatter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def process(self, msg, kwargs):
        d = inspect.stack()[3].frame.f_locals
        try:
            msg = msg.format(**d)
        except Exception:
            print(f"Could not find within {d}")
            raise
        return (msg, kwargs)
