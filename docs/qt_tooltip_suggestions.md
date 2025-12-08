# Qt Tooltip-Vorschläge

Überblick über alle Widgets in den `.ui` Dateien mit vorgeschlagenen (teils Rich-Text) Tooltips zur einheitlichen Dokumentation in Qt Creator. Bestehende Tooltips können unverändert übernommen oder durch die Vorschläge ersetzt werden.

## `connection.ui`

| Widget (Typ) | Beschriftung/Name | Tooltip-Vorschlag |
| --- | --- | --- |
| Dialog (QDialog) | Verbindung herstellen | `<b>Serielle Verbindung</b> zum GM-Zähler öffnen oder abbrechen.` |
| buttonBox (QDialogButtonBox) | OK/Abbrechen | `Mit <b>Öffnen</b> wird der ausgewählte Port verbunden, <b>Abbrechen</b> schließt den Dialog.` |
| label_5 (QLabel) | Hinweistext | `Kurzanleitung zur Auswahl von Port und Baudrate.` |
| comboSerial (QComboBox) | Portauswahl | Bereits vorhanden: `Kommunikation mit dem Arduino …`; kann so bleiben. |
| buttonRefreshSerial (QPushButton) | Aktualisieren | Bereits vorhanden: `Die Liste der Ports aktualisieren.` |
| label_4 (QLabel) | Baud Rate | `Serielle Übertragungsgeschwindigkeit in Baud wählen (Standard: 115200).` |
| comboBox (QComboBox) | Baud-Auswahl | `Übliche Baudraten des GM-Zählers. Nur ändern, wenn Gerät abweichend konfiguriert ist.` |
| line (Line) | Trennlinie | `Optische Trennung der Verbindungsdaten.` |
| label (QLabel) | Adresse | `Vom Gerät gemeldete Bus-Adresse (read-only).` |
| device_address (QLineEdit) | Adresse Feld | `Vom Gerät gemeldete Bus-Adresse (nicht editierbar).` |
| label_2 (QLabel) | Name | `Vom Gerät gemeldeter Gerätename.` |
| device_name (QLineEdit) | Name Feld | `Automatisch erkannter Gerätename (read-only).` |
| label_3 (QLabel) | Beschreibung | `Zusätzliche Gerätebeschreibung laut Firmware.` |
| device_desc (QLineEdit) | Beschreibung Feld | `Beschreibung des verbundenen Geräts (read-only).` |
| status_msg (QLabel) | Statusmeldung | `Status- oder Fehlermeldungen zum Verbindungsaufbau.` |

## `control.ui`

| Widget (Typ) | Beschriftung/Name | Tooltip-Vorschlag |
| --- | --- | --- |
| Form (QWidget) | Kontrollfenster | `Schnellzugriff auf aktuelle Geräteeinstellungen.` |
| label_11 (QLabel) | „Aktuelle Einstellungen” | `Zeigt die zuletzt an das Gerät übertragenen Parameter.` |
| mode_label (QLabel) | Zähl-Modus | `Zählmodus auswählen.` |
| sModeSingle (QRadioButton) | Einzel | Bereits vorhanden: `Stoppt die Messung nach Ablauf Zähldauer.` |
| sModeMulti (QRadioButton) | Wiederholung | Bereits vorhanden: `Wiederholt die Messung automatisch nach Ablauf Zähldauer.` |
| query_label (QLabel) | Abfragemodus | `Legt fest, wann Messergebnisse vom Gerät abgefragt werden.` |
| sQModeMan (QRadioButton) | Manuell | `Zählergebnisse nur auf manuelle Anforderung übertragen.` |
| sQModeAuto (QRadioButton) | Automatik | `Zählergebnisse zyklisch automatisch übertragen.` |
| duration_label (QLabel) | Zähldauer | `Zeitfenster je Messung auswählen.` |
| sDuration (QComboBox) | Zähldauer-Auswahl | Bereits vorhanden: `Wie lange der Zähler misst.` |
| volt_label (QLabel) | GM-Spannung | `Sollspannung des Geiger-Müller-Zählrohrs in Volt.` |
| sVoltage (QSpinBox) | Spannung Spinbox | `Sollspannung einstellen (300–700 V).` |
| voltDial (QDial) | Spannung Drehrad | `Alternative Einstellung der GM-Spannung per Drehregler.` |
| line (Line) | Trennlinie | `Optische Trennung zwischen Soll- und Ist-Werten.` |
| controlButton (QPushButton) | Einstellungen ändern | Bereits vorhanden: `Klicken um Einstellungen an Gerät zu übertragen…` |
| label_8 (QLabel) | GM-Spannung / V | `Aktuell gemessene Hochspannung des Zählrohrs.` |
| cVoltage (QLCDNumber) | Spannung Ist | Bereits vorhanden: `Aktuelle GM-Spannung.` |
| label_9 (QLabel) | Zähldauer / s | `Aktuelle Zähldauer laut Gerät.` |
| cDuration (QLCDNumber) | Dauer Ist | Bereits vorhanden: `Aktuelle eingestellte Zähldauer. 999 für unendllich.` |
| label_10 (QLabel) | Abfragemodus | `Aktueller Abfragemodus des Geräts.` |
| cQueryMode (QLabel) | Abfragemodus Ist | Bereits vorhanden: `Aktuell eingestellter Abfragemodus der Zählergebnisse.` |
| label (QLabel) | Version | `Firmware-Version des verbundenen Geräts.` |
| cVersion (QLabel) | Version Wert | Bereits vorhanden: `GM-Zähler Firmware.` |
| label_12 (QLabel) | Zähl-Modus | `Aktueller Zählmodus des Geräts.` |
| cMode (QLabel) | Zählmodus Wert | Bereits vorhanden: `Aktuell eingestellter Zählmodus.` |

