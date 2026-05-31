#!/usr/bin/env python3
# Layer: ui/dialogs — ConnectionDialog.
# Port enumeration, baud select, refresh, demo-mode mock port, AlertDialog retry.

import logging
import os
from tempfile import gettempdir
from typing import Optional

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QDialogButtonBox,
    QWidget,
)
from serial.tools import list_ports

from ...infrastructure.config import import_config
from ...infrastructure.device_manager import DeviceManager
from ...infrastructure.mocks.mock_gm_counter import MockGMCounter
from ...pyqt.ui_connection import Ui_Dialog as Ui_Connection
from ...helper_classes_compat import AlertWindow

_log = logging.getLogger(__name__)
CONFIG = import_config()


class ConnectionWindow(QDialog):
    """Startup connection dialog.

    Lets the user pick a serial port and baud rate; optionally uses the
    mock PTY port if demo_mode is enabled and a port file exists.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        demo_mode: bool = False,
        default_device: str = "None",
        measurement_state=None,
    ) -> None:
        # Build a fresh Qt-free DeviceManager
        self.device_manager = DeviceManager(measurement_state=measurement_state)
        # Wire status callback to our label
        self.device_manager.on_status = lambda msg, col: self.status_message(msg, col)

        self.connection_successful = False
        self.default_device = default_device
        self.ports: list[list[str]] = []

        mock_port = self._check_mock_port()
        self.demo_mode = demo_mode and mock_port is not None
        if self.demo_mode and mock_port:
            self.ports.append(
                [mock_port, "Mock Device", "Virtual device for demonstration"]
            )
            _log.debug("Demo mode enabled: %s", mock_port)

        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self.combo = self.ui.comboSerial
        self._update_ports()

        self.ui.buttonRefreshSerial.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)
        self.status_message("Bereit zur Verbindung...", "white")

    # ------------------------------------------------------------------
    # Helpers

    def _check_mock_port(self) -> Optional[str]:
        path = os.path.join(gettempdir(), "virtual_serial_port.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read().strip() or None
        return None

    def status_message(self, message: str, color: str = "white") -> None:
        try:
            if hasattr(self.ui, "status_msg") and self.ui.status_msg is not None:
                self.ui.status_msg.setText(message)
                self.ui.status_msg.setStyleSheet(f"color: {color};")
                QApplication.processEvents()
        except Exception as exc:
            _log.error("Failed to set status message: %s", exc)

    def _get_port_info(self, port) -> dict:
        info = {
            "device": getattr(port, "device", ""),
            "name": getattr(port, "name", ""),
            "description": getattr(port, "description", "n/a"),
            "hwid": getattr(port, "hwid", ""),
            "manufacturer": getattr(port, "manufacturer", ""),
            "product": getattr(port, "product", ""),
            "vid": getattr(port, "vid", None),
            "pid": getattr(port, "pid", None),
        }
        if not info["description"] or info["description"] == "n/a":
            if info["product"]:
                info["description"] = info["product"]
            elif info["manufacturer"]:
                info["description"] = info["manufacturer"]
            elif info["vid"] is not None and info["pid"] is not None:
                info["description"] = (
                    f"USB Device (VID:{info['vid']:04X} PID:{info['pid']:04X})"
                )
            elif info["hwid"]:
                info["description"] = info["hwid"]
        if not info["name"]:
            info["name"] = info["device"].split("/")[-1].split("\\")[-1]
        return info

    def _update_ports(self) -> None:
        self.ui.comboSerial.clear()
        for field in [self.ui.device_name, self.ui.device_address, self.ui.device_desc]:
            field.clear()

        if self.demo_mode:
            self.ports = self.ports[:1]
        else:
            self.ports = []

        ports = list_ports.comports()
        arduino_index = -1

        for port in ports:
            info = self._get_port_info(port)
            self.ports.append([info["device"], info["name"], info["description"]])
            idx = len(self.ports) - 1
            if arduino_index == -1 and (
                self.default_device == info["device"]
                or self.default_device in info["description"]
            ):
                arduino_index = idx

        for port in self.ports:
            self.combo.addItem(port[0], port[2])

        if arduino_index != -1:
            self.combo.setCurrentIndex(arduino_index)
            self._update_port_description()

    def _update_port_description(self) -> None:
        idx = self.combo.currentIndex()
        if idx >= 0 and idx < len(self.ports):
            port = self.ports[idx]
            self.ui.device_name.setText(port[1])
            self.ui.device_address.setText(port[0])
            self.ui.device_desc.setText(port[2])
        else:
            for field in [
                self.ui.device_name,
                self.ui.device_address,
                self.ui.device_desc,
            ]:
                field.clear()

    def attempt_connection(self):
        port = self.combo.currentText()
        baudrate = int(self.ui.comboBox.currentText())
        self.status_message(f"Verbinde mit {port}...", "orange")
        QApplication.processEvents()

        # Use MockGMCounter for the mock port
        is_mock = self.demo_mode and self.ports and port == self.ports[0][0]
        device_class = MockGMCounter if is_mock else None

        success = self.device_manager.connect_device(
            port, baudrate, device_class=device_class
        )
        if success:
            self.status_message(f"Verbunden mit {port}", "darkgreen")
            self.connection_successful = True
            return True, self.device_manager
        else:
            self.status_message(f"Verbindung zu {port} fehlgeschlagen", "red")
            QApplication.processEvents()
            self.connection_successful = False
            return False, None

    def accept(self) -> None:
        success, _ = self.attempt_connection()
        if success:
            return super().accept()

        alert = AlertWindow(
            self,
            message=f"Verbindung zu {self.combo.currentText()} fehlgeschlagen.\n\nBitte überprüfen Sie die Verbindung.",
            title="Verbindungsfehler",
            buttons=[
                ("Wiederholen", QDialogButtonBox.ButtonRole.ResetRole),
                ("Anderen Port wählen", QDialogButtonBox.ButtonRole.ActionRole),
                ("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole),
            ],
        )
        result = alert.exec()
        role = alert.get_clicked_role()

        if (
            role == QDialogButtonBox.ButtonRole.RejectRole
            or result == QDialog.DialogCode.Rejected
        ):
            return super().reject()
        if role == QDialogButtonBox.ButtonRole.ActionRole:
            return False  # Dialog stays open
        if role == QDialogButtonBox.ButtonRole.ResetRole:
            return self.accept()  # Recursive retry
        return False
