# GMCounter Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANWENDUNGS-SCHICHTEN                     │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  UI LAYER (gmcounter/ui/)                                     │
│  ────────────────────────────────────────                     │
│  ✓ PySide6-Imports erlaubt                                    │
│  ✗ Keine Business-Logik                                       │
│                                                                │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ windows/    │  │ dialogs/ │  │ widgets/ │  │ common/  │  │
│  │             │  │          │  │          │  │          │  │
│  │ MainWindow  │  │Connection│  │ Plot     │  │ Dialogs  │  │
│  │             │  │ Alert    │  │ Control  │  │ Statusbar│  │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────┘  │
│         │               │              │              │       │
│         └───────────────┴──────────────┴──────────────┘       │
│                            ▼                                   │
└───────────────────────────────────────────────────────────────┘
                            ║
                            ║ Delegiert an
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  CORE LAYER (gmcounter/core/)                                 │
│  ─────────────────────────────────                            │
│  ✗ KEINE PySide6-Imports                                      │
│  ✓ Pure Python Business-Logik                                 │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ models.py        │  │ services.py      │  │ utils.py   │ │
│  │                  │  │                  │  │            │ │
│  │ MeasurementPoint │  │ MeasurementSvc   │  │ Sanitize   │ │
│  │ MeasurementSession│  │ SaveService     │  │ Foldername │ │
│  │ DeviceSettings   │  │ DeviceControlSvc │  │ Statistics │ │
│  │ DeviceInfo       │  │                  │  │            │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│                                 │                             │
└─────────────────────────────────┼─────────────────────────────┘
                                  ║
                                  ║ Nutzt
                                  ▼
┌───────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (gmcounter/infrastructure/)             │
│  ────────────────────────────────────────────────             │
│  ✓ Externe Interaktionen                                      │
│  ✓ Qt-Threading erlaubt                                       │
│                                                                │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ config.py      │  │ qt_threads.py│  │ file_io.py       │ │
│  │                │  │              │  │ (zukünftig)      │ │
│  │ import_config  │  │ DataAcq      │  │                  │ │
│  │ get_config     │  │ Thread       │  │                  │ │
│  └────────────────┘  └──────────────┘  └──────────────────┘ │
│                                                                │
└───────────────────────────────────────────────────────────────┘
                            ║
                            ║ Zugriff auf
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  HARDWARE / EXTERNE SYSTEME                                   │
│  ──────────────────────────                                   │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Arduino      │  │ Dateisystem  │  │ Konfiguration│       │
│  │ GM-Counter   │  │ CSV/JSON     │  │ config.json  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                │
└───────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      DATENFLUSS-BEISPIEL                        │
└─────────────────────────────────────────────────────────────────┘

1. USER-AKTION
   │
   └─> MainWindow.on_start_button_clicked()
       │
       ├─> Liest UI-Werte (sample, group, etc.)
       │
       └─> Delegiert an Service
           │
           └─> MeasurementService.start_session(sample, group)
               │
               ├─> Erstellt MeasurementSession (Model)
               ├─> Setzt Timestamps
               └─> Gibt Session zurück
                   │
                   └─> MainWindow aktualisiert UI
                       │
                       └─> StatusBarManager.show_message("Started")

2. DATEN-EMPFANG
   │
   └─> DataAcquisitionThread (Infrastructure)
       │
       ├─> Liest Bytes von Arduino
       ├─> Validiert Paket
       └─> Emittiert Signal: data_point(index, value)
           │
           └─> MainWindow.on_data_received(index, value)
               │
               ├─> MeasurementService.add_point(index, value, timestamp)
               │   └─> Fügt zu Session.points hinzu
               │
               └─> PlotWidget.update_plot(data)

3. DATEN-SPEICHERN
   │
   └─> MainWindow.on_save_button_clicked()
       │
       ├─> ask_save_file() (UI Common)
       │   └─> Benutzer wählt Datei
       │
       ├─> data = MeasurementService.get_data_as_list()
       │
       └─> SaveService.save_measurement(filename, data, metadata)
           │
           ├─> Schreibt CSV (Infrastructure)
           ├─> Schreibt JSON-Metadata
           └─> Gibt Path zurück
               │
               └─> show_info("Saved successfully") (UI Common)


┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITEKTUR-REGELN                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│ CORE LAYER          │
├─────────────────────┤
│ ✓ Pure Python       │
│ ✓ Standard Library  │
│ ✓ Dataclasses       │
│ ✗ KEIN PySide6      │
│ ✗ KEIN Qt           │
└─────────────────────┘

┌─────────────────────┐
│ UI LAYER            │
├─────────────────────┤
│ ✓ PySide6/Qt        │
│ ✓ Widgets           │
│ ✓ Event-Handler     │
│ ✗ Business-Logik    │
│ → Delegiert zu Core │
└─────────────────────┘

┌─────────────────────┐
│ INFRASTRUCTURE      │
├─────────────────────┤
│ ✓ File I/O          │
│ ✓ Threading         │
│ ✓ Config            │
│ ✓ Hardware          │
│ ✗ Business-Logik    │
└─────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                 DEPENDENCY-RICHTUNG                             │
└─────────────────────────────────────────────────────────────────┘

                    UI Layer
                       │
                       ▼
                   Core Layer
                       │
                       ▼
             Infrastructure Layer
                       │
                       ▼
                External Systems

Regel: Höhere Schichten dürfen tiefere importieren
       Tiefere Schichten dürfen NICHT höhere importieren
       Core darf NICHTS von UI wissen!


┌─────────────────────────────────────────────────────────────────┐
│                    VORTEILE                                     │
└─────────────────────────────────────────────────────────────────┘

1. TESTBARKEIT
   ✓ Core ohne Qt testbar
   ✓ Schnelle Unit-Tests
   ✓ Keine GUI-Abhängigkeiten

2. WARTBARKEIT
   ✓ Klare Verantwortlichkeiten
   ✓ Einfach zu verstehen
   ✓ Änderungen isoliert

3. WIEDERVERWENDBARKEIT
   ✓ Services in CLI nutzbar
   ✓ Services in API nutzbar
   ✓ Keine UI-Kopplung

4. SKALIERBARKEIT
   ✓ Neue Features folgen Pattern
   ✓ Konsistente Struktur
   ✓ Team-freundlich

5. BEST PRACTICES
   ✓ Separation of Concerns
   ✓ Dependency Inversion
   ✓ PySide6-Guidelines
```
