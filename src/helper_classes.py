import re
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Union
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QStatusBar,
    QLabel,
    QMessageBox,
    QDialog,
    QWidget,
    QDialogButtonBox,
    QFileDialog,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from src.debug_utils import Debug


class Statusbar:
    """
    A class to manage the status bar messages and styles.
    Attributes:
        statusbar (QStatusBar): The status bar widget.
        old_state (list): The previous state of the status bar.
    Methods:
        __init__(statusbar: QStatusBar):
            Initializes the Statusbar with the given QStatusBar widget.
        temp_message(message: str, backcolor: str = None, duration: int = None):
            Displays a temporary message on the status bar.
        perm_message(message: str, index: int = 0, backcolor: str = None):
            Displays a permanent message on the status bar.
        _update_statusbar_style(backcolor: str):
            Updates the style of the status bar.
        _save_state():
            Saves the current state of the status bar.
    """

    def __init__(self, statusbar: QStatusBar) -> None:
        self.statusbar = statusbar
        self.old_state: list[str] = []
        self._save_state()

    def temp_message(
        self, message: str, backcolor: str = "", duration: int = 0
    ) -> None:
        new_style = self._update_statusbar_style(backcolor)
        # set statusbar style
        self.statusbar.setStyleSheet(new_style)

        # Set new message and if duration is provided, reset after the duration elapses
        if duration != 0:
            self.statusbar.showMessage(message, duration)
            Debug.info(f"Statusbar message: {message} with duration: {duration}")
            # reset to old state after duration
            QTimer.singleShot(
                duration, lambda: self.statusbar.setStyleSheet(self.old_state[1])
            )
            QTimer.singleShot(
                duration, lambda: self.statusbar.showMessage(self.old_state[0])
            )
        else:
            self.statusbar.showMessage(message)
            Debug.info(f"Permanent Statusbar message: {message}")

    def perm_message(self, message: str, index: int = 0, backcolor: str = "") -> None:
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)
        label = QLabel()
        label.setText(message)
        self.statusbar.insertPermanentWidget(index, label)
        Debug.info(f"Permanent Statusbar message: {message} at index: {index}")

    def _update_statusbar_style(self, backcolor: str) -> str:
        # get current state
        self._save_state()

        # Set new style if backcolor is provided or keep the old style
        if backcolor:
            if "background-color:" in self.old_state[1]:
                # if old style had backcolor, replace it with the new one
                new_style = self.old_state[1].replace(
                    re.search(r"background-color:\s*[^;]+;", self.old_state[1]).group(
                        0
                    ),
                    f"background-color: {backcolor};",
                )
                Debug.info(
                    f"Statusbar background color updated: {self.old_state[1]} -> {new_style}"
                )
            else:
                # otherwise append the new backcolor
                new_style = self.old_state[1] + f"background-color: {backcolor};"
                Debug.info(f"Statusbar background color set: {new_style}")
        else:
            new_style = self.old_state[1]
            Debug.info("No background color change")
        return new_style

    def _save_state(self):
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]


