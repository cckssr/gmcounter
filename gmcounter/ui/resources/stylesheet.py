"""Light and dark Qt stylesheets for the GMCounter UI.

The module exposes helper functions to apply a coherent application-wide
appearance.  The styles aim to be modern, neutral and easy to maintain.
"""

from __future__ import annotations

from typing import Final


_DARK_STYLESHEET: Final[
    str
] = r"""
/* Base */
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #e5e7eb;
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #1f2937;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
    background-color: #111827;
    color: #e5e7eb;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #cbd5e1;
}

QLabel {
    color: #e5e7eb;
}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
    background-color: #0b1220;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    color: #e5e7eb;
    selection-background-color: #1d4ed8;
    selection-color: #f8fafc;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #0b1220;
    color: #e5e7eb;
    selection-background-color: #1d4ed8;
    selection-color: #f8fafc;
    border: 1px solid #334155;
}

QRadioButton, QCheckBox {
    spacing: 6px;
    color: #e5e7eb;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #f8fafc;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #1f2937;
    color: #9ca3af;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1f2937;
    border-radius: 8px;
    background: #111827;
    padding: 6px;
}

QTabBar::tab {
    background: #0b1220;
    color: #cbd5e1;
    padding: 8px 14px;
    border: 1px solid #1f2937;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: #111827;
    color: #e5e7eb;
    border-color: #3b82f6;
}

/* Tables */
QTableView {
    background-color: #0b1220;
    alternate-background-color: #111827;
    gridline-color: #1f2937;
    border: 1px solid #1f2937;
    selection-background-color: #1d4ed8;
    selection-color: #f8fafc;
}

QHeaderView::section {
    background-color: #111827;
    color: #e5e7eb;
    padding: 6px;
    border: 1px solid #1f2937;
}

/* Status bar & progress */
QStatusBar {
    background: #0b1220;
    color: #cbd5e1;
    border-top: 1px solid #1f2937;
    padding: 4px;
}

QProgressBar {
    background-color: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 6px;
    text-align: center;
    color: #e5e7eb;
}

QProgressBar::chunk {
    background-color: #22c55e;
    border-radius: 6px;
}
"""

_LIGHT_STYLESHEET: Final[
    str
] = r"""
/* Base */
QMainWindow, QWidget {
    background-color: #f5f7fb;
    color: #0f172a;
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
    background-color: #ffffff;
    color: #0f172a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #334155;
}

QLabel {
    color: #0f172a;
}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 8px;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
    border-color: #2563eb;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #cbd5e1;
}

QRadioButton, QCheckBox {
    spacing: 6px;
    color: #0f172a;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    padding: 6px;
}

QTabBar::tab {
    background: #f8fafc;
    color: #334155;
    padding: 8px 14px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #0f172a;
    border-color: #2563eb;
}

/* Tables */
QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #e2e8f0;
    border: 1px solid #e2e8f0;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 6px;
    border: 1px solid #e2e8f0;
}

/* Status bar & progress */
QStatusBar {
    background: #f1f5f9;
    color: #334155;
    border-top: 1px solid #e2e8f0;
    padding: 4px;
}

QProgressBar {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    text-align: center;
    color: #0f172a;
}

QProgressBar::chunk {
    background-color: #16a34a;
    border-radius: 6px;
}
"""


def get_stylesheet(mode: str = "dark") -> str:
    """Return the Qt stylesheet for the requested mode.

    Args:
        mode: Either ``"dark"`` or ``"light"`` (case-insensitive).

    Raises:
        ValueError: If the mode is unknown.
    """

    normalized = mode.strip().lower()
    if normalized.startswith("dark"):
        return _DARK_STYLESHEET
    if normalized.startswith("light"):
        return _LIGHT_STYLESHEET
    raise ValueError(f"Unknown stylesheet mode: {mode}")


def apply_stylesheet(app, mode: str = "dark") -> None:
    """Apply the chosen stylesheet to the given QApplication."""

    app.setStyleSheet(get_stylesheet(mode))
