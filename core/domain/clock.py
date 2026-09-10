"""
Clock Protocol and Implementations for QuakMeeting.
Provides an abstraction over system time for deterministic testing and simulation.
"""
from typing import Protocol, runtime_checkable
from datetime import datetime, timezone, timedelta
import time


@runtime_checkable
class Clock(Protocol):
    """Protocol for querying current time."""

    def now(self) -> datetime:
        """Returns current timezone-aware UTC datetime."""
        ...

    def time(self) -> float:
        """Returns current POSIX timestamp in seconds."""
        ...


class SystemClock:
    """Production clock querying the operating system."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def time(self) -> float:
        return time.time()


class FakeClock:
    """Deterministic, controllable clock for testing and simulations."""

    def __init__(self, initial_time: datetime):
        self._current = initial_time.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._current

    def time(self) -> float:
        return self._current.timestamp()

    def advance(self, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0) -> None:
        """Advances current clock time by the specified duration."""
        self._current += timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)

    def set_time(self, new_time: datetime) -> None:
        """Sets the clock to an exact datetime."""
        self._current = new_time.astimezone(timezone.utc)


# Global default clock instance
system_clock = SystemClock()
