"""GMCounter - main program of the Geiger-Mueller counter GUI application.

Flags:
    --profile   UI profile of the main window (expert or student); default:
                ``application.profile`` of config.json. The toolbar can switch it at run time.
    --simulate  Run on a simulated GM counter (mock on a pseudo-terminal, no hardware needed).

The window opens directly; the device is connected in its connection panel.
"""

import argparse
import logging
import sys
import os

from PySide6.QtCore import (
    qInstallMessageHandler,
    QtMsgType,
)  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module

from .infrastructure.logging import Debug
from .infrastructure.simulation import simulation_available
from .ui.launcher import Launcher
from .infrastructure.config import import_config

_qt_log = logging.getLogger("gmcounter.qt")


def _qt_message_handler(mode, _context, message: str) -> None:
    if mode == QtMsgType.QtWarningMsg:
        _qt_log.warning("Qt: %s", message)
    elif mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        _qt_log.error("Qt: %s", message)
    # QtDebugMsg / QtInfoMsg are too verbose — suppress


# from .ui.resources.stylesheet import apply_stylesheet

# If executed as a script (package context missing), ensure the repo root is on
# sys.path and set __package__ so relative imports below work correctly.
if __package__ is None:
    # src/ is the package directory; parent is repository root
    package_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(package_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    # define package name to allow relative imports
    __package__ = "src"


# Load the configuration file
CONFIG = import_config()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    ``--profile`` selects an entry of the ``profiles`` config section, ``--simulate`` runs
    on the simulated counter.
    """
    parser = argparse.ArgumentParser(prog="gmcounter")
    parser.add_argument(
        "--profile",
        choices=sorted(CONFIG.get("profiles", {}) or ["expert"]),
        default=None,
        help="UI profile (default: application.profile from config.json)",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="run on a simulated GM counter (no hardware needed)",
    )
    args, _unknown = parser.parse_known_args(argv)  # Qt options pass through
    if args.simulate and not simulation_available():
        parser.error(
            "--simulate needs the mock devices (not in the release wheel; use a source "
            "checkout with pip install -e .) and pseudo-terminals (not on Windows)"
        )
    return args


def main():
    """Application entry point.

    Initialises the debug system and opens the main window; the user connects the device in
    the window's connection panel.
    """
    args = parse_args()
    # Initialise the debug system
    match CONFIG["debug"]["level_default"]:
        case "verbose":
            debug_level = Debug.DEBUG_VERBOSE
        case "info":
            debug_level = Debug.DEBUG_INFO
        case "error":
            debug_level = Debug.DEBUG_ERROR
        case _:
            debug_level = Debug.DEBUG_OFF

    Debug.init(debug_level=debug_level, app_name=CONFIG["application"]["name"])

    # Redirect Qt's own warning/error messages into our log file
    qInstallMessageHandler(_qt_message_handler)

    # Register the global exception handler
    sys.excepthook = Debug.exception_hook

    Debug.info(f"Starting application (simulate={args.simulate})...")

    # Create the QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # The launcher builds the main window for the profile and can rebuild it on a profile
    # switch, keeping the device manager (and its connection).
    launcher = Launcher(profile=args.profile, simulate=args.simulate, parent=app)
    app.aboutToQuit.connect(launcher.shutdown)
    launcher.start()  # application.window_mode
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
