"""MockTransport capture behavior and client delivery (offline only)."""

import pytest

from slackalert import Alert, AlertClient, MockTransport, Severity, Transport


def test_mock_transport_captures_payload():
    transport = MockTransport()
    client = AlertClient(transport)

    alert = Alert(severity=Severity.WARNING, title="High latency")
    result = client.send(alert)

    assert len(transport.sent) == 1
    assert transport.last is transport.sent[0]
    assert transport.last["attachments"][0]["color"] == "#e8a33d"
    assert result["ok"] is True


def test_mock_transport_is_a_transport():
    # Structural typing: MockTransport satisfies the Transport protocol.
    assert isinstance(MockTransport(), Transport)


def test_last_raises_before_any_send():
    with pytest.raises(IndexError):
        _ = MockTransport().last


def test_multiple_sends_accumulate():
    transport = MockTransport()
    client = AlertClient(transport)
    for i in range(3):
        client.send(Alert(severity=Severity.INFO, title=f"tick {i}"))
    assert len(transport.sent) == 3
    assert transport.last["attachments"][0]["fallback"] == "[INFO] tick 2"