class AlertWindow(QDialog):
    """
    Initializes the alert window with customizable buttons and messages.
    Provides tracking for which button was clicked.
    """

    def __init__(
        self,
        parent: QWidget,
        message: str = "Alert",
        title: str = "Warning",
        buttons=None,
    ) -> None:
        super().__init__(parent)
        try:
            from pyqt.ui_alert import (
                Ui_Dialog,
            )  # local import to avoid Qt dependency when unused
        except Exception:  # pragma: no cover - fallback
            Ui_Dialog = object  # type: ignore
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(title)

        # Speichert den zuletzt geklickten Button
        self.clicked_button = None
        self.clicked_role = None
        self.clicked_text = None

        # Set message im TextBox-Label
        if hasattr(self.ui, "textBox"):
            self.ui.textBox.setText(message)

        # Configure buttons if provided
        if buttons and hasattr(self.ui, "buttonBox"):
            # Bestehende Signalverbindungen sichern
            old_accepted = None
            old_rejected = None

            if hasattr(self.ui.buttonBox, "accepted") and hasattr(
                self.ui.buttonBox.accepted, "connect"
            ):
                old_accepted = self.ui.buttonBox.accepted
                try:
                    self.ui.buttonBox.accepted.disconnect()
                except:
                    pass

            if hasattr(self.ui.buttonBox, "rejected") and hasattr(
                self.ui.buttonBox.rejected, "connect"
            ):
                old_rejected = self.ui.buttonBox.rejected
                try:
                    self.ui.buttonBox.rejected.disconnect()
                except:
                    pass

            # Bestehende Buttons löschen
            self.ui.buttonBox.clear()

            # Neue Buttons hinzufügen und mit Callbacks verbinden
            for button_text, role in buttons:
                button = self.ui.buttonBox.addButton(button_text, role)
                # Button-Klick-Handler hinzufügen
                button.clicked.connect(
                    lambda checked=False, b=button, r=role, t=button_text: self._handle_button_clicked(
                        b, r, t
                    )
                )

            # Allgemeine Dialog-Ereignisse mit unseren Button-Tracking verbinden
            if old_accepted:
                self.ui.buttonBox.accepted.connect(self.accept)
            if old_rejected:
                self.ui.buttonBox.rejected.connect(self.reject)

    def _handle_button_clicked(self, button, role, text):
        """
        Speichert Informationen über den angeklickten Button.
        """
        Debug.info(f"Button geklickt: {text} mit Rolle {role}")
        self.clicked_button = button
        self.clicked_role = role
        self.clicked_text = text

        # Dialog entsprechend der Rolle beenden
        if role == QDialogButtonBox.ButtonRole.AcceptRole:
            self.accept()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:
            self.reject()
        # Bei anderen Rollen (ActionRole, ResetRole, etc.) lassen wir den Dialog offen

    def get_clicked_button(self):
        """
        Gibt den angeklickten Button zurück.

        Returns:
            QPushButton: Der angeklickte Button oder None
        """
        return self.clicked_button

    def get_clicked_role(self):
        """
        Gibt die Rolle des angeklickten Buttons zurück.

        Returns:
            QDialogButtonBox.ButtonRole: Die Rolle des angeklickten Buttons oder None
        """
        return self.clicked_role

    def get_clicked_text(self):
        """
        Gibt den Text des angeklickten Buttons zurück.

        Returns:
            str: Der Text des angeklickten Buttons oder None
        """
        return self.clicked_text


