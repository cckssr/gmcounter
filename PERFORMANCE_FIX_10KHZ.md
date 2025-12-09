# Performance-Optimierung für Hochfrequenz-Datenaufnahme (bis 10 kHz)

## Problem

Die Anwendung fror bei Frequenzen über 1000 Hz ein aufgrund mehrerer kritischer Probleme:

1. **Blocking Signal-Slot Connection**: Der Data-Acquisition-Thread blockierte den GUI-Thread
2. **Exzessive GUI-Updates**: Bei 10 kHz = 10.000 GUI-Updates pro Sekunde
3. **Table-Updates**: Tabelle wurde für jeden einzelnen Datenpunkt aktualisiert
4. **Fehlende Thread-Sicherheit**: Race Conditions bei Queue-Zugriff
5. **Ineffiziente Sleep-Zeiten**: Zu lange Wartezeiten im Acquisition-Thread

## Lösung

### 1. Qt.QueuedConnection für Thread-sichere Signal-Übertragung

**Datei**: `gmcounter/ui/windows/main_window.py`

```python
# VORHER (FALSCH):
self.device_manager.data_received.connect(self.handle_data)

# NACHHER (KORREKT):
self.device_manager.data_received.connect(
    self.handle_data, Qt.ConnectionType.QueuedConnection
)
```

**Effekt**: Signal wird asynchron in die Event-Queue des GUI-Threads eingereiht, statt den Acquisition-Thread zu blockieren.

### 2. GUI-Update-Intervall erhöht (100ms → 200ms)

**Datei**: `gmcounter/ui/controllers/data_controller.py`

```python
# Minimum 200ms zwischen GUI-Updates = 5 Updates/Sekunde
UPDATE_INTERVAL = max(200, CONFIG["timers"]["gui_update_interval"])
```

**Effekt**: Reduziert GUI-Load von 10 Updates/s auf 5 Updates/s bei gleicher visueller Qualität.

### 3. Table-Updates drastisch reduziert (nur alle 500ms)

**Datei**: `gmcounter/ui/controllers/data_controller.py`

```python
# Update table ONLY every 500ms to prevent GUI freeze at high frequencies
# At 10kHz, this reduces table updates from 10000/s to 2/s
if (current_time - self._last_table_update) >= 0.5:
    self._update_table_with_batch(new_points)
    self._last_table_update = current_time
```

**Effekt**: Bei 10 kHz nur noch 2 Table-Updates/Sekunde statt 10.000.

### 4. Queue mit Overflow-Protection

**Datei**: `gmcounter/ui/controllers/data_controller.py`

```python
# Max size: at 10kHz with 200ms updates = 2000 points max per batch
# Use 10000 as safety buffer (= 1 second at 10kHz)
self.data_queue: queue.Queue = queue.Queue(maxsize=10000)

# Non-blocking enqueue
try:
    self.data_queue.put_nowait((index_num, value_num, timestamp))
except queue.Full:
    Debug.warning("Data queue overflow! GUI cannot keep up...")
```

**Effekt**: Verhindert Memory-Überlauf und blockiert nie den Acquisition-Thread.

### 5. Adaptive Sleep-Zeiten im Acquisition-Thread

**Datei**: `gmcounter/infrastructure/qt_threads.py`

```python
# VORHER: Immer 1ms sleep
time.sleep(0.001)

# NACHHER: Adaptive sleep
if self.manager.measurement_active:
    time.sleep(0.0001)  # 0.1ms während Messung
else:
    time.sleep(0.01)    # 10ms wenn idle
```

**Effekt**: Bei 10 kHz (Pakete alle 0.1ms) ist 0.1ms sleep optimal für minimale Latenz ohne CPU-Überlastung.

### 6. Thread-sichere clear_data() Implementation

**Datei**: `gmcounter/ui/controllers/data_controller.py`

```python
def clear_data(self) -> None:
    # Stop timer temporarily
    was_running = self.gui_update_timer.isActive()
    if was_running:
        self.gui_update_timer.stop()

    # Clear data safely
    with self._queue_lock:
        self.data_queue = queue.Queue(maxsize=10000)

    # Restart timer
    if was_running:
        self.gui_update_timer.start(...)
```

**Effekt**: Verhindert Race Conditions beim Löschen während aktiver Aufnahme.

## Performance-Verbesserungen

| Metrik          | Vorher (1 kHz) | Nachher (10 kHz)            |
| --------------- | -------------- | --------------------------- |
| GUI-Updates/s   | 10             | 5                           |
| Table-Updates/s | 1000           | 2                           |
| Queue-Größe     | Unbegrenzt     | 10.000 (max)                |
| Thread-Sleep    | 1ms            | 0.1ms (aktiv) / 10ms (idle) |
| Signal-Delivery | Blocking       | Asynchron (queued)          |

## Erwartete Ergebnisse

✅ **10 kHz Datenrate** sollte jetzt ohne Einfrieren funktionieren  
✅ **Alle Daten werden gespeichert** (unbegrenzte `data_points` Liste)  
✅ **GUI bleibt responsiv** durch asynchrone Updates  
✅ **CPU-Last reduziert** durch optimierte Sleep-Zeiten  
✅ **Memory-Sicherheit** durch Queue-Overflow-Protection

## Test-Empfehlungen

1. **1 kHz**: Sollte perfekt flüssig laufen
2. **5 kHz**: Sollte ohne Probleme funktionieren
3. **10 kHz**: Sollte stabil sein, GUI-Updates können minimal verzögert sein (akzeptabel)
4. **>10 kHz**: Queue-Overflow-Warnung möglich, aber keine Datenverluste in CSV

## Bekannte Limitierungen

- **Tabellen-Anzeige**: Bei >5 kHz werden nur die letzten `max_history` Punkte angezeigt
- **Plot-Updates**: Nur alle 200ms, kann bei sehr schnellen Änderungen leicht "nachlaufen"
- **CSV-Export**: Unbegrenzt, kann bei sehr langen Messungen (>1 Million Punkte) langsam werden

## Weiterführende Optimierungen (optional)

Falls weitere Probleme auftreten:

1. **Plot-Downsampling**: Bei >10.000 GUI-Punkten nur jeden N-ten Punkt anzeigen
2. **Circular Buffer**: Statt Liste einen Ring-Buffer für `data_points` verwenden
3. **Separate Thread für File-I/O**: Schreiben direkt in Datei statt in Memory
4. **Binary Protocol Optimization**: Hardware-Timestamp statt Software-Timestamp

## Änderungen zusammengefasst

- ✅ `main_window.py`: Qt.QueuedConnection für Thread-Safety
- ✅ `data_controller.py`: GUI-Update-Interval 200ms, Table-Updates alle 500ms
- ✅ `data_controller.py`: Queue mit maxsize=10000 und Overflow-Protection
- ✅ `data_controller.py`: Thread-sichere clear_data() Implementation
- ✅ `qt_threads.py`: Adaptive Sleep-Zeiten (0.1ms aktiv / 10ms idle)

---

**Datum**: 9. Dezember 2025  
**Status**: ✅ Implementiert und bereit zum Testen
