#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional
from tempfile import gettempdir
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QApplication,
    QDialog,
    QDialogButtonBox,
)
from serial.tools import list_ports
from ...pyqt.ui_connection import Ui_Dialog as Ui_Connection
from ...helper_classes_compat import AlertWindow
from ...infrastructure.logging import Debug
from ...infrastructure.device_manager import DeviceManager


class ConnectionWindow(QDialog):
    """
    A dialog window for managing device connections.

    This window allows the user to select and connect to available devices
    or a mock device (in demo mode).
    It provides a user interface for listing serial ports, refreshing the list,
    and displaying port descriptions.
    The window supports a demo mode for demonstration purposes,
    which uses a mock virtual port if available.

    Attributes:
        device_manager (DeviceManager): Manages device connections and statuses.
        connection_successful (bool): Indicates if a connection was successfully established.
        default_device (str): The default device to connect to.
        ports (list): List of available ports, including mock port if in demo mode.
        demo_mode (bool): Whether the window is operating in demo mode.
        ui (Ui_Connection): The UI object for the connection window.
        combo (QComboBox): The combo box widget for selecting serial ports.

    Methods:
        __init__: Initializes the connection window and sets up the UI.
        check_mock_port: Checks if a mock virtual port is available for demo mode.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        demo_mode: bool = False,
        default_device: str = "None",
    ):
        """
        Initializes the connection window.

        Args:
            parent (QWidget, optional): Parent widget for the dialog. Defaults to None.
            demo_mode (bool, optional): If True, uses a mock port for demonstration purposes.
            default_device (str, optional): The default device to connect to. Defaults to "None".
        """
        self.device_manager = DeviceManager()
        # Connect status_update signal to our status_message slot
        self.device_manager.status_update.connect(self.status_message)
        self.connection_successful = False
        self.default_device = default_device
        self.ports = []  # List to hold available ports

        # Check if demo mode is active and mock port is available
        mock_port = self.check_mock_port()
        self.demo_mode = demo_mode and mock_port is not None
        Debug.debug(f"Demo mode is {'enabled' if self.demo_mode else 'disabled'}")
        if self.demo_mode:
            self.ports.append(
                [mock_port, "Mock Device", "Virtual device for demonstration purposes"]
            )

        # Initialize parent and connection windows
        super().__init__(parent)
        self.ui = Ui_Connection()
        self.ui.setupUi(self)
        self.combo = self.ui.comboSerial  # Use the combo box from the UI
        self._update_ports()  # Initialize available ports

        # Attach functions to UI elements
        self.ui.buttonRefreshSerial.clicked.connect(self._update_ports)
        self.combo.currentIndexChanged.connect(self._update_port_description)

        # Initialize status message to show that the widget is ready
        self.status_message("Ready to connect...", "white")

    def check_mock_port(self) -> str | None:
        """
        Checks if the mock virtual port is available.
        Returns:
            str: The mock port name if available, otherwise None.
        """
        path = os.path.join(gettempdir(), "virtual_serial_port.txt")
        Debug.debug(f"Checking for mock port at: {path}")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                port = f.read().strip()
                Debug.debug(f"Mock port found: {port}")
                return port
        return None

    def status_message(self, message, color="white"):
        """
        Updates the status message in the connection dialog.
        """
        try:
            # Debug: Print to console to verify the method is called
            Debug.debug(f"Status message: {message} (color: {color})")

            # Check if the UI element exists
            if hasattr(self.ui, "status_msg") and self.ui.status_msg is not None:
                self.ui.status_msg.setText(message)
                self.ui.status_msg.setStyleSheet(f"color: {color};")

                # Force UI update
                QApplication.processEvents()  # Process events to update UI immediately
                self.ui.status_msg.repaint()  # Force repaint to ensure message is shown

                Debug.debug(f"Status message set successfully: '{message}'")
            else:
                Debug.error("Status message widget (status_msg) not found in UI")

        except Exception as e:
            Debug.error(f"Failed to set status message: {e}")

    def _get_port_info(self, port) -> dict:
        """
        Extract detailed port information, with fallbacks for Windows.

        On Windows, pyserial sometimes returns limited information.
        This method tries multiple attributes to get the best available info.

        Args:
            port: A serial port object from list_ports.comports()

        Returns:
            dict: Dictionary with 'device', 'name', 'description', 'hwid', 'manufacturer'
        """
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

        # Fallback: If description is empty or "n/a", try to build from other fields
        if not info["description"] or info["description"] == "n/a":
            # Try product name first
            if info["product"]:
                info["description"] = info["product"]
            # Then manufacturer
            elif info["manufacturer"]:
                info["description"] = info["manufacturer"]
            # Try VID:PID as last resort
            elif info["vid"] is not None and info["pid"] is not None:
                info["description"] = (
                    f"USB Device (VID:{info['vid']:04X} PID:{info['pid']:04X})"
                )
            # Use HWID if available
            elif info["hwid"]:
                info["description"] = info["hwid"]

        # If name is empty, use last part of device path
        if not info["name"]:
            info["name"] = info["device"].split("/")[-1].split("\\")[-1]

        return info

    def _update_ports(self):
        """
        Initializes and updates the available serial ports.
        """
        # Clear existing ports
        self.ui.comboSerial.clear()
        for field in [self.ui.device_name, self.ui.device_address, self.ui.device_desc]:
            field.clear()
        if self.demo_mode:
            self.ports = self.ports[:1]  # Clear all but the mock port
        else:
            self.ports = []

        Debug.info(f"Resetting available ports to {self.ports}")

        # Get available ports
        ports = list_ports.comports()
        arduino_index = -1  # Index if the default device is found

        for i, port in enumerate(ports):
            port_info = self._get_port_info(port)
            Debug.debug(
                f"Found port: {port_info['device']} - {port_info['description']}"
            )
            self.ports.append(
                [port_info["device"], port_info["name"], port_info["description"]]
            )  # Store port info for later use
            # Check if the port matches the default device
            if self.default_device in port_info["description"] and arduino_index == -1:
                arduino_index = i + int(self.demo_mode)

        Debug.debug(f"Available ports updated: {self.ports}")
        # Add ports to the combo box
        for port in self.ports:
            self.combo.addItem(port[0], port[2])

        # Setze Arduino-Port als vorausgewählt, wenn gefunden
        if arduino_index != -1:
            self.combo.setCurrentIndex(arduino_index)
            self._update_port_description()

    def _update_port_description(self):
        """
        Updates the port description based on the selected port.
        """
        index = self.combo.currentIndex()
        if index >= 0:
            port = self.ports[index]
            device = port[1]
            description = port[2]
            address = port[0]
        # If no valid index, clear the fields
        else:
            device = ""
            address = ""
            description = ""

        self.ui.device_name.setText(device)
        self.ui.device_address.setText(address)
        self.ui.device_desc.setText(description)

    def attempt_connection(self):
        """
        Attempts to connect to the selected device.

        Returns:
            tuple: (success, device_manager) - success is a boolean, device_manager is the
                  configured DeviceManager if successful, None otherwise.
        """
        port = self.combo.currentText()
        baudrate = int(self.ui.comboBox.currentText())

        # Show connecting message and give UI time to update
        self.status_message(f"Connecting to {port}...", "orange")
        Debug.info(f"Attempting to connect to port: {port}")

        # Give UI time to show the message
        QApplication.processEvents()

        # Check if connected
        success = self.device_manager.connect_device(port, baudrate)

        if success:
            self.status_message(f"Successfully connected to {port}", "darkgreen")
            Debug.info(f"Successfully connected to port: {port}")
            self.connection_successful = True
            return True, self.device_manager
        else:
            self.status_message(f"Failed to connect to {port}", "red")
            Debug.error(f"Failed to connect to port: {port}")
            # Give time to show error message
            QApplication.processEvents()
            self.connection_successful = False
            return False, None

    def accept(self):
        """
        Called when the user clicks OK. Attempts connection before accepting.
        """
        success, _ = self.attempt_connection()

        if success:
            return super().accept()
        Debug.error(f"Connection attempt failed for port: {self.combo.currentText()}")

        # Show error dialog with retry options
        error_msg = f"Failed to connect to {self.combo.currentText()}"
        alert = AlertWindow(
            self,
            message=f"{error_msg}\n\nPlease check if the device is connected properly and try again.",
            title="Connection Error",
            buttons=[
                ("Retry", QDialogButtonBox.ButtonRole.ResetRole),
                ("Select Another Port", QDialogButtonBox.ButtonRole.ActionRole),
                ("Cancel", QDialogButtonBox.ButtonRole.RejectRole),
            ],
        )

        result = alert.exec()

        role = alert.get_clicked_role()
        Debug.debug(f"Alert dialog result: {result}, role: {role}")
        if (
            role == QDialogButtonBox.ButtonRole.RejectRole
            or result == QDialog.DialogCode.Rejected
        ):
            Debug.info("User canceled connection attempt")
            return super().reject()

        if role == QDialogButtonBox.ButtonRole.ActionRole:
            Debug.info("User chose to select another port")
            return False  # Dialog remains open for port selection

        if role == QDialogButtonBox.ButtonRole.ResetRole:
            Debug.info(f"Retrying connection with port: {self.combo.currentText()}")
            return self.accept()  # Recursive call

        # Fallback, if no role matched
        Debug.error("No valid role selected, rejecting dialog")
        return False
