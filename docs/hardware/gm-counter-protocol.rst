GM-Zähler Kommunikationsprotokoll
=================================

Es gibt zwei Protokollebenen:

* **Host ↔ Arduino (USB-Seriell, SCPI):** Die GUI spricht ausschließlich SCPI mit der Arduino-Firmware (siehe unten). Das ist die Schnittstelle, die ``GMCounterAdapter`` verwendet.
* **Arduino ↔ GM-Zähler-Platine (``Serial1``, 9600 Baud, Ein-Buchstaben-Befehle):** Die Firmware übersetzt die SCPI-Befehle in die Befehle der Platine. Diese Befehle sind ab dem Abschnitt „Kommunikationsprotokoll der GM-Platine" beschrieben und werden von der GUI nie direkt gesendet.

SCPI-Schnittstelle (Host ↔ Arduino)
-----------------------------------

Verbindung: USB-Seriell, 1 000 000 Baud (Standard, ``gm_counter.default_baud``). Jeder Befehl endet mit ``\n``. Befehle sind groß-/kleinschreibungsunabhängig. Kurz- und Langform sind gleichwertig (``CONF:VOLT`` = ``CONFIGURE:VOLTAGE``). Fehler landen in der Fehlerwarteschlange (``SYST:ERR?``). Ein Befehl mit ``?`` ist eine Abfrage.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Befehl
     - Funktion
   * - ``*IDN?``
     - Identifikation: ``TU Berlin,GM-Counter,<Seriennummer>,<Firmware-Version>``
   * - ``*RST``
     - (nur Befehl) Zurücksetzen auf Standardwerte: 500 V, Zählzeit-Modus 2, Einzelmodus, Stream aus
   * - ``*CLS``
     - (nur Befehl) Fehlerwarteschlange leeren
   * - ``*TST?, *OPC?``
     - Selbsttest (liefert 0), Operation abgeschlossen (liefert 1)
   * - ``SYST:ERR?``
     - Nächsten Fehler aus der Warteschlange lesen
   * - ``SYST:CLR``
     - (nur Befehl) Zählregister der GM-Platine löschen
   * - ``SYST:DEB [ON/OFF]``
     - Debug-Modus abfragen/setzen
   * - ``INIT``
     - (nur Befehl) Messung starten: Start-Marker, dann Binärdatenstrom (siehe unten)
   * - ``ABOR``
     - (nur Befehl) Messung stoppen
   * - ``CONF:VOLT [300..700]``
     - GM-Spannung in V abfragen/setzen
   * - ``CONF:TIME [0..5]``
     - Zählzeit-Modus abfragen/setzen: 0 = unendlich, 1 = 1 s, 2 = 10 s, 3 = 60 s, 4 = 100 s, 5 = 300 s
   * - ``CONF:REP [0/1]``
     - Wiederholmodus abfragen/setzen
   * - ``CONF:STR [0..4]``
     - Stream-Modus abfragen/setzen: 0 = aus, 4 = kontinuierliche Statusausgabe
   * - ``CONF:SPKR [0..3]``
     - (nur Befehl) Lautsprecher: 0 = aus, 1 = GM-Ton, 2 = Bereitschaftston, 3 = beide
   * - ``FETC:STAT?``
     - Status als CSV mit 6 Feldern: Zählung, letztes Ergebnis, Zählzeit, Wiederholung, Fortschritt, Spannung
   * - ``DIAG:STAT?``
     - Statistik der letzten Messung: Dauer in ms, Punkte, entprellt, Überläufe, TX-Drops
   * - ``DIAG:PASS``
     - (nur Befehl) Durchleitung zu ``Serial1`` umschalten (nur Diagnose)
   * - ``HELP?``
     - Befehlsübersicht der Firmware

**Binärer Datenstrom nach** ``INIT``: Start-Marker ``0xFF`` × 6, danach Datenpakete ``0xAA b0 b1 b2 b3 0x55`` (Zeit seit dem letzten Ereignis in Timer-Ticks, 32 Bit little-endian; Umrechnung in µs mit ``ticks_per_us``, Standard 48). Bei endlicher Zählzeit ohne Wiederholmodus sendet die Firmware am Ende ``0xEE`` × 6 und stoppt selbst. Während des Datenstroms dürfen keine weiteren Textbefehle gesendet werden; ``FETC:STAT?`` ist nur im Ruhezustand zulässig.