## `mainwindow.ui`

| Widget (Typ) | Beschriftung/Name | Tooltip-Vorschlag |
| --- | --- | --- |
| MainWindow (QMainWindow) | Hauptfenster | `Hauptoberfläche des GM-Counters.` |
| centralwidget (QWidget) | Zentralbereich | `Beinhaltet Steuerung, Status und Diagramme.` |
| settings (QGroupBox) | „Einstellungen” | `Messparameter festlegen, die an das Gerät gesendet werden.` |
| mode_label (QLabel) | Zähl-Modus | `Gewünschten Zählmodus auswählen.` |
| sModeSingle (QRadioButton) | Einzel | Bereits vorhanden: `Stoppt die Messung nach Ablauf Zähldauer.` |
| sModeMulti (QRadioButton) | Wiederholung | Bereits vorhanden: `Wiederholt die Messung automatisch nach Ablauf Zähldauer.` |
| label_10 (QLabel) | Abfragemodus | `Wann sollen Messergebnisse abgefragt werden?` |
| sQModeMan (QRadioButton) | Manuell | `Zählergebnisse nur bei manueller Anforderung abfragen.` |
| sQModeAuto (QRadioButton) | Automatik | `Zählergebnisse automatisch nach jeder Messung abrufen.` |
| duration_label (QLabel) | Zähldauer | `Zeitfenster pro Messung wählen.` |
| sDuration (QComboBox) | Zähldauer-Auswahl | Bereits vorhanden: `Wie lange der Zähler misst.` |
| volt_label (QLabel) | GM-Spannung | `Sollspannung des Geiger-Müller-Zählrohrs in Volt.` |
| sVoltage (QSpinBox) | Spannung Spinbox | `Sollspannung einstellen (300–700 V).` |
| voltDial (QDial) | Spannung Drehrad | `Alternative Einstellung der GM-Spannung per Drehregler.` |
| buttonSetting (QPushButton) | Einstellungen ändern | `Aktuelle Auswahl an das Gerät übertragen.` |
| groupBox (QGroupBox) | „Speicherung” | `Metadaten und Speicheroptionen für Messungen.` |
| label_6 (QLabel) | Radioaktive Probe* | `Pflichtfeld: Kennung der verwendeten Probe.` |
| radSample (QComboBox) | Probe-Auswahl | Bereits vorhanden: Auswahl-Pflichtfeld-Hinweis. |
| label_7 (QLabel) | Gruppe* | `Pflichtfeld: Praktikumsgruppe auswählen.` |
| groupLetter (QComboBox) | Gruppen-Auswahl | Bereits vorhanden: Hinweis zur Pflichtauswahl. |
| label_5 (QLabel) | Eigenes Suffix | `Optionales Namens-Suffix für gespeicherte Dateien.` |
| suffix (QLineEdit) | Suffix Feld | Bereits vorhanden: `Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen.` |
| buttonSave (QPushButton) | Speichern | Bereits vorhanden: `Messung speichern (Dateidialog).` |
| autoSave (QCheckBox) | Automatische Speicherung | Bereits vorhanden: Beschreibung zur Autosave-Benennung. |
| buttonStart (QPushButton) | Start | Bereits vorhanden: `Start der Messung.` |
| buttonStop (QPushButton) | Stop | Bereits vorhanden: `Aktuelle Messung stoppen.` |
| line (Line) | Trennlinie | `Trennung zwischen Steuerung und Anzeige.` |
| gridGroupBox (QGroupBox) | Diagramme/Status | `Diagramm- und Statusbereich der Messung.` |
| line_2 (Line) | Trennlinie | `Trennung zwischen Diagrammen und Statistik.` |
| tabWidget (QTabWidget) | Tabs | `Zwischen Zeitreihe, Histogramm und Tabelle wechseln.` |
| timePlot (QWidget) | Zeitreihe | `Plot der Zählrate über die Zeit.` |
| histogramm (QWidget) | Histogramm | `Histogramm der Messergebnisse.` |
| histWidget (QWidget) | Statistik | `Statistikfelder zur aktuellen Messung.` |
| label_13 (QLabel) | Anzahl | `Anzahl der gemessenen Stichproben.` |
| cStatPoints (QLineEdit) | Anzahl Feld | `Zeigt, wie viele Einzelmessungen in der Statistik enthalten sind (read-only).` |
| label_14 (QLabel) | Min / µs | `Minimaler Zählwert pro µs der Stichprobe.` |
| cStatMin (QLineEdit) | Minimum Feld | `Kleinster Messwert (read-only).` |
| label_15 (QLabel) | Max / µs | `Maximaler Zählwert pro µs der Stichprobe.` |
| cStatMax (QLineEdit) | Maximum Feld | `Größter Messwert (read-only).` |
| label_16 (QLabel) | Mittelwert / µs | `Arithmetischer Mittelwert der Stichprobe.` |
| cStatAvg (QLineEdit) | Mittelwert Feld | `Durchschnittlicher Messwert (read-only).` |
| label_17 (QLabel) | Standardabw. / µs | `Standardabweichung der Messwerte.` |
| cStatSD (QLineEdit) | Std.-Abw. Feld | `Streuung der Messwerte (read-only).` |
| list (QWidget) | Liste | `Tabellarische Auflistung der gespeicherten Werte.` |
| tableView (QTableView) | Tabelle | `Zeigt Messpunkte oder gespeicherte Datensätze (nicht editierbar).` |
| label_4 (QLabel) | Voriger Wert | `Letztes Messresultat der vorangegangenen Messung.` |
| lastCount (QLCDNumber) | Letzter Wert | `Anzeige des vorherigen Messwerts.` |
| label_18 (QLabel) | Aktuelle GM-Parameter | `Überschrift der aktuellen Geräteparameter.` |
| progressBar (QProgressBar) | Fortschritt | `Fortschritt innerhalb der aktuellen Zähldauer.` |
| progressTimer (QLabel) | Restzeit | `Restzeit oder verstrichene Zeit der aktuellen Messung.` |
| label_2 (QLabel) | Status: | `Status der Verbindung und Messung.` |
| line_4 (Line) | Trennlinie | `Trennung zwischen Status-LED und Werten.` |
| statusLED (QLabel) | Status-LED | `Farbige Statusanzeige (Rot = aus, Grün = bereit/aktiv).` |
| statusText (QLabel) | Status-Text | `Verbalisierte Statusmeldung des Geräts.` |
| currentCount (QLCDNumber) | Aktuell | `Anzeige des laufenden Messwerts.` |
| label_3 (QLabel) | Aktuell | `Überschrift für aktuellen Messwert.` |
| label_8 (QLabel) | GM-Spannung / V | `Aktuell gemessene Hochspannung.` |
| cVoltage (QLCDNumber) | Spannung Ist | Bereits vorhanden: `Aktuelle GM-Spannung.` |
| label_9 (QLabel) | Zähldauer / s | `Aktuelle Zähldauer laut Gerät.` |
| cDuration (QLCDNumber) | Dauer Ist | Bereits vorhanden: `Aktuelle eingestellte Zähldauer. 999 für unendllich.` |
| query_label (QLabel) | Abfragemodus | `Aktuell eingestellter Abfragemodus.` |
| cQueryMode (QLabel) | Abfragemodus Wert | Bereits vorhanden: `Aktuell eingestellter Abfragemodus der Zählergebnisse.` |
| label_12 (QLabel) | Zähl-Modus | `Aktuell verwendeter Zählmodus.` |
| cMode (QLabel) | Zählmodus Wert | Bereits vorhanden: `Aktuell eingestellter Zählmodus.` |
| label (QLabel) | Firmware-Version | `Firmware-Version des Geräts.` |
| cVersion (QLabel) | Firmware Wert | Bereits vorhanden: `GM-Zähler Firmware.` |
| label_11 (QLabel) | OpenBIS Code | `Zuordnungscode für OpenBIS.` |
| cOpenbis (QLabel) | OpenBIS Wert | `Aktuell ausgewählter OpenBIS-Code.` |
| menubar (QMenuBar) | Menüleiste | `Anwendungsmenüs (falls befüllt).` |
| statusBar (QStatusBar) | Statusbar | `Globale Statusmeldungen der Anwendung.` |

## `alert.ui`

| Widget (Typ) | Beschriftung/Name | Tooltip-Vorschlag |
| --- | --- | --- |
| Dialog (QDialog) | Alert | `Hinweis- oder Fehlermeldung bestätigen.` |
| buttonBox (QDialogButtonBox) | Ok/Abbrechen | `Bestätigt oder verwirft den Hinweis.` |
| textBox (QLabel) | Meldungstext | `Detailierte Meldung; Text kann kopiert werden.` |
