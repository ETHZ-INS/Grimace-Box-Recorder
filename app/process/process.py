from abc import ABC, abstractmethod
from typing import Callable


class IProcess(ABC):
    """
    A process that is a part of the processing pipeline.
    It is expected to stop by itself when its input queue is closed.
    If it has an output queue, it should close it when it stops.
    It is expected to clean after itself when it stops.
    """

    # TODO: Added args and kwargs to the methods for compatibility with qthreads. Is this the right way?
    @abstractmethod
    def start(self, *args, **kwargs):
        # Start the process
        raise NotImplementedError

    @abstractmethod
    def stop(self, *args, **kwargs):
        # Stop the process ungracefully. Should close the input queue.
        # Should be idempotent, i.e. calling stop multiple times should not cause an error.
        raise NotImplementedError

    # TODO Added return type for compatibility with qthreads. Is this the right way?
    @abstractmethod
    def wait(self, timeout: int = None) -> bool:
        # Wait for the process to stop. Returns True if the process stopped, False if the timeout was reached.
        # If timeout is None, wait indefinitely
        raise NotImplementedError

    @abstractmethod
    def on_error(self, func: Callable):
        # Register a function to be called when an error occurs. Should use Qt signals.
        raise NotImplementedError

    def check_health(self, *args, **kwargs) -> dict:
        # Check the health of the process. Should return a dictionary of warnings and optionally additional values.
        # Each warning should have a unique key and a human-readable message as the value.
        return {"warnings": {}}
