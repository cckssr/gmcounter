#!/bin/bash

# Convert UI files to Python using pyside6-uic
.venv/bin/pyside6-uic ./gmcounter/pyqt/mainwindow.ui -o ./gmcounter/pyqt/ui_mainwindow.py
.venv/bin/pyside6-uic ./gmcounter/pyqt/connection.ui -o ./gmcounter/pyqt/ui_connection.py
.venv/bin/pyside6-uic ./gmcounter/pyqt/alert.ui -o ./gmcounter/pyqt/ui_alert.py

echo "UI files converted successfully"