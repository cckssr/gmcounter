"""Tests for core/reconnect_service.py — no Qt required."""

from gmcounter.core.reconnect_service import ReconnectStrategy, ConnectionRetryService


def test_strategy_should_retry():
    s = ReconnectStrategy(max_attempts=3)
    assert s.should_retry()
    s.attempt_count = 3
    assert not s.should_retry()


def test_strategy_delay_increases():
    s = ReconnectStrategy(initial_delay_ms=100, backoff_factor=2.0, max_attempts=5)
    d1 = s.get_next_delay_ms()
    d2 = s.get_next_delay_ms()
    assert d2 > d1


def test_strategy_delay_capped():
    s = ReconnectStrategy(
        initial_delay_ms=1000, backoff_factor=10.0, max_delay_ms=2000, max_attempts=5
    )
    for _ in range(5):
        d = s.get_next_delay_ms()
        assert d <= 2000


def test_strategy_reset():
    s = ReconnectStrategy(max_attempts=3)
    s.attempt_count = 3
    s.reset()
    assert s.attempt_count == 0
    assert s.should_retry()


def test_retry_service_success():
    calls = []

    def reconnect():
        calls.append(1)
        return True  # succeed on first try

    svc = ConnectionRetryService(max_attempts=3, initial_delay_ms=1)
    result = svc.attempt_reconnect(reconnect)
    assert result is True
    assert len(calls) == 1


def test_retry_service_failure():
    svc = ConnectionRetryService(max_attempts=2, initial_delay_ms=1)
    result = svc.attempt_reconnect(lambda: False)
    assert result is False


def test_retry_service_status_callback():
    messages = []
    svc = ConnectionRetryService(max_attempts=2, initial_delay_ms=1)
    svc.attempt_reconnect(
        lambda: False,
        status_callback=lambda msg, color: messages.append((msg, color)),
    )
    assert any("fehlgeschlagen" in m[0].lower() for m in messages)


def test_retry_service_abort_flag():
    aborted = [False]

    def abort():
        aborted[0] = True
        return True

    svc = ConnectionRetryService(max_attempts=5, initial_delay_ms=1)
    result = svc.attempt_reconnect(lambda: False, abort_flag=abort)
    assert result is False
