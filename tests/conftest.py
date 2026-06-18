"""Project-wide pytest fixtures and CLI options."""

import os
import tempfile
import threading
import time

import pytest

# Ensure Qt uses the offscreen platform so tests never need a display server.
# This runs before any test module is imported (and therefore before any
# QApplication is constructed), making it effective in VSCode, CLI, and CI.
# Honour QT_QPA_PLATFORM if the caller has already set it explicitly.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_addoption(parser):
    parser.addoption(
        "--port",
        default=None,
        metavar="PORT",
        help="Serial port for hardware tests (e.g. /dev/tty.usbserial-XXXX)",
    )
    parser.addoption(
        "--baudrate",
        default=1000000,
        type=int,
        metavar="BAUD",
        help="Baud rate for hardware tests (default 1000000)",
    )


@pytest.fixture(scope="session")
def hw_port(request):
    """Serial port for hardware-only tests; skips if --port not given."""
    port = request.config.getoption("--port")
    if port is None:
        pytest.skip(
            "No --port specified; pass --port /dev/tty... to run hardware tests"
        )
    return port


@pytest.fixture(scope="session")
def hw_baudrate(request):
    return int(request.config.getoption("--baudrate"))


@pytest.fixture
def gm_adapter(request):
    """Yield a connected GMCounterAdapter.

    Uses real hardware if --port is given; otherwise starts a MockGMCounter
    PTY server and connects to it via GMCounterAdapter (Unix only).
    """
    port = request.config.getoption("--port")
    baudrate = int(request.config.getoption("--baudrate"))

    if port:
        from gmcounter.infrastructure.devices.gm_counter import GMCounterAdapter

        dev = GMCounterAdapter(port=port, baudrate=baudrate)
        yield dev
        try:
            dev.set_counting(False)
        except Exception:
            pass
        dev.close()
        return

    # No hardware — start MockGMCounter PTY server (Unix only).
    try:
        import pty  # noqa: F401
    except ImportError:
        pytest.skip(
            "PTY-based mock requires Unix; pass --port to test on real hardware"
        )

    from gmcounter.infrastructure.mocks.mock_gm_counter import (
        MockGMCounter,
        run_pty_server,
    )
    from gmcounter.infrastructure.devices.gm_counter import GMCounterAdapter

    # Use a unique port file per fixture invocation to prevent races between
    # sequential tests that each start their own PTY server.
    port_file = os.path.join(
        tempfile.gettempdir(), f"gm_pty_{os.getpid()}_{id(request)}.txt"
    )
    if os.path.exists(port_file):
        os.remove(port_file)

    stop = threading.Event()
    server = threading.Thread(
        target=run_pty_server,
        kwargs={
            "device_class": MockGMCounter,
            "stop_event": stop,
            "port_file": port_file,
        },
        daemon=True,
    )
    server.start()

    deadline = time.time() + 5.0
    while not os.path.exists(port_file):
        if time.time() > deadline:
            stop.set()
            pytest.fail("MockGMCounter PTY server did not start within 5 s")
        time.sleep(0.05)

    with open(port_file) as fh:
        pty_port = fh.read().strip()

    if not pty_port:
        stop.set()
        pytest.fail(f"MockGMCounter PTY server wrote empty port path to {port_file}")

    dev = GMCounterAdapter(port=pty_port, baudrate=9600)

    yield dev

    try:
        dev.set_counting(False)
    except Exception:
        pass
    dev.close()
    stop.set()
    server.join(timeout=2.0)
