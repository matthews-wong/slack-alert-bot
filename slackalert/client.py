"""High-level entry point: build a payload, throttle, and deliver it."""

from __future__ import annotations

from typing import Optional

from .blocks import build_payload
from .models import Alert
from .throttle import Throttle
from .transport import Transport


class AlertClient:
    """Render alerts and deliver them through an injectable transport.

    Args:
        transport: Any object satisfying the ``Transport`` protocol.
        throttle: Optional :class:`Throttle`; when set, duplicate alerts
            within the window are suppressed and :meth:`send` returns None.
    """

    def __init__(self, transport: Transport, throttle: Optional[Throttle] = None) -> None:
        self.transport = transport
        self.throttle = throttle

    def send(self, alert: Alert):
        """Send an alert. Returns the transport result, or None if throttled."""
        if self.throttle is not None and not self.throttle.should_send(alert.key):
            return None
        payload = build_payload(alert)
        return self.transport.send(payload)
