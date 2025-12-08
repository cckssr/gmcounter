# Migration zur neuen Architektur

## Übersicht

Das Projekt wurde gemäß den PySide6-Entwicklungsrichtlinien in drei Hauptschichten umstrukturiert:

### 1. Core Layer (`gmcounter/core/`)

**KEINE PySide6-Imports erlaubt!**

- `models.py` - Domain-Modelle (MeasurementPoint, MeasurementSession, DeviceSettings, DeviceInfo)
- `services.py` - Business-Logik Services:
  - `MeasurementService` - Verwaltung von Mess-Sessions
  - `SaveService` - Speichern von Messdaten (ohne Qt)
  - `DeviceControlService` - Gerätesteuerung (Logik-Teil)
- `utils.py` - Reine Utility-Funktionen ohne Qt:
  - `sanitize_subterm_for_folder()`
  - `create_dropbox_foldername()`
  - `create_group_name()`
  - `calculate_statistics()`

### 2. Infrastructure Layer (`gmcounter/infrastructure/`)

Externe Interaktionen (OS, Hardware, Threading)

- `config.py` - Konfigurationsverwaltung (`import_config()`)
- `qt_threads.py` - Qt Threading-Helpers (`DataAcquisitionThread`)
- `arduino.py` und `device_manager.py` bleiben in der Root (Hardware-Zugriff)

### 3. UI Layer (`gmcounter/ui/`)

**NUR PySide6-Code**

- `common/` - Wiederverwendbare UI-Utilities:
  - `dialogs.py` - Standard-Dialoge (`show_info()`, `show_error()`, `ask_question()`, `ask_save_file()`)
  - `statusbar.py` - Statusleisten-Verwaltung (`StatusBarManager`)
- `windows/` - Hauptfenster (main_window.py sollte hier hin)
- `dialogs/` - Dialog-Fenster (connection.py sollte hier hin)
- `widgets/` - Wiederverwendbare Widgets (plot.py sollte hier hin)
- `pyqt/` - Generierte UI-Dateien (bleibt hier)

## Migration-Schritte für bestehende Module

### Sofort zu erledigen:

1. **helper_classes.py aufteilen:**

   - `SaveManager` → `core/services.py` (als `SaveService`)
   - `MessageHelper` → `ui/common/dialogs.py` (als Funktionen)
   - `Statusbar` → `ui/common/statusbar.py` (als `StatusBarManager`)
   - Utility-Funktionen → `core/utils.py`

2. **control.py:**

   - `ControlWidget` umbenennen zu `ControlService`
   - Nach `core/services.py` als `DeviceControlService` verschieben
   - Alle Qt-Imports entfernen

3. **data_controller.py:**

   - Queue/Threading-Teil zu `infrastructure/`
   - Reine Datenverarbeitung zu `core/services.py`
   - UI-Updates bleiben als dünne Wrapper

4. **plot.py:**

   - Nach `ui/widgets/` verschieben
   - Berechnungslogik ggf. in `core/utils.py` extrahieren

5. **connection.py:**

   - Nach `ui/dialogs/` verschieben
   - ConnectionWindow bleibt als UI-Komponente

6. **main_window.py:**
   - Nach `ui/windows/` verschieben
   - Business-Logik zu Services delegieren
   - Nur noch UI-Event-Handler und Updates

## Import-Änderungen

### Alt:

```python
from .helper_classes import SaveManager, MessageHelper, Statusbar
from .control import ControlWidget
```

### Neu:

```python
from ..core.services import SaveService, MeasurementService, DeviceControlService
from ..ui.common import show_info, show_error, ask_question, StatusBarManager
from ..infrastructure.config import import_config
```

## Regeln für neue Features

1. **Business-Logik immer in `core/services.py`** - KEINE PySide6-Imports!
2. **UI-Code immer in `ui/`** - So dünn wie möglich, delegiert zu Services
3. **Externe Zugriffe in `infrastructure/`** - Threading, Dateien, Netzwerk
4. **Wiederverwendbare UI-Funktionen in `ui/common/`** - Nicht in jedem Widget neu implementieren
5. **Modelle in `core/models.py`** - Dataclasses ohne Qt-Dependencies

## Vorteile der neuen Struktur

- ✅ Testbarkeit: Core-Layer ohne Qt testbar
- ✅ Wartbarkeit: Klare Verantwortlichkeiten
- ✅ Wiederverwendbarkeit: Services können in CLI/API wiederverwendet werden
- ✅ Übersichtlichkeit: Logische Verzeichnisstruktur
- ✅ Best Practices: Entspricht PySide6-Guidelines
