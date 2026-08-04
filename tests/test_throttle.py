"""Throttle de-dupe behavior with an injected, controllable clock."""

from slackalert import Alert, AlertClient, MockTransport, Severity, Throttle


class FakeClock:
    """Deterministic clock; advance manually, never sleeps."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_duplicate_within_window_is_suppressed():
    clock = FakeClock()
    throttle = Throttle(window_seconds=60, clock=clock)

    assert throttle.should_send("k") is True   # first always passes
    assert throttle.should_send("k") is False  # duplicate within window
    clock.advance(30)
    assert throttle.should_send("k") is False  # still inside window


def test_send_allowed_after_window_elapses():
    clock = FakeClock()
    throttle = Throttle(window_seconds=60, clock=clock)

    assert throttle.should_send("k") is True
    clock.advance(60)
    assert throttle.should_send("k") is True   # window boundary elapsed


def test_distinct_keys_are_independent():
    clock = FakeClock()
    throttle = Throttle(window_seconds=60, clock=clock)
    assert throttle.should_send("a") is True
    assert throttle.should_send("b") is True


def test_client_drops_throttled_duplicates():
    clock = FakeClock()
    throttle = Throttle(window_seconds=300, clock=clock)
    transport = MockTransport()
    client = AlertClient(transport, throttle=throttle)

    alert = Alert(severity=Severity.ERROR, title="DB unreachable")
    first = client.send(alert)
    second = client.send(alert)  # same key, within window

    assert first is not None
    assert second is None
    assert len(transport.sent) == 1  # only one payload actually delivered

    clock.advance(300)
    third = client.send(alert)
    assert third is not None
    assert len(transport.sent) == 2
