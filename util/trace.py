import logging
from functools import wraps


class Trace:
    default_logger = logging.getLogger()
    default_level = logging.DEBUG

    @classmethod
    def set_default_logger(cls, logger):
        cls.default_logger = logger

    @classmethod
    def trace(cls, logger=None, level: int = None):
        if logger is None:
            logger = cls.default_logger
        if level is None:
            level = cls.default_level

        def decorator(func):
            qualname = func.__qualname__

            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.log(level, "FUN %s", qualname)
                result = func(*args, **kwargs)
                logger.log(level, "FUNEND %s", qualname)
                return result
            return wrapper
        return decorator