Kommunikationsprotokoll der GM-Platine" beschrieben und werden von der GUI nie direkt gesendet.

SCPI-Schnittstelle (Host ↔ Arduino)
-----------------------------------

Verbindung: USB-Seriell, 1 000 000 Baud (Standard, ``gm_counter.default_baud``). Jeder Befehl endet mit ``\n``. Befehle sind groß-/kleinschreibungsunabhängig. Kurz- und Langform sind gleichwertig (``CONF:VOLT`` = ``CONFIGURE:VOLTAGE``). Fehler landen in der Fehlerwarteschlange (``SYST:ERR?``). Ein Befehl mit ``?`` ist eine Abfrage.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Befehl
     - Funktion
   * - ``*IDN?``
     - Identifikation: ``TU Berlin,GM-Counter,<Seriennummer>,<Firmware-Version>``
   * - ``*RST``
     - (nur Befehl) Zurücksetzen auf Standardwerte: 500 V, Zählzeit-Modus 2, Einzelmodus, Stream aus
   * - ``*CLS``
     - (nur Befehl) Fehlerwarteschlange leeren
   * - ``*TST?, *OPC?``
     - Selbsttest (liefert 0), Operation abgeschlossen (liefert 1)
   * - ``SYST:ERR?``
     - Nächsten Fehler aus der Warteschlange lesen
   * - ``SYST:CLR``
     - (nur Befehl) Zählregister der GM-Platine löschen
   * - ``SYST:DEB [ON/OFF]``
     - Debug-Modus abfragen/setzen
   * - ``INIT``
     - (nur Befehl) Messung starten: Start-Marker, dann Binärdatenstrom (siehe unten)
   * - ``ABOR``
     - (nur Befehl) Messung stoppen
   * - ``CONF:VOLT [300..700]``
     - GM-Spannung in V abfragen/setzen
   * - ``CONF:TIME [0..5]``
     - Zählzeit-Modus abfragen/setzen: 0 = unendlich, 1 = 1 s, 2 = 10 s, 3 = 60 s, 4 = 100 s, 5 = 300 s
   * - ``CONF:REP [0/1]``
     - Wiederholmodus abfragen/setzen
   * - ``CONF:STR [0..4]``
     - Stream-Modus abfragen/setzen: 0 = aus, 4 = kontinuierliche Statusausgabe
   * - ``CONF:SPKR [0..3]``
     - (nur Befehl) Lautsprecher: 0 = aus, 1 = GM-Ton, 2 = Bereitschaftston, 3 = beide
   * - ``FETC:STAT?``
     - Status als CSV mit 6 Feldern: Zählung, letztes Ergebnis, Zählzeit, Wiederholung, Fortschritt, Spannung
   * - ``DIAG:STAT?``
     - Statistik der letzten Messung: Dauer in ms, Punkte, entprellt, Überläufe, TX-Drops
   * - ``DIAG:PASS``
     - (nur Befehl) Durchleitung zu ``Serial1`` umschalten (nur Diagnose)
   * - ``HELP?``
     - Befehlsübersicht der Firmware

**Binärer Datenstrom nach** ``INIT``: Start-Marker ``0xFF`` × 6, danach Datenpakete ``0xAA b0 b1 b2 b3 0x55`` (Zeit seit dem letzten Ereignis in Timer-Ticks, 32 Bit little-endian; Umrechnung in µs mit ``ticks_per_us``, Standard 48). Bei endlicher Zählzeit ohne Wiederholmodus sendet die Firmware am Ende ``0xEE`` × 6 und stoppt selbst. Während des Datenstroms dürfen keine weiteren Textbefehle gesendet werden; ``FETC:STAT?`` ist nur im Ruhezustand zulässig.

.. note::

   ``MEAS:STRT`` / ``MEAS:STP`` kennen nur ``GMCounterAdapter`` und der Mock; die Firmware implementiert sie nicht, und die GUI verwendet sie nicht.

