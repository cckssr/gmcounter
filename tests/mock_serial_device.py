"""Standalone PTY mock server for manual testing.

Delegates to infrastructure/mocks/mock_gm_counter.py which implements the
current SCPI command set and correct binary packet format.

Usage:
    python tests/mock_serial_device.py [--max-tick SECONDS]

The slave PTY path is written to /tmp/virtual_serial_port.txt so the app's
connection dialog finds it automatically when demo_mode is enabled.
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gmcounter.infrastructure.mocks.mock_gm_counter import MockGMCounter, run_pty_server

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the PTY mock GM counter.")
    parser.add_argument(
        "--max-tick",
        type=float,
        default=1.0,
        help="Maximum inter-pulse interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--pulse-interval-us",
        type=int,
        default=None,
        help="Fixed inter-pulse interval in µs for deterministic output (optional)",
    )
    args = parser.parse_args()

    class ConfiguredMock(MockGMCounter):
        def __init__(self, port: str, **kwargs):
            super().__init__(
                port=port,
                max_tick=args.max_tick,
                pulse_interval_us=args.pulse_interval_us,
            )

    print("Starting PTY mock server. Press Ctrl-C to stop.")
    run_pty_server(device_class=ConfiguredMock)


if __name__ == "__main__":
    main()
