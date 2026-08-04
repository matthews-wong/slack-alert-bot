"""Delivery transports for Slack payloads.

The core library depends only on the ``Transport`` protocol; concrete HTTP
delivery (``WebhookTransport``) lives behind that seam, and ``MockTransport``
lets tests and demos run fully offline.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Anything that can deliver a Slack payload dict."""

    def send(self, payload: dict) -> object:
        """Deliver the payload. Returns a transport-specific result."""
        ...


class MockTransport:
    """In-memory transport that captures payloads instead of sending them.

    Useful for tests and offline demos: every payload passed to :meth:`send`
    is appended to :attr:`sent`.
    """

    def __init__(self) -> None:
        self.sent: List[dict] = []

    def send(self, payload: dict) -> dict:
        self.sent.append(payload)
        return {"ok": True, "captured": len(self.sent)}

    @property
    def last(self) -> dict:
        """The most recently captured payload."""
        if not self.sent:
            raise IndexError("No payloads have been sent yet.")
        return self.sent[-1]


class WebhookTransport:
    """Deliver payloads to a Slack Incoming Webhook via ``requests``.

    ``requests`` is imported lazily so the library (and its offline tests)
    have no hard dependency on it unless real delivery is actually used.
    """

    def __init__(self, webhook_url: str, timeout: float = 10.0) -> None:
        if not webhook_url:
            raise ValueError("WebhookTransport requires a non-empty webhook_url.")
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send(self, payload: dict):
        import requests  # local import keeps requests optional for offline use

        response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response
