"""slackalert - route operational alerts to Slack with rich Block Kit formatting."""

from .models import Alert, Severity
from .blocks import build_blocks, build_payload, escape_text, SEVERITY_STYLE
from .transport import Transport, WebhookTransport, MockTransport
from .client import AlertClient
from .throttle import Throttle

__all__ = [
    "Alert",
    "Severity",
    "build_blocks",
    "build_payload",
    "escape_text",
    "SEVERITY_STYLE",
    "Transport",
    "WebhookTransport",
    "MockTransport",
    "AlertClient",
    "Throttle",
]

__version__ = "0.1.0"