Kommunikationsprotokoll der GM-Platine (``Serial1``)
----------------------------------------------------

Basierend auf der dänischen Anleitung für den GM-Zähler.

Datenstrom
----------

Das automatische Streaming sendet Daten als Text mit 9600 Bits pro Sekunde. Standardmäßig wird ein Komma zwischen den Werten eingefügt:

* aktuelle Zählnummer
* letztes abgeschlossenes Ergebnis
* Zählzeit
* Wiederholung (0/1)
* Fortschritt
* Spannung

**Fortschritt** bedeutet hier: Prozentsatz der gewählten Zählzeit. Oder (bei unendlicher Zählzeit): Verstrichene Zeit in Sekunden.

Kommunikationsprotokoll
-----------------------

Die Befehle an das Gerät bestehen aus einem Buchstaben, eventuell gefolgt von einer Zahl. Die möglichen Antworten des Gerätes hängen von dem Befehl ab.

Befehle
-------

Streaming-Steuerung (``b``)
~~~~~~~~~~~~~~~~~~~~~~~~~

Bei alleiniger Verwendung gibt der Befehl den Status zurück.
Wenn er mit einem Parameter 0-8 verwendet wird, ändert sich die Funktion wie folgt:

+---------+---------------------------------------------------------------+
| Befehl  | Funktion                                                      |
+=========+===============================================================+
| ``b0``  | Streaming stoppen                                             |
+---------+---------------------------------------------------------------+
| ``b1``  | Streaming-Daten senden, wenn die Messung bereit ist           |
+---------+---------------------------------------------------------------+
| ``b2``  | Streaming-Daten jetzt senden                                  |
+---------+---------------------------------------------------------------+
| ``b3``  | Jetzt senden und fortfahren, wenn bereit (b2+b1)              |
+---------+---------------------------------------------------------------+
| ``b4``  | Daten alle 50 ms senden                                       |
+---------+---------------------------------------------------------------+
| ``b5``  | Komma zwischen den Werten verwenden                           |
+---------+---------------------------------------------------------------+
| ``b6``  | Semikolon zwischen den Werten verwenden                       |
+---------+---------------------------------------------------------------+
| ``b7``  | Leerzeichen zwischen den Werten verwenden                     |
+---------+---------------------------------------------------------------+
| ``b8``  | Tabulator zwischen den Werten verwenden                       |
+---------+---------------------------------------------------------------+


**Standard**: ``b4`` und ``b5``. Wenn beim Einschalten des Geräts Start/Stop gedrückt und gehalten wird, entspricht dies ``b0``.

**Beispiel**: ``b1`` startet das Streaming, wenn die Messung bereit ist.

