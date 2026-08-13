"""Block Kit payload structure and severity styling."""

import json

import pytest

from slackalert import Alert, Severity, build_blocks, build_payload, escape_text
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


def test_escape_text_handles_control_chars_ampersand_first():
    # & must be escaped before < / > so &lt; / &gt; are not double-escaped.
    assert escape_text("a < b & c > d") == "a &lt; b &amp; c &gt; d"
    assert escape_text("&lt;") == "&amp;lt;"


def test_special_chars_escaped_in_all_text_fields():
    # Untrusted alert content must not smuggle Slack markup into any text
    # field: <url|label> would otherwise render as an injected link.
    alert = Alert(
        severity=Severity.ERROR,
        title="q > 5 & p < 1",
        description="see <https://evil.example.com|click> & retry",
        fields={"a<b": "x&y"},
        source="svc<1>",
    )
    payload = build_payload(alert)
    blocks = payload["attachments"][0]["blocks"]

    header_text = blocks[0]["text"]["text"]
    assert header_text == ":x: q &gt; 5 &amp; p &lt; 1"

    description_text = blocks[1]["text"]["text"]
    assert description_text == "see &lt;https://evil.example.com|click&gt; &amp; retry"
    # No raw markup delimiters survive -> no link injection.
    assert "<" not in description_text and ">" not in description_text

    field_text = blocks[2]["fields"][0]["text"]
    assert field_text == "*a&lt;b*\nx&amp;y"

    context_text = blocks[-1]["elements"][0]["text"]
    assert "`svc&lt;1&gt;`" in context_text

    # Fallback (plain-text notification) is escaped too.
    assert payload["attachments"][0]["fallback"] == "[ERROR] q &gt; 5 &amp; p &lt; 1"


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
