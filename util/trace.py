import logging
from functools import wraps


class Trace:
    """
    Decorator for tracing function calls. If you add the trace decorator to a function,
    it logs the start and end of every function call to the provided logger.
    Helps debugging the program flow, especially once we deploy the program to our collaborators,
    so we can see exactly what they did.
    """
    default_logger = logging.getLogger()
    default_level = logging.DEBUG

    @classmethod
    def set_default_logger(cls, logger):
        cls.default_logger = logger

    # TODO: Add an option log the arguments and return values of the function.
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
