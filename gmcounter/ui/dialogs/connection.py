#!/usr/bin/env python3
# Layer: ui/dialogs — ConnectionDialog.
# Port enumeration, baud select, refresh, demo-mode mock port, retry prompt.
# All user-visible texts come from config.json (ui.connection).

import logging
import os
from tempfile import gettempdir
from typing import Optional

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)
from serial.tools import list_ports

from ...infrastructure.config import AppConfig, default_config, import_config
from ...infrastructure.device_manager import DeviceManager
from ...pyqt.ui_connection import Ui_ConnectionDialog
from ..i18n import apply_strings

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
        config: Optional[AppConfig] = None,
    ) -> None:
        self._config = config or default_config()
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
                [
                    mock_port,
                    self._text("text_mock_name"),
                    self._text("text_mock_description"),
                ]
            )
            _log.debug("Demo mode enabled: %s", mock_port)

        super().__init__(parent)
        self.ui = Ui_ConnectionDialog()
        self.ui.setupUi(self)
        apply_strings(self, self._config.section("ui").get("connection", {}))
        self._apply_button_texts()
        self.combo = self.ui.comboPort
        self._update_ports()

        self.ui.buttonRefreshPorts.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)
        self.status_message(self._text("text_ready"), "white")

    # ------------------------------------------------------------------
    # Helpers

    def _text(self, key: str, **fmt) -> str:
        """Configured German text ``ui.connection.<key>``."""
        return self._config.text(f"connection.{key}", **fmt)

    def _apply_button_texts(self) -> None:
        """Set the standard-button captions, which ``apply_strings`` cannot reach."""
        box = self.ui.buttonBox
        for standard, key in (
            (QDialogButtonBox.StandardButton.Open, "button_open"),
            (QDialogButtonBox.StandardButton.Cancel, "button_cancel"),
        ):
            button = box.button(standard)
            if button is not None:
                button.setText(self._text(key))

    def _check_mock_port(self) -> Optional[str]:
        path = os.path.join(gettempdir(), "virtual_serial_port.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read().strip() or None
        return None

    def status_message(self, message: str, color: str = "white") -> None:
        try:
            if hasattr(self.ui, "valueStatus") and self.ui.valueStatus is not None:
                self.ui.valueStatus.setText(message)
                self.ui.valueStatus.setStyleSheet(f"color: {color};")
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
        self.ui.comboPort.clear()
        for field in [self.ui.editName, self.ui.editAddress, self.ui.editDescription]:
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
            self.ui.editName.setText(port[1])
            self.ui.editAddress.setText(port[0])
            self.ui.editDescription.setText(port[2])
        else:
            for field in [
                self.ui.editName,
                self.ui.editAddress,
                self.ui.editDescription,
            ]:
                field.clear()

    def attempt_connection(self):
        port = self.combo.currentText()
        baudrate = int(self.ui.comboBaud.currentText())
        self.status_message(self._text("text_connecting", port=port), "orange")
        QApplication.processEvents()

        # The mock PTY port is served by run_pty_server() (infrastructure/mocks).
        # GMCounterAdapter (device_class=None default) speaks to it over the PTY
        # slave using the standard SCPI command set — no special device class needed.
        success = self.device_manager.connect_device(port, baudrate)
        if success:
            self.status_message(self._text("text_connected", port=port), "darkgreen")
            self.connection_successful = True
            return True, self.device_manager
        else:
            self.status_message(self._text("text_failed", port=port), "red")
            QApplication.processEvents()
            self.connection_successful = False
            return False, None

    def accept(self) -> None:
        success, _ = self.attempt_connection()
        if success:
            return super().accept()

        msg = QMessageBox(self)
        msg.setWindowTitle(self._text("text_error_title"))
        msg.setText(self._text("text_error_body", port=self.combo.currentText()))
        msg.setIcon(QMessageBox.Icon.Warning)
        retry_btn = msg.addButton(
            self._text("button_retry"), QMessageBox.ButtonRole.AcceptRole
        )
        msg.addButton(self._text("button_other_port"), QMessageBox.ButtonRole.ResetRole)
        msg.addButton(self._text("button_cancel"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked is retry_btn:
            return self.accept()  # Recursive retry
        if msg.buttonRole(clicked) == QMessageBox.ButtonRole.RejectRole:
            return super().reject()
        # "choose another port" — leave dialog open
