"""Render an Alert into a Slack Block Kit payload.

Slack colors the vertical bar of a message via the legacy ``attachments``
wrapper, while modern layout comes from ``blocks``. We combine both: blocks
live inside a single attachment carrying the severity color.
"""

from __future__ import annotations

from typing import Dict, List

from .models import Alert, Severity

# Severity -> (color hex for the attachment bar, leading emoji).
SEVERITY_STYLE: Dict[Severity, Dict[str, str]] = {
    Severity.INFO: {"color": "#36a64f", "emoji": ":information_source:"},
    Severity.WARNING: {"color": "#e8a33d", "emoji": ":warning:"},
    Severity.ERROR: {"color": "#e01e5a", "emoji": ":x:"},
    Severity.CRITICAL: {"color": "#8b0000", "emoji": ":rotating_light:"},
}


def severity_color(severity: Severity) -> str:
    """Return the hex color associated with a severity."""
    return SEVERITY_STYLE[severity]["color"]


def severity_emoji(severity: Severity) -> str:
    """Return the Slack emoji shortcode associated with a severity."""
    return SEVERITY_STYLE[severity]["emoji"]


def build_blocks(alert: Alert) -> List[dict]:
    """Build the ordered list of Block Kit blocks for an alert."""
    style = SEVERITY_STYLE[alert.severity]
    blocks: List[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{style['emoji']} {alert.title}",
                "emoji": True,
            },
        }
    ]

    if alert.description:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": alert.description},
            }
        )

    if alert.fields:
        blocks.append(
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{key}*\n{value}"}
                    for key, value in alert.fields.items()
                ],
            }
        )

    if alert.links:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": label, "emoji": True},
                        "url": url,
                    }
                    for label, url in alert.links.items()
                ],
            }
        )

    context_parts = [f"Severity: *{alert.severity.value.upper()}*"]
    if alert.source:
        context_parts.append(f"Source: `{alert.source}`")
    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "  |  ".join(context_parts)}
            ],
        }
    )

    return blocks


def build_payload(alert: Alert) -> dict:
    """Build the full Slack payload (color bar + blocks) for an alert."""
    style = SEVERITY_STYLE[alert.severity]
    return {
        "attachments": [
            {
                "color": style["color"],
                "blocks": build_blocks(alert),
                # Plaintext fallback for notifications / clients without Block Kit.
                "fallback": f"[{alert.severity.value.upper()}] {alert.title}",
            }
        ]
    }
