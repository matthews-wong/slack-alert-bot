"""Domain models for alerts.

Kept framework-free so the core stays independent of Slack/HTTP concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Severity(str, Enum):
    """Alert severity levels, ordered from least to most urgent.

    Inherits from ``str`` so values serialize cleanly to JSON and compare
    against plain strings coming from CLI flags or JSON files.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @classmethod
    def parse(cls, value: "Severity | str") -> "Severity":
        """Coerce a string (case-insensitive) or Severity into a Severity."""
        if isinstance(value, Severity):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError as exc:
            valid = ", ".join(s.value for s in cls)
            raise ValueError(
                f"Unknown severity {value!r}. Expected one of: {valid}."
            ) from exc


@dataclass
class Alert:
    """An operational alert to be rendered and delivered to Slack.

    Attributes:
        severity: How urgent the alert is; drives color and emoji.
        title: Short headline shown in the Slack header block.
        description: Longer human-readable body (mrkdwn allowed).
        fields: Ordered key/value metadata rendered as a two-column grid.
        links: Named links (label -> url) rendered as action buttons.
        source: Optional origin of the alert (service, host, job).
        dedupe_key: Optional stable key for throttling; falls back to
            ``severity:title`` when not provided.
    """

    severity: Severity
    title: str
    description: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    links: Dict[str, str] = field(default_factory=dict)
    source: Optional[str] = None
    dedupe_key: Optional[str] = None

    def __post_init__(self) -> None:
        self.severity = Severity.parse(self.severity)
        if not self.title or not str(self.title).strip():
            raise ValueError("Alert.title must be a non-empty string.")

    @property
    def key(self) -> str:
        """Stable identity used for de-duplication/throttling."""
        return self.dedupe_key or f"{self.severity.value}:{self.title}"

    @classmethod
    def from_dict(cls, data: Dict) -> "Alert":
        """Build an Alert from a plain dict (e.g. parsed JSON)."""
        return cls(
            severity=Severity.parse(data.get("severity", Severity.INFO)),
            title=data["title"],
            description=data.get("description", ""),
            fields=dict(data.get("fields", {})),
            links=dict(data.get("links", {})),
            source=data.get("source"),
            dedupe_key=data.get("dedupe_key"),
        )
