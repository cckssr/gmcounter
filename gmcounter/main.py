"""GMCounter - main program of the Geiger-Mueller counter GUI application."""

import argparse
import logging
import sys
import os

from PySide6.QtCore import (
    qInstallMessageHandler,
    QtMsgType,
)  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from .infrastructure.logging import Debug
from .ui.dialogs.connection import ConnectionWindow
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
    """Command line: ``--profile`` selects an entry of the ``profiles`` config section."""
    parser = argparse.ArgumentParser(prog="gmcounter")
    parser.add_argument(
        "--profile",
        choices=sorted(CONFIG.get("profiles", {}) or ["expert"]),
        default=None,
        help="UI profile (default: application.profile from config.json)",
    )
    args, _unknown = parser.parse_known_args(argv)  # Qt options pass through
    return args


def main():
    """Application entry point.

    Initialises the debug system, shows the connection dialog and creates the main window.
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

    Debug.info("Starting application...")

    # Create the QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Show the connection dialog
    connection_dialog = ConnectionWindow(
        demo_mode=CONFIG["gm_counter"]["demo_mode"],
        default_device=CONFIG["gm_counter"]["default_arduino"],
    )

    # Dialog accepted: the connection has been tried
    if connection_dialog.exec():
        success = connection_dialog.connection_successful
        device_manager = connection_dialog.device_manager

        if success and device_manager is not None:
            # Connected: the launcher builds the main window for the profile and can
            # rebuild it on a profile switch, keeping this device manager connected.
            launcher = Launcher(device_manager, profile=args.profile)
            launcher.start()  # application.window_mode
            sys.exit(app.exec())
        else:
            # Connection failed
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(CONFIG["messages"]["connection_failed"])
            msg_box.setWindowTitle(CONFIG["messages"]["title_connection_error"])
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            sys.exit(1)
    else:
        # The user cancelled the dialog
        Debug.info("Connection cancelled by the user")
        sys.exit(0)


if __name__ == "__main__":
    main()
