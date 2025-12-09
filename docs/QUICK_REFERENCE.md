# Schnellreferenz: Neue Architektur verwenden

## Import-Cheatsheet

### ❌ ALT (nicht mehr verwenden)

```python
from .helper_classes import SaveManager, MessageHelper, Statusbar
from .control import ControlWidget
from .helper_classes import import_config
```

### ✅ NEU (empfohlen)

```python
# Core Services (KEIN Qt!)
from gmcounter.core.services import (
    MeasurementService,
    SaveService,
    DeviceControlService
)
from gmcounter.core.models import (
    MeasurementPoint,
    MeasurementSession,
    DeviceSettings
)
from gmcounter.core.utils import (
    sanitize_subterm_for_folder,
    create_dropbox_foldername,
    calculate_statistics
)

# UI Common Helpers
from gmcounter.ui.common import (
    show_info,
    show_warning,
    show_error,
    ask_question,
    ask_save_file,
    StatusBarManager
)

# Infrastructure
from gmcounter.infrastructure.config import import_config
from gmcounter.infrastructure.qt_threads import DataAcquisitionThread
```

### 🔄 Übergangsweise (Rückwärtskompatibilität)

```python
# Funktioniert, aber veraltet - gibt Deprecation-Warnung
from .helper_classes_compat import SaveManager, MessageHelper, Statusbar
```

## Verwendungsbeispiele

### 1. Dialoge anzeigen

```python
# ❌ Alt
from .helper_classes import MessageHelper
MessageHelper.info(self, "Information", "Titel")
MessageHelper.error(self, "Fehler", "Titel")
if MessageHelper.question(self, "Frage?", "Titel"):
    pass

# ✅ Neu
from gmcounter.ui.common import show_info, show_error, ask_question
show_info(self, "Information", "Titel")
show_error(self, "Fehler", "Titel")
if ask_question(self, "Frage?", "Titel"):
    pass
```

### 2. Statusleiste verwenden

```python
# ❌ Alt
from .helper_classes import Statusbar
self.statusbar = Statusbar(self.ui.statusBar)
self.statusbar.temp_message("Nachricht", "green", 3000)

# ✅ Neu
from gmcounter.ui.common import StatusBarManager
self.statusbar = StatusBarManager(self.ui.statusBar)
self.statusbar.show_message("Nachricht", "green", 3000)
```

### 3. Daten speichern

```python
# ❌ Alt
from .helper_classes import SaveManager
self.save_manager = SaveManager(base_dir="GMCounter", tk_designation="TK47")
self.save_manager.auto_save_measurement(...)

# ✅ Neu
from gmcounter.core.services import SaveService
self.save_service = SaveService(base_dir="GMCounter", tk_designation="TK47")
self.save_service.auto_save(...)
```

### 4. Messung verwalten

```python
# ✅ Neu - MeasurementService
from gmcounter.core.services import MeasurementService

self.measurement_service = MeasurementService()

# Session starten
session = self.measurement_service.start_session(
    radioactive_sample="Co-60",
    subterm="Gruppe A",
    group="A"
)

# Datenpunkt hinzufügen
self.measurement_service.add_point(index=1, value=12345.0, timestamp="12:34:56")

# Session stoppen
session = self.measurement_service.stop_session()

# Prüfen ob ungespeichert
if self.measurement_service.has_unsaved_data():
    # Speichern...
    pass

# Daten für CSV exportieren
data = self.measurement_service.get_data_as_list()
```

### 5. Gerät steuern

```python
# ❌ Alt
from .control import ControlWidget
self.control = ControlWidget(device_manager)
self.control.apply_settings({"repeat": True, "voltage": 500, ...})

# ✅ Neu
from gmcounter.core.services import DeviceControlService
from gmcounter.core.models import DeviceSettings

self.control_service = DeviceControlService(device_manager)

settings = DeviceSettings(repeat=True, voltage=500, counting_time=1, auto_query=False)
self.control_service.apply_settings(settings)

# Oder mit dict
current = self.control_service.get_current_settings()
```

### 6. Konfiguration laden

```python
# ❌ Alt
from .helper_classes import import_config
CONFIG = import_config()

# ✅ Neu
from gmcounter.infrastructure.config import import_config
CONFIG = import_config()
```

### 7. Dateidialog

```python
# ✅ Neu
from gmcounter.ui.common import ask_save_file, ask_open_file
from pathlib import Path

# Speichern
path = ask_save_file(
    parent=self,
    title="Messung speichern",
    default_dir=Path.home() / "Documents",
    default_name="measurement.csv",
    file_filter="CSV Files (*.csv);;All Files (*.*)"
)
if path:
    # Speichern...
    pass

# Öffnen
path = ask_open_file(
    parent=self,
    title="Messung öffnen",
    default_dir=Path.home() / "Documents",
    file_filter="CSV Files (*.csv);;All Files (*.*)"
)
if path:
    # Laden...
    pass
```

## Wo erstelle ich neue Komponenten?

### Neue Business-Logik

```python
# gmcounter/core/services.py
class MyNewService:
    """NO PySide6 imports!"""
    def __init__(self):
        pass

    def do_something(self, data):
        # Pure Python logic
        return result
```

### Neues Datenmodell

```python
# gmcounter/core/models.py
from dataclasses import dataclass

@dataclass
class MyDataModel:
    """NO PySide6 imports!"""
    name: str
    value: float
```

### Neue Utility-Funktion

```python
# gmcounter/core/utils.py
def my_utility_function(input_data):
    """NO PySide6 imports!"""
    # Pure calculation/transformation
    return result
```

### Neues Widget

```python
# gmcounter/ui/widgets/my_widget.py
from PySide6.QtWidgets import QWidget
from ...core.services import MyNewService

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = MyNewService()  # Delegate to service

    def on_button_click(self):
        # Get data from UI
        data = self.lineEdit.text()

        # Delegate to service
        result = self.service.do_something(data)

        # Update UI
        self.resultLabel.setText(str(result))
```

### Neuer Dialog

```python
# gmcounter/ui/dialogs/my_dialog.py
from PySide6.QtWidgets import QDialog
from ...ui.common import show_error

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Setup UI...

    def on_ok_clicked(self):
        if not self.validate():
            show_error(self, "Validation failed", "Error")
            return
        self.accept()
```

## Testing

### Core testen (ohne Qt)

```python
# tests/test_services.py
from gmcounter.core.services import MeasurementService

def test_measurement_service():
    service = MeasurementService()
    session = service.start_session(radioactive_sample="Co-60")
    service.add_point(1, 12345.0, "12:34:56")

    assert service.current_session.count == 1
    assert service.has_unsaved_data() == True
```

### UI testen (mit Qt)

```python
# tests/test_widgets.py
import pytest
from PySide6.QtWidgets import QApplication
from gmcounter.ui.widgets.my_widget import MyWidget

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_my_widget(app):
    widget = MyWidget()
    widget.show()
    assert widget.isVisible()
```

## Checkliste für neuen Code

- [ ] Business-Logik in `core/services.py` (KEIN PySide6!)
- [ ] Datenmodelle in `core/models.py` (KEIN PySide6!)
- [ ] UI-Code in `ui/` (delegiert zu Services)
- [ ] Wiederverwendbare Dialoge in `ui/common/`
- [ ] Tests für Core ohne Qt
- [ ] Imports aus neuen Modulen
- [ ] Keine direkten Imports aus alten Modulen
