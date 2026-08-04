"""Block Kit payload structure and severity styling."""

import json

import pytest

from slackalert import Alert, Severity, build_blocks, build_payload
from slackalert.blocks import SEVERITY_STYLE


@pytest.fixture
def alert():
    return Alert(
        severity=Severity.CRITICAL,
        title="Disk almost full",
        description="Only *2%* free on `/data`.",
        fields={"Host": "db-01", "Free": "2%"},
        links={"Runbook": "https://example.com/runbook"},
        source="node-exporter",
    )


def test_blocks_have_expected_structure(alert):
    blocks = build_blocks(alert)
    types = [b["type"] for b in blocks]
    # header, description section, fields section, actions, context
    assert types == ["header", "section", "section", "actions", "context"]

    header = blocks[0]
    assert header["text"]["type"] == "plain_text"
    assert alert.title in header["text"]["text"]
    assert SEVERITY_STYLE[Severity.CRITICAL]["emoji"] in header["text"]["text"]

    fields_block = blocks[2]
    assert len(fields_block["fields"]) == 2
    assert all(f["type"] == "mrkdwn" for f in fields_block["fields"])

    actions_block = blocks[3]
    assert actions_block["elements"][0]["url"] == "https://example.com/runbook"


def test_payload_carries_severity_color(alert):
    payload = build_payload(alert)
    attachment = payload["attachments"][0]
    assert attachment["color"] == SEVERITY_STYLE[Severity.CRITICAL]["color"]
    assert attachment["color"] == "#8b0000"
    assert "blocks" in attachment
    assert attachment["fallback"].startswith("[CRITICAL]")


def test_payload_is_well_formed_json(alert):
    payload = build_payload(alert)
    # Round-trips through JSON without error -> well-formed and serializable.
    assert json.loads(json.dumps(payload)) == payload


def test_minimal_alert_omits_optional_blocks():
    payload = build_payload(Alert(severity=Severity.INFO, title="Heartbeat"))
    types = [b["type"] for b in payload["attachments"][0]["blocks"]]
    # No description, fields, or links -> only header + context remain.
    assert types == ["header", "context"]


@pytest.mark.parametrize(
    "severity,color",
    [
        (Severity.INFO, "#36a64f"),
        (Severity.WARNING, "#e8a33d"),
        (Severity.ERROR, "#e01e5a"),
        (Severity.CRITICAL, "#8b0000"),
    ],
)
def test_each_severity_maps_to_its_color(severity, color):
    payload = build_payload(Alert(severity=severity, title="x"))
    assert payload["attachments"][0]["color"] == color