class Helper:
    """
    A helper class with static methods for common tasks.
    Methods:
        close_event(parent, event):
            Handles the close event for a window.
    """

    @staticmethod
    def close_event(parent, event):
        # Debug-Logging hinzufügen
        print("Schließen-Event wurde ausgelöst - frage Benutzer nach Bestätigung")
        reply = QMessageBox.question(
            parent,
            "Beenden",
            "Wollen Sie sicher das Programm schließen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            print("Benutzer hat bestätigt - Programm wird beendet")
            event.accept()
        else:
            print("Benutzer hat abgebrochen - Programm läuft weiter")
            event.ignore()


class MessageHelper:
    """Utility functions for showing standard message dialogs."""

    @staticmethod
    def info(parent: QWidget, message: str, title: str = "Information") -> None:
        QMessageBox.information(parent, title, message, QMessageBox.StandardButton.Ok)

    @staticmethod
    def warning(parent: QWidget, message: str, title: str = "Warning") -> None:
        QMessageBox.warning(parent, title, message, QMessageBox.StandardButton.Ok)

    @staticmethod
    def error(parent: QWidget, message: str, title: str = "Error") -> None:
        QMessageBox.critical(parent, title, message, QMessageBox.StandardButton.Ok)

    @staticmethod
    def question(
        parent: QWidget,
        message: str,
        title: str = "Question",
    ) -> bool:
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes


class SaveManager:
    """Utility class for storing measurement data and metadata."""

    def __init__(self, base_dir: Path = None, auto_save: bool = False) -> None:
        self.base_dir = Path(base_dir or Path.home() / "Documents" / "GMCounter")
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover - unlikely
            Debug.error(f"Failed to create base directory {self.base_dir}: {exc}")
        self.auto_save = auto_save
        self.last_saved = True
        self.index = 0

    def filename_auto(
        self,
        rad_sample: str,
        group_letter: str,
        suffix: str = "",
        extension: str = ".csv",
    ) -> str:
        """Generate a standard file name.

        Parameters
        ----------
        rad_sample:
            Sample identifier to include in the file name.
        group_letter:
            Group letter to include in the file name.
        suffix:
            Optional suffix (``-run1`` etc.).
        extension:
            File extension including leading dot.
        """

        if not rad_sample:
            Debug.error("Radioactive sample name cannot be empty.")
            return ""
        if not group_letter:
            Debug.error("Group letter cannot be empty.")
            return ""

        timestamp = datetime.now().strftime("%Y_%m_%d")
        if suffix and not suffix.startswith("-"):
            suffix = "-" + suffix
        self.index += 1
        return f"{timestamp}-{self.index:02d}-{rad_sample}{suffix}{extension}"

    def mark_unsaved(self) -> None:
        """Mark the current measurement as not yet saved."""

        self.last_saved = False

    def has_unsaved(self) -> bool:
        """Return ``True`` if a measurement has not been saved."""

        return not self.last_saved

    def create_metadata(
        self,
        start: datetime,
        end: datetime,
        group: str,
        sample: str,
        extra: Union[dict, None] = None,
    ) -> dict:
        """Create metadata dictionary following basic Dublin Core fields."""

        group_name = (
            group if group and len(str(group)) > 1 else self._create_group_name(group)
        )
        metadata = {
            "dc:date": start.strftime("%Y-%m-%d"),
            "dc:creator": group_name,
            "dc:title": sample,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "radioactive_sample": sample,
        }
        if extra:
            metadata.update(extra)
        return metadata

    def save_measurement(
        self, file_name: str, data: list[list[str]], metadata: dict
    ) -> Path:
        """Save CSV data and accompanying metadata.

        ``file_name`` may be an absolute path or a simple file name. Relative
        names are stored below ``base_dir``.
        """

        csv_path = Path(file_name)
        if not csv_path.is_absolute():
            csv_path = self.base_dir / csv_path
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_f:
                writer = csv.writer(csv_f)
                writer.writerows(data)
            with open(csv_path.with_suffix(".json"), "w", encoding="utf-8") as js_f:
                json.dump(metadata, js_f, indent=2)
            self.last_saved = True
            Debug.info(f"Saved measurement to {csv_path}")
        except Exception as exc:  # pragma: no cover - file system errors
            Debug.error(f"Failed to save measurement: {exc}", exc_info=exc)
        return csv_path

    def auto_save_measurement(
        self,
        rad_sample: str,
        group_letter: str,
        data: list[list[str]],
        start: datetime,
        end: datetime,
        suffix: str = "",
    ) -> Path:
        """Automatically save data using a generated file name."""

        if not data:
            Debug.error("No data provided for auto save")
            return None

        file_name = self.filename_auto(rad_sample, group_letter, suffix)
        meta = self.create_metadata(start, end, group_letter, rad_sample)
        return self.save_measurement(file_name, data, meta)

    def manual_save_measurement(
        self,
        parent: QWidget,
        rad_sample: str,
        group_letter: str,
        data: list[list[str]],
        start: datetime,
        end: datetime,
    ) -> Path:
        """Open a save dialog and store the measurement."""

        if not data:
            MessageHelper.warning(
                parent,
                "Keine Messdaten zum Speichern vorhanden.",
                "Warnung",
            )
            return None

        if not rad_sample or not group_letter:
            MessageHelper.warning(
                parent,
                "Bitte wählen Sie eine radioaktive Probe und eine Gruppenzuordnung aus.",
                "Warnung",
            )
            return None

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Messung speichern",
            str(self.base_dir),
            "CSV-Dateien (*.csv);;Alle Dateien (*)",
            "CSV-Dateien (*.csv)",
        )
        if not file_path:
            return None

        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        meta = self.create_metadata(start, end, group_letter, rad_sample)
        return self.save_measurement(file_path, data, meta)

    def _create_group_name(self, letter: str) -> str:
        """Create a group name based on the letter."""
        semester = "SoSe"
        if datetime.now().month >= 10 and datetime.now().month <= 12:
            semester = "WiSe"
        day = datetime.now().strftime("%a")[:2]
        year = datetime.now().year

        if not letter or not re.match(r"^[A-Z]$", letter):
            Debug.error(f"Invalid group letter: {letter}")
            return "Ungültige Gruppe"

        return f"{semester}{year}_{day}_{letter.upper()}"


def import_config(language: str = "de") -> dict:
    """
    Imports the language-specific configuration from config.json.
    Args:
        language (str): The language code to load the configuration for (default is "de").
    Returns:
        dict: The configuration dictionary.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config[language]
    except FileNotFoundError:
        Debug.error(
            "config.json not found. Please ensure it exists in the project root."
        )
        return {}
    except json.JSONDecodeError as e:
        Debug.error(f"Error decoding JSON from config.json: {e}")
        return {}
