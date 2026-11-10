"""DeviceManager.connect_device: a port that opens but does not answer *IDN? is not connected."""

from __future__ import annotations

from gmcounter.infrastructure.device_manager import DeviceManager


class FakeDevice:
    """Minimal device whose ``*IDN?`` replies are scripted."""

    def __init__(self, replies, **_kwargs) -> None:
        self.replies = list(replies)
        self.closed = False
        self.queries = 0

    def get_information(self, use_cache: bool = True) -> dict:
        self.queries += 1
        return self.replies.pop(0) if self.replies else {}

    def close(self) -> None:
        self.closed = True


GOOD = {"copyright": "TU Berlin", "version": "2.3.1", "openbis": "E34250"}
SILENT = {"copyright": "", "version": "", "openbis": ""}


def _connect(replies):
    manager = DeviceManager()
    statuses: list[tuple[str, str]] = []
    infos: list[dict] = []
    manager.on_status = lambda text, colour: statuses.append((text, colour))
    manager.on_device_info = infos.append
    created: list[FakeDevice] = []

    def device_class(**kwargs):
        created.append(FakeDevice(replies, **kwargs))
        return created[-1]

    ok = manager.connect_device("/dev/test", 1_000_000, device_class=device_class)
    return manager, ok, statuses, infos, created


def test_a_device_that_identifies_itself_is_connected():
    manager, ok, statuses, infos, _created = _connect([GOOD])
    assert ok and manager.connected and manager.device is not None
    assert infos == [GOOD]
    assert statuses[-1][1] == "green"


def test_a_silent_device_is_rejected_and_closed():
    manager, ok, statuses, infos, created = _connect([SILENT, SILENT])
    assert not ok
    assert not manager.connected and manager.device is None
    assert created[0].closed
    assert infos == []
    assert statuses[-1][1] == "red"
    assert all(colour != "green" for _text, colour in statuses)


def test_one_slow_idn_reply_is_retried():
    manager, ok, _statuses, infos, created = _connect([SILENT, GOOD])
    assert ok and manager.connected
    assert created[0].queries == 2
    assert infos == [GOOD]
