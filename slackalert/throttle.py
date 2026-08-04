"""De-dupe / rate-window helper.

Suppresses repeat alerts sharing the same key within a rolling time window.
The clock is injectable so tests can advance time without real sleeps.
"""

from __future__ import annotations

import time
from typing import Callable, Dict


class Throttle:
    """Allow an alert key at most once per ``window_seconds``.

    Args:
        window_seconds: Suppression window; duplicates within it are dropped.
        clock: Zero-arg callable returning a monotonically increasing float
            (seconds). Defaults to :func:`time.monotonic`; inject a fake in
            tests to control time deterministically.
    """

    def __init__(
        self,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative.")
        self.window_seconds = window_seconds
        self._clock = clock
        self._last_seen: Dict[str, float] = {}

    def should_send(self, key: str) -> bool:
        """Return True if ``key`` may be sent now, recording the send time.

        The first occurrence of a key always passes. Subsequent occurrences
        pass only once the window has elapsed since the last allowed send.
        """
        now = self._clock()
        last = self._last_seen.get(key)
        if last is not None and (now - last) < self.window_seconds:
            return False
        self._last_seen[key] = now
        return True

    def reset(self, key: str | None = None) -> None:
        """Forget throttling state for one key, or all keys when key is None."""
        if key is None:
            self._last_seen.clear()
        else:
            self._last_seen.pop(key, None)
