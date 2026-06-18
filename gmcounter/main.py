"""GMCounter - Hauptprogramm für die Geiger-Müller Counter GUI-Anwendung."""

import logging
import sys
import os

from PySide6.QtCore import qInstallMessageHandler, QtMsgType  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from .infrastructure.logging import Debug
from .ui.dialogs.connection import ConnectionWindow
from .ui.windows.main_window import MainWindow
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
# sys.path so the gmcounter package is importable.
if __package__ is None:
    package_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(package_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


# Konfigurationsdatei laden
CONFIG = import_config()


def main():
    """Haupteinstiegspunkt der Anwendung.

    Initialisiert das Debug-System, startet die Verbindungsdialog
    und erstellt das Hauptfenster.
    """
    # Debug-System initialisieren
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

    # Globalen Exception-Handler registrieren
    sys.excepthook = Debug.exception_hook

    Debug.info("Starte Anwendung...")

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Stylesheet anwenden
    # apply_stylesheet(app, CONFIG.get("ui", {}).get("theme", "dark"))
    # Debug.debug("Stylesheet angewendet")
    # Verbindungsdialog anzeigen
    connection_dialog = ConnectionWindow(
        demo_mode=CONFIG["gm_counter"]["demo_mode"],
        default_device=CONFIG["gm_counter"]["default_arduino"],
    )

    # Wenn der Dialog bestätigt wurde, Verbindung herstellen
    if connection_dialog.exec():
        success = connection_dialog.connection_successful
        device_manager = connection_dialog.device_manager

        if success and device_manager is not None:
            # Hauptfenster erstellen und anzeigen, wenn Verbindung erfolgreich
            main_window = MainWindow(device_manager)
            # MainWindow.__init__ already calls showMaximized(); no show() needed here.

            # Anwendung ausführen
            sys.exit(app.exec())
        else:
            # Fehlerfall: Verbindung fehlgeschlagen
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(CONFIG["messages"]["connection_failed"])
            msg_box.setWindowTitle("Verbindungsfehler")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            sys.exit(1)
    else:
        # Benutzer hat den Dialog abgebrochen
        Debug.info("Verbindung vom Benutzer abgebrochen")
        sys.exit(0)


if __name__ == "__main__":
    main()
