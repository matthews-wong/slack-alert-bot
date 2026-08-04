"""Command-line entry point for sending an alert to Slack.

Build an alert from flags or a JSON file, render Block Kit, and deliver it
through either the real webhook transport or the offline MockTransport.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

from .blocks import build_payload
from .client import AlertClient
from .models import Alert, Severity
from .transport import MockTransport, WebhookTransport

WEBHOOK_ENV_VAR = "SLACK_WEBHOOK_URL"


def _parse_pairs(pairs: Optional[List[str]], flag: str) -> Dict[str, str]:
    """Parse repeated ``key=value`` flags into an ordered dict."""
    result: Dict[str, str] = {}
    for item in pairs or []:
        if "=" not in item:
            raise SystemExit(f"Invalid {flag} value {item!r}; expected key=value.")
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _build_alert(args: argparse.Namespace) -> Alert:
    if args.json:
        with open(args.json, "r", encoding="utf-8") as handle:
            return Alert.from_dict(json.load(handle))
    if not args.title:
        raise SystemExit("Either --json or --title is required.")
    return Alert(
        severity=Severity.parse(args.severity),
        title=args.title,
        description=args.description or "",
        fields=_parse_pairs(args.field, "--field"),
        links=_parse_pairs(args.link, "--link"),
        source=args.source,
        dedupe_key=args.dedupe_key,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slack-alert-bot",
        description="Render an operational alert as Slack Block Kit and deliver it.",
    )
    parser.add_argument(
        "--severity",
        default=Severity.INFO.value,
        help="info | warning | error | critical (default: info)",
    )
    parser.add_argument("--title", help="Alert headline.")
    parser.add_argument("--description", help="Longer alert body (mrkdwn allowed).")
    parser.add_argument("--source", help="Origin of the alert (service/host/job).")
    parser.add_argument("--dedupe-key", dest="dedupe_key", help="Stable throttle key.")
    parser.add_argument(
        "--field",
        action="append",
        metavar="KEY=VALUE",
        help="Metadata field (repeatable).",
    )
    parser.add_argument(
        "--link",
        action="append",
        metavar="LABEL=URL",
        help="Action-button link (repeatable).",
    )
    parser.add_argument("--json", help="Read the alert from a JSON file instead of flags.")
    parser.add_argument(
        "--webhook-url",
        dest="webhook_url",
        help=f"Slack incoming webhook URL (falls back to ${WEBHOOK_ENV_VAR}).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Do not send; print the payload that would be delivered (offline).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    alert = _build_alert(args)

    if args.mock:
        transport = MockTransport()
        AlertClient(transport).send(alert)
        json.dump(transport.last, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    webhook_url = args.webhook_url or os.environ.get(WEBHOOK_ENV_VAR)
    if not webhook_url:
        raise SystemExit(
            f"No webhook URL: pass --webhook-url or set ${WEBHOOK_ENV_VAR} "
            "(or use --mock to preview offline)."
        )
    AlertClient(WebhookTransport(webhook_url)).send(alert)
    sys.stdout.write("Alert delivered.\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
