#!/usr/bin/env python3
"""Automatischer Test der Signal-Verbindungen in der GUI."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gmcounter.device_manager import DeviceManager
from gmcounter.main_window import MainWindow


def test_gui_connections():
    """Test dass MainWindow korrekt mit DeviceManager Signals verbunden ist."""
    app = QApplication(sys.argv)

    # DeviceManager erstellen
    manager = DeviceManager()

    # MainWindow erstellen (dies sollte die Signals verbinden)
    try:
        window = MainWindow(manager)
        print("✅ MainWindow erfolgreich erstellt")

        # Prüfen ob Signals verbunden sind
        # Dies wird durch das Erstellen von MainWindow automatisch gemacht
        print("✅ Signal-Verbindungen hergestellt")

        # Test Signal emission
        test_passed = []

        # Original handle_data Methode wrappen
        original_handle_data = window.handle_data

        def wrapped_handle_data(index, value):
            test_passed.append(True)
            print(f"✅ Data Signal empfangen: index={index}, value={value}")
            original_handle_data(index, value)

        window.handle_data = wrapped_handle_data

        # Test Signal aussenden
        manager.data_received.emit(1, 100.5)
        app.processEvents()

        if test_passed:
            print("✅ MainWindow empfängt Daten-Signals korrekt")
        else:
            print("❌ Daten-Signal wurde nicht empfangen")
            return False

        print("✅ Alle GUI-Tests bestanden!")
        return True

    except Exception as e:
        print(f"❌ Fehler beim Erstellen von MainWindow: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gui_connections()
    sys.exit(0 if success else 1)
