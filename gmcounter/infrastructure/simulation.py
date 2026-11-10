# Layer: infrastructure — simulated GM counter for ``--simulate``.

"""A ``MockGMCounter`` served on a pseudo-terminal, so the real adapter can connect to it.

The mocks are not part of the release wheel, so they are imported only when a simulation is
started; :func:`simulation_available` tells whether that is possible.
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
import time
from importlib.util import find_spec
from typing import Any

_log = logging.getLogger(__name__)

START_TIMEOUT_S = 5.0
STOP_TIMEOUT_S = 2.0


def simulation_available() -> bool:
    """Whether ``--simulate`` can run: the mocks are installed and the OS has pseudo-terminals."""
    return (
        find_spec("gmcounter.infrastructure.mocks") is not None
        and find_spec("termios") is not None  # pty needs termios (not on Windows)
    )


class SimulatedCounter:
    """Runs ``run_pty_server`` with a ``MockGMCounter`` in a daemon thread.

    ``start()`` returns the pseudo-terminal path; connect to it like to a serial port.
    ``device_kwargs`` go to ``MockGMCounter`` (e.g. ``pulse_interval_us`` for a fixed rate).
    """

    def __init__(self, **device_kwargs: Any) -> None:
        self._device_kwargs = device_kwargs
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._port_file = os.path.join(
            tempfile.gettempdir(), f"gmcounter_sim_{os.getpid()}_{id(self)}.txt"
        )
        self.port: str | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, timeout_s: float = START_TIMEOUT_S) -> str:
        """Start the mock server and wait for its port; returns the port path."""
        if self.running and self.port:
            return self.port
        # Imported here: the release wheel leaves out infrastructure.mocks.
        from .mocks.mock_gm_counter import MockGMCounter, run_pty_server

        if os.path.exists(self._port_file):
            os.remove(self._port_file)
        self._stop.clear()
        self._thread = threading.Thread(
            target=run_pty_server,
            kwargs={
                "device_class": MockGMCounter,
                "stop_event": self._stop,
                "port_file": self._port_file,
                **self._device_kwargs,
            },
            name="gmcounter-simulation",
            daemon=True,
        )
        self._thread.start()

        deadline = time.monotonic() + timeout_s
        while not os.path.exists(self._port_file):
            if time.monotonic() > deadline or not self._thread.is_alive():
                self.stop()
                raise RuntimeError("simulated GM counter did not start")
            time.sleep(0.02)
        with open(self._port_file, encoding="utf-8") as fh:
            self.port = fh.read().strip()
        if not self.port:
            self.stop()
            raise RuntimeError("simulated GM counter reported no port")
        _log.info("Simulated GM counter on %s", self.port)
        return self.port

    def stop(self) -> None:
        """Stop the server thread (it removes its port file)."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=STOP_TIMEOUT_S)
        self._thread = None
        self.port = None
