# GMCounter - Geiger-Müller Counter GUI

Eine grafische Benutzeroberfläche zur Steuerung und Datenerfassung eines Geiger-Müller-Zählrohrs für Zufallszahlengenerierung.

## Projektstruktur

Das Projekt verwendet eine modulare Struktur mit dem Paket `gmcounter`:

```
GMCounter/
├── main.py                 # Einstiegspunkt (Alternative)
├── pyproject.toml          # Projekt-Konfiguration und Abhängigkeiten
├── requirements.txt        # Python Abhängigkeiten (Alternative)
│
├── gmcounter/              # Hauptpaket
│   ├── __init__.py         # Paket-Initialisierung
│   ├── __main__.py         # Entry Point für `python -m gmcounter`
│   ├── main.py             # Hauptprogramm
│   ├── arduino.py          # GM-Counter Kommunikation
│   ├── config.json         # Zentrale Konfiguration
│   ├── connection.py       # Verbindungsverwaltung
│   ├── data_controller.py  # Datenverwaltung und -verarbeitung
│   ├── device_manager.py   # Geräte-Management
│   ├── debug_utils.py      # Debug-Hilfsfunktionen
│   ├── helper_classes.py   # Hilfsklassen (SaveManager, etc.)
│   ├── main_window.py      # Hauptfensterklasse
│   ├── control.py          # Steuerungs-Widget
│   ├── plot.py             # Plotting-Funktionalität
│   └── pyqt/               # Qt UI-Definitionen
│       ├── ui_mainwindow.py
│       └── ui_connection.py
│
├── tests/                  # Testdateien
├── docs/                   # Dokumentation
└── logs/                   # Logdateien (automatisch erstellt)
```

## Installation

### Option 1: Installation via pip (empfohlen)

```bash
# Aus dem Projektverzeichnis installieren
pip install .

# Oder im Entwicklungsmodus (für Entwicklung)
pip install -e .
```

### Option 2: Direkte Installation der Abhängigkeiten

```bash
pip install -r requirements.txt
```

## Anwendung starten

### Nach pip-Installation

```bash
# Als GUI-Anwendung (ohne Terminal-Fenster unter Windows)
gmcounter
```

### Ohne Installation

```bash
# Als Python-Modul
python -m gmcounter

# Oder über main.py
python main.py
```

### Windows ohne CMD-Fenster

```bash
pythonw -m gmcounter
```

## Verwendung

1. Nach dem Start wird ein Verbindungsdialog angezeigt, in dem Sie den seriellen Port auswählen können.

2. Im Hauptfenster können Sie:
   - Die Messparameter (Spannung, Zähldauer, etc.) einstellen
   - Messungen starten und stoppen
   - Messdaten in Echtzeit anzeigen
   - Statistiken zur laufenden Messung anzeigen
   - Messdaten als CSV exportieren

## Entwicklung

Die Anwendung wurde mit einer sauberen Architektur entwickelt:

- **Model**: `DataController` und andere Datenklassen verwalten die Daten
- **View**: Qt-basierte Benutzeroberfläche (PySide6)
- **Controller**: `MainWindow` und Hilfsklassen steuern den Ablauf

Die `config.json` enthält zentrale Konfigurationsoptionen.

## Tests

Das Projekt enthält umfangreiche Tests:

### Automatisierte Tests

```bash
# Mit pytest
pytest

# Mit Coverage
pytest --cov=gmcounter
```

### Manueller Testplan

Der Datei `testplan.md` enthält einen strukturierten Plan für manuelle Tests.

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Repository

- **GitHub**: https://github.com/cckssr/gmcounter
- **Dokumentation**: https://gmcounter.readthedocs.io
