#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit-Tests für die ConnectionWindow-Klasse.

Dieser Test testet das Connection Window, das für die Verbindung mit seriellen Geräten
und Mock-Geräten (Demo-Modus) zuständig ist.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import pytest

# Pfad zum Projektverzeichnis hinzufügen für lokale Imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Qt-Abhängigkeiten überprüfen
pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox
from PySide6.QtCore import Qt, QTimer

from src.connection import ConnectionWindow
from src.device_manager import DeviceManager
from src.helper_classes import AlertWindow


class TestConnectionWindow(unittest.TestCase):
    """Testfälle für das ConnectionWindow."""

    @classmethod
    def setUpClass(cls):
        """Einmalige Einrichtung für alle Tests."""
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Testumgebung für jeden Test einrichten."""
        # Mock für externe Abhängigkeiten
        self.list_ports_patcher = patch("src.connection.list_ports")
        self.debug_patcher = patch("src.connection.Debug")
        self.device_manager_patcher = patch("src.connection.DeviceManager")
        self.alert_window_patcher = patch("src.connection.AlertWindow")

        self.mock_list_ports = self.list_ports_patcher.start()
        self.mock_debug = self.debug_patcher.start()
        self.mock_device_manager_class = self.device_manager_patcher.start()
        self.mock_alert_window = self.alert_window_patcher.start()

        # Mock für list_ports.comports()
        self.mock_port1 = Mock()
        self.mock_port1.device = "/dev/ttyUSB0"
        self.mock_port1.name = "USB0"
        self.mock_port1.description = "Arduino Uno"

        self.mock_port2 = Mock()
        self.mock_port2.device = "/dev/ttyUSB1"
        self.mock_port2.name = "USB1"
        self.mock_port2.description = "Generic Serial Device"

        self.mock_list_ports.comports.return_value = [self.mock_port1, self.mock_port2]

        # Mock für DeviceManager
        self.mock_device_manager = Mock(spec=DeviceManager)
        self.mock_device_manager_class.return_value = self.mock_device_manager

    def tearDown(self):
        """Testumgebung nach jedem Test aufräumen."""
        self.list_ports_patcher.stop()
        self.debug_patcher.stop()
        self.device_manager_patcher.stop()
        self.alert_window_patcher.stop()

    def test_initialization_normal_mode(self):
        """Test der normalen Initialisierung ohne Demo-Modus."""
        connection_window = ConnectionWindow()

        # Überprüfen, dass DeviceManager erstellt wurde
        self.mock_device_manager_class.assert_called_once_with(
            status_callback=connection_window.status_message
        )

        # Überprüfen der Grundeinstellungen
        self.assertFalse(connection_window.demo_mode)
        self.assertFalse(connection_window.connection_successful)
        self.assertEqual(connection_window.default_device, "None")

        # Überprüfen, dass Ports aktualisiert wurden
        self.mock_list_ports.comports.assert_called()

        connection_window.close()

    def test_initialization_demo_mode_without_mock_port(self):
        """Test der Initialisierung im Demo-Modus ohne verfügbaren Mock-Port."""
        with patch.object(ConnectionWindow, "check_mock_port", return_value=None):
            connection_window = ConnectionWindow(demo_mode=True)

            # Demo-Modus sollte deaktiviert sein, da kein Mock-Port verfügbar
            self.assertFalse(connection_window.demo_mode)

            connection_window.close()

    def test_initialization_demo_mode_with_mock_port(self):
        """Test der Initialisierung im Demo-Modus mit verfügbarem Mock-Port."""
        mock_port = "/tmp/mock_serial_port"

        with patch.object(ConnectionWindow, "check_mock_port", return_value=mock_port):
            connection_window = ConnectionWindow(demo_mode=True)

            # Demo-Modus sollte aktiviert sein
            self.assertTrue(connection_window.demo_mode)

            # Mock-Port sollte in der Portliste stehen
            self.assertEqual(len(connection_window.ports), 3)  # 2 echte + 1 Mock
            self.assertEqual(connection_window.ports[0][0], mock_port)
            self.assertEqual(connection_window.ports[0][1], "Mock Device")

            connection_window.close()

    def test_check_mock_port_exists(self):
        """Test für check_mock_port wenn der Mock-Port existiert."""
        mock_port_content = "/tmp/virtual_serial_port"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(mock_port_content)
            temp_file_path = temp_file.name

        try:
            with patch("src.connection.os.path.join", return_value=temp_file_path):
                connection_window = ConnectionWindow()
                result = connection_window.check_mock_port()
                self.assertEqual(result, mock_port_content)
                connection_window.close()
        finally:
            os.unlink(temp_file_path)

    def test_check_mock_port_not_exists(self):
        """Test für check_mock_port wenn der Mock-Port nicht existiert."""
        with patch("src.connection.os.path.exists", return_value=False):
            connection_window = ConnectionWindow()
            result = connection_window.check_mock_port()
            self.assertIsNone(result)
            connection_window.close()

    def test_update_ports(self):
        """Test der _update_ports Methode."""
        connection_window = ConnectionWindow()

        # Ports sollten korrekt geladen werden
        self.assertEqual(len(connection_window.ports), 2)
        self.assertEqual(connection_window.ports[0][0], "/dev/ttyUSB0")
        self.assertEqual(connection_window.ports[1][0], "/dev/ttyUSB1")

        # ComboBox sollte die Ports enthalten
        self.assertEqual(connection_window.combo.count(), 2)
        self.assertEqual(connection_window.combo.itemText(0), "/dev/ttyUSB0")

        connection_window.close()

    def test_update_ports_with_default_device(self):
        """Test der _update_ports Methode mit Default-Device."""
        connection_window = ConnectionWindow(default_device="Arduino Uno")

        # Arduino Uno sollte vorausgewählt sein
        self.assertEqual(connection_window.combo.currentIndex(), 0)

        connection_window.close()

    def test_update_port_description(self):
        """Test der _update_port_description Methode."""
        connection_window = ConnectionWindow()

        # Port auswählen
        connection_window.combo.setCurrentIndex(0)
        connection_window._update_port_description()

        # Überprüfen, dass die Beschreibungsfelder korrekt gesetzt wurden
        self.assertEqual(connection_window.ui.device_address.text(), "/dev/ttyUSB0")
        self.assertEqual(connection_window.ui.device_name.text(), "USB0")
        self.assertEqual(connection_window.ui.device_desc.text(), "Arduino Uno")

        connection_window.close()

    def test_attempt_connection_success(self):
        """Test einer erfolgreichen Verbindung."""
        self.mock_device_manager.connect.return_value = True

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")
        connection_window.ui.comboBox.setCurrentText("9600")

        success, device_manager = connection_window.attempt_connection()

        # Überprüfen der erfolgreichen Verbindung
        self.assertTrue(success)
        self.assertTrue(connection_window.connection_successful)
        self.assertEqual(device_manager, self.mock_device_manager)

        # Überprüfen, dass connect mit korrekten Parametern aufgerufen wurde
        self.mock_device_manager.connect.assert_called_once_with("/dev/ttyUSB0", 9600)

        connection_window.close()

    def test_attempt_connection_failure(self):
        """Test einer fehlgeschlagenen Verbindung."""
        self.mock_device_manager.connect.return_value = False

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")
        connection_window.ui.comboBox.setCurrentText("9600")

        success, device_manager = connection_window.attempt_connection()

        # Überprüfen der fehlgeschlagenen Verbindung
        self.assertFalse(success)
        self.assertFalse(connection_window.connection_successful)
        self.assertIsNone(device_manager)

        connection_window.close()

    def test_status_message(self):
        """Test der status_message Methode."""
        connection_window = ConnectionWindow()

        connection_window.status_message("Test message", "green")

        # Überprüfen, dass die Nachricht gesetzt wurde
        self.assertEqual(connection_window.ui.status_msg.text(), "Test message")

        connection_window.close()

    def test_accept_successful_connection(self):
        """Test der accept Methode bei erfolgreicher Verbindung."""
        self.mock_device_manager.connect.return_value = True

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")

        with patch.object(
            connection_window,
            "attempt_connection",
            return_value=(True, self.mock_device_manager),
        ):
            with patch("PySide6.QtWidgets.QDialog.accept") as mock_super_accept:
                result = connection_window.accept()

                # Überprüfen, dass super().accept() aufgerufen wurde
                mock_super_accept.assert_called_once()

        connection_window.close()

    def test_accept_failed_connection_alert_creation(self):
        """Test ob AlertWindow bei fehlgeschlagener Verbindung erstellt wird."""
        # Mock für AlertWindow
        mock_alert_instance = Mock()
        mock_alert_instance.exec.return_value = QDialog.DialogCode.Rejected
        mock_alert_instance.get_clicked_role.return_value = (
            QDialogButtonBox.ButtonRole.RejectRole
        )
        self.mock_alert_window.return_value = mock_alert_instance

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")

        # Simuliere fehlgeschlagene Verbindung
        with patch.object(
            connection_window, "attempt_connection", return_value=(False, None)
        ):
            with patch("PySide6.QtWidgets.QDialog.reject") as mock_super_reject:
                result = connection_window.accept()

                # Überprüfen, dass AlertWindow erstellt wurde
                self.mock_alert_window.assert_called_once()

                # Überprüfen, dass die korrekten Parameter übergeben wurden
                call_args = self.mock_alert_window.call_args
                self.assertEqual(call_args[1]["title"], "Connection Error")
                self.assertIn(
                    "Failed to connect to /dev/ttyUSB0", call_args[1]["message"]
                )

        connection_window.close()

    def test_accept_failed_connection_cancel(self):
        """Test der accept Methode bei fehlgeschlagener Verbindung mit Cancel."""
        self.mock_device_manager.connect.return_value = False

        # Mock für AlertWindow
        mock_alert_instance = Mock()
        mock_alert_instance.exec.return_value = QDialog.DialogCode.Rejected
        mock_alert_instance.get_clicked_role.return_value = (
            QDialogButtonBox.ButtonRole.RejectRole
        )
        self.mock_alert_window.return_value = mock_alert_instance

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")

        with patch.object(
            connection_window, "attempt_connection", return_value=(False, None)
        ):
            with patch("PySide6.QtWidgets.QDialog.reject") as mock_super_reject:
                result = connection_window.accept()

                # Überprüfen, dass super().reject() aufgerufen wurde
                mock_super_reject.assert_called_once()

        connection_window.close()

    def test_accept_failed_connection_select_another_port(self):
        """Test der accept Methode bei fehlgeschlagener Verbindung mit 'Select Another Port'."""
        self.mock_device_manager.connect.return_value = False

        # Mock für AlertWindow
        mock_alert_instance = Mock()
        mock_alert_instance.exec.return_value = QDialog.DialogCode.Accepted
        mock_alert_instance.get_clicked_role.return_value = (
            QDialogButtonBox.ButtonRole.ActionRole
        )
        self.mock_alert_window.return_value = mock_alert_instance

        connection_window = ConnectionWindow()
        connection_window.combo.setCurrentText("/dev/ttyUSB0")

        with patch.object(
            connection_window, "attempt_connection", return_value=(False, None)
        ):
            result = connection_window.accept()

            # Überprüfen, dass False zurückgegeben wird (Dialog bleibt offen)
            self.assertFalse(result)

        connection_window.close()

    def test_refresh_button_functionality(self):
        """Test der Refresh-Button Funktionalität."""
        connection_window = ConnectionWindow()

        # Neue Ports für den zweiten Aufruf
        mock_port3 = Mock()
        mock_port3.device = "/dev/ttyUSB2"
        mock_port3.name = "USB2"
        mock_port3.description = "Another Device"

        self.mock_list_ports.comports.return_value = [self.mock_port1, mock_port3]

        # Button-Click simulieren
        connection_window.ui.buttonRefreshSerial.click()

        # Überprüfen, dass die Ports aktualisiert wurden
        self.assertEqual(connection_window.combo.count(), 2)
        self.assertEqual(connection_window.combo.itemText(1), "/dev/ttyUSB2")

        connection_window.close()

    def test_combo_index_changed_signal(self):
        """Test des currentIndexChanged Signals der ComboBox."""
        connection_window = ConnectionWindow()

        # Index ändern
        connection_window.combo.setCurrentIndex(1)

        # Überprüfen, dass die Port-Beschreibung aktualisiert wurde
        self.assertEqual(connection_window.ui.device_address.text(), "/dev/ttyUSB1")
        self.assertEqual(connection_window.ui.device_name.text(), "USB1")

        connection_window.close()

    def test_port_description_with_invalid_index(self):
        """Test der Port-Beschreibung mit ungültigem Index."""
        connection_window = ConnectionWindow()

        # Ungültigen Index setzen
        connection_window.combo.setCurrentIndex(-1)
        connection_window._update_port_description()

        # Felder sollten leer sein
        self.assertEqual(connection_window.ui.device_address.text(), "")
        self.assertEqual(connection_window.ui.device_name.text(), "")
        self.assertEqual(connection_window.ui.device_desc.text(), "")

        connection_window.close()


class TestConnectionWindowIntegration(unittest.TestCase):
    """Integrationstests für das ConnectionWindow."""

    @classmethod
    def setUpClass(cls):
        """Einmalige Einrichtung für alle Tests."""
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_window_creation_and_closure(self):
        """Integration Test: Fenster erstellen und schließen."""
        with patch("src.connection.list_ports.comports", return_value=[]):
            with patch("src.connection.DeviceManager"):
                connection_window = ConnectionWindow()

                # Fenster sollte erstellt werden
                self.assertIsInstance(connection_window, ConnectionWindow)
                self.assertIsInstance(connection_window, QDialog)

                # Fenster sollte geschlossen werden können
                connection_window.close()

    def test_demo_mode_integration(self):
        """Integration Test: Demo-Modus Funktionalität."""
        mock_port = "/tmp/test_virtual_port"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(mock_port)
            temp_file_path = temp_file.name

        try:
            with patch("src.connection.list_ports.comports", return_value=[]):
                with patch("src.connection.DeviceManager"):
                    with patch(
                        "src.connection.os.path.join", return_value=temp_file_path
                    ):
                        connection_window = ConnectionWindow(demo_mode=True)

                        # Demo-Modus sollte aktiviert sein
                        self.assertTrue(connection_window.demo_mode)

                        # Mock-Port sollte verfügbar sein
                        self.assertTrue(
                            any(
                                port[0] == mock_port for port in connection_window.ports
                            )
                        )

                        connection_window.close()
        finally:
            os.unlink(temp_file_path)


def run_tests():
    """Führt alle Tests aus."""
    # Alle Testklassen sammeln
    test_classes = [
        TestConnectionWindow,
        TestConnectionWindowIntegration,
    ]

    # Test Suite erstellen
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
