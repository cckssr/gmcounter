#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GMCounter - Hauptprogramm für die Geiger-Müller Counter GUI-Anwendung.
"""


import sys
import os

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)
from .debug_utils import Debug
from .connection import ConnectionWindow
from .main_window import MainWindow
from .helper_classes import import_config

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


# Konfigurationsdatei laden
CONFIG = import_config()


def main():
    """
    Haupteinstiegspunkt der Anwendung.
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

    # Globalen Exception-Handler registrieren
    sys.excepthook = Debug.exception_hook

    Debug.info("Starte Anwendung...")

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

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
            main_window.show()

            # Timer starten, wenn vorhanden
            if hasattr(main_window, "timer"):
                main_window.timer.start()

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