Unternehmensinformationen (``c``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rückgabe der Unternehmensinformation als Zeichenkette:

.. code-block:: text

   (c) copyright 2020 Frederiksen Scientific A/S


Registerwerte lesen (``d``)
~~~~~~~~~~~~~~~~~~~~~~~~~

Rückgabe des aktuellen Wertes aus dem Sekundärregister und Primärregister.

Ergebnisse senden (``e``)
~~~~~~~~~~~~~~~~~~~~~~~

Wenn der Befehl allein verwendet wird, wird der Status zurückgegeben.
Wenn der Befehl mit den Parametern 0-1 verwendet wird, ändert sich der Status wie folgt:


+---------+----------------------------------------------------------------------------------+
| Befehl  | Funktion                                                                         |
+=========+==================================================================================+
| ``e0``  | Zählnummern werden nicht automatisch gesendet                                    |
+---------+----------------------------------------------------------------------------------+
| ``e1``  | Zählnummern werden automatisch gesendet, wenn jede Zählperiode abgeschlossen ist |
+---------+----------------------------------------------------------------------------------+

**Beispiel**: ``e1`` aktiviert das automatische Senden der Zählnummern nach jeder Zählperiode.

Zählzeit (``f``)
~~~~~~~~~~~~~~

Bei alleiniger Verwendung gibt der Befehl die aktuelle Zählzeit in Sekunden zurück.
Wenn der Befehl mit den Parametern 0-5 verwendet wird, ändert sich die Zählzeit:


+---------+---------------+
| Befehl  | Zählzeit      |
+=========+===============+
| ``f0``  | Unendlich     |
+---------+---------------+
| ``f1``  | 1 Sekunde     |
+---------+---------------+
| ``f2``  | 10 Sekunden   |
+---------+---------------+
| ``f3``  | 60 Sekunden   |
+---------+---------------+
| ``f4``  | 100 Sekunden  |
+---------+---------------+
| ``f5``  | 300 Sekunden  |
+---------+---------------+

Andere Zählzeiten sind ungültig. Die Anzeigesymbole werden in Abhängigkeit von der Zählzeit aktiviert.

**Beispiel**: ``f3`` setzt die Zählzeit auf 60 Sekunden.

GM-Spannung (``j``)
~~~~~~~~~~~~~~~~~

Bei alleiniger Verwendung gibt der Befehl die aktuelle GM-Spannung in Volt zurück.
Wenn der Befehl mit den Parametern 400-700 verwendet wird, wird die GM-Spannung entsprechend gesetzt.

**Beispiel**: ``j520`` setzt die GM-Spannung auf 520V.

Einzel-/Wiederholungsmodus (``o``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wenn der Befehl allein verwendet wird, wird der Status zurückgegeben.
Bei Verwendung des Befehls mit den Parametern 0-1 ändert sich der Modus:

+---------+---------------+
| Befehl  | Modus         |
+=========+===============+
| ``o0``  | Einzeln       |
+---------+---------------+
| ``o1``  | Wiederholung  |
+---------+---------------+

**Beispiel**: ``o1`` setzt den Modus auf Wiederholung.

Start/Stopp der Zählung (``s``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wenn der Befehl allein verwendet wird, gibt er den Status zurück (0 = keine Zählung aktiv).
Mit einer Zahl kann eine Zählung gestartet oder gestoppt werden:


+---------+------------------------+
| Befehl  | Funktion               |
+=========+========================+
| ``s0``  | Stoppt die Zählung     |
+---------+------------------------+
| ``s1``  | Startet die Zählung    |
+---------+------------------------+

**Beispiel**: ``s1`` startet die Zählung.

Lautsprecher (``U``)
~~~~~~~~~~~~~~~~~~

Wenn der Befehl allein verwendet wird, gibt er den aktuellen Status des Lautsprechers zurück.
Mit einer Nummer wird der Lautsprecher entsprechend ein-/ausgeschaltet:

+---------+---------------------------------------------+
| Befehl  | Funktion                                    |
+=========+=============================================+
| ``U0``  | GM-Ton aus - Bereitschaftston aus           |
+---------+---------------------------------------------+
| ``U1``  | GM-Ton an - Bereitschaftston aus            |
+---------+---------------------------------------------+
| ``U2``  | GM-Ton aus - Bereitschaftston ein           |
+---------+---------------------------------------------+
| ``U3``  | GM-Ton ein - Bereitschaftston ein           |
+---------+---------------------------------------------+

**Beispiel**: ``U1`` schaltet den GM-Ton ein, ohne den Bereitschaftston zu aktivieren.

Versionsnummer (``v``)
~~~~~~~~~~~~~~~~~~~~

Rückgabe der Versionsnummer:

.. code-block:: text

   GM-Zähler. Firmware-Version xxxxxxxx


Zählnummern lesen (``w``)
~~~~~~~~~~~~~~~~~~~~~~~

Liest das Register, in das der Wert aus dem Primärregister nach Ende der Zählzeit kopiert wird.
Das Register wird gelöscht, wenn es gelesen wird.
Wenn das Register leer ist, wird "-1" zurückgegeben.

**Wichtig**: Um sicherzustellen, dass alle Werte übertragen werden, muss dieses Register mit einer Frequenz gelesen werden, die höher ist als die Zählzeitfrequenz.

Implementierung in GMCounter
--------------------------

Die GMCounter implementiert diese Befehle in der ``DeviceManager``-Klasse (siehe :doc:`../api`), die die serielle Kommunikation mit dem GM-Zähler verwaltet. Jeder Befehl wird durch eine entsprechende Methode gekapselt, um eine benutzerfreundliche API zu bieten.
