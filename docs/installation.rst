Installation
============

Systemvoraussetzungen
---------------------

* Python 3.10 oder höher
* USB-Port für GM-Zähler-Verbindung
* 500 MB freier Speicherplatz

Installation
------------

.. code-block:: bash

   # Repository klonen
   git clone https://github.com/cckssr/GMCounter.git
   cd GMCounter
   
   # Abhängigkeiten installieren
   pip install -r requirements.txt
   
   # Test-Start im Demo-Modus
   python main.py --demo

Abhängigkeiten
--------------

Automatisch installiert via requirements.txt:

* **PySide6**: GUI-Framework
* **matplotlib**: Datenvisualisierung  
* **pyserial**: Serielle Kommunikation
* **numpy**: Numerische Berechnungen
* **scipy**: Statistische Funktionen

Erste Einrichtung
-----------------

**Hardware-Setup:**
1. GM-Zähler per USB anschließen
2. GMCounter starten: ``python main.py``
3. COM-Port wird automatisch erkannt
4. Test-Messung durchführen

**Konfiguration anpassen:**
- Datei ``config.json`` bearbeiten
- Wichtige Parameter: Baudrate, Timeout, Puffergröße
- Neustart für Änderungen erforderlich

Fehlerbehebung
--------------

**COM-Port Probleme (Linux):**

.. code-block:: bash

   # Benutzerrechte setzen
   sudo usermod -a -G dialout $USER
   # Neuanmeldung erforderlich

**Modulprobleme:**

.. code-block:: bash

   # Fehlende Module nachinstallieren
   pip install --upgrade -r requirements.txt

**Debug-Informationen:**

.. code-block:: bash

   # Ausführliche Logs aktivieren
   python main.py --debug

Deinstallation
--------------

.. code-block:: bash

   # Projektverzeichnis löschen
   rm -rf GMCounter/

.. code-block:: bash

Virtuelle Umgebung erstellen (empfohlen)
========================================
python -m venv GMCounter-env

Virtuelle Umgebung aktivieren
=============================
Windows:
========
GMCounter-env\Scripts\activate
macOS/Linux:
============
source GMCounter-env/bin/activate

GMCounter installieren
====================
pip install GMCounter


Option 2: Quellcode-Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Repository klonen
=================
git clone https://github.com/cckssr/GMCounter.git
cd GMCounter

Abhängigkeiten installieren
===========================
pip install -r requirements.txt

Anwendung starten
=================
python main.py


Option 3: Download-Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Laden Sie die neueste Version von der `Releases-Seite <https://github.com/cckssr/GMCounter/releases>`_ herunter
2. Entpacken Sie das Archiv
3. Installieren Sie die Abhängigkeiten:

.. code-block:: bash

pip install -r requirements.txt


Abhängigkeiten
--------------

Die folgenden Python-Pakete werden benötigt:

.. code-block:: text

PySide6>=6.5.0
matplotlib>=3.7.0
numpy>=1.24.0
pyserial>=3.5


Vollständige Abhängigkeitsliste
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Anzeigen aller installierten Abhängigkeiten
===========================================
pip list


Erste Einrichtung
-----------------

1. Konfiguration erstellen
~~~~~~~~~~~~~~~~~~~~~~~~~~

Beim ersten Start wird automatisch eine Konfigurationsdatei erstellt:

.. code-block:: json

{
  "debug_level": 1,
  "auto_connect": false,
  "default_port": "",
  "theme": "light",
  "language": "de"
}


2. Gerätetreiber installieren
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Windows
^^^^^^^

1. Laden Sie die Arduino-Treiber von der `offiziellen Website <https://www.arduino.cc/en/software>`_ herunter
2. Installieren Sie die Treiber
3. Starten Sie den Computer neu

macOS
^^^^^

Keine zusätzlichen Treiber erforderlich. macOS erkennt Arduino-Geräte automatisch.

Linux
^^^^^

.. code-block:: bash

Benutzer zur dialout-Gruppe hinzufügen
======================================
sudo usermod -a -G dialout $USER

Abmelden und wieder anmelden
============================
logout


3. Geräteverbindung testen
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Schließen Sie Ihren GM-Zähler an
2. Starten Sie GMCounter
3. Gehen Sie zu "Gerät" → "Verbinden"
4. Wählen Sie den entsprechenden Port aus

Fehlerbehebung
--------------

Häufige Probleme
~~~~~~~~~~~~~~~~

"Kein Modul namens 'PySide6' gefunden"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

PySide6 installieren
====================
pip install PySide6


"Port nicht gefunden" oder "Zugriff verweigert"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Windows:**

* Überprüfen Sie den Geräte-Manager
* Installieren Sie die Arduino-Treiber neu

**macOS:**

* Überprüfen Sie die Systemeinstellungen → Sicherheit
* Erlauben Sie den Zugriff auf USB-Geräte

**Linux:**

.. code-block:: bash

Benutzerrechte überprüfen
=========================
groups $USER

Sollte "dialout" enthalten
==========================
sudo usermod -a -G dialout $USER


"Matplotlib-Backend-Fehler"
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

Zusätzliche Abhängigkeiten installieren
=======================================
Ubuntu/Debian:
==============
sudo apt-get install python3-tk

macOS:
======
brew install python-tk

Windows: Meist nicht erforderlich
=================================


Debug-Modus aktivieren
~~~~~~~~~~~~~~~~~~~~~~

Für detaillierte Fehlersuche:

.. code-block:: bash

Umgebungsvariable setzen
========================
export GMCounter_DEBUG=1

Oder in der Konfigurationsdatei
===============================
{
    "debug_level": 3
}


Deinstallation
--------------

Pip-Installation
~~~~~~~~~~~~~~~~

.. code-block:: bash

pip uninstall GMCounter


Quellcode-Installation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Verzeichnis löschen
===================
rm -rf GMCounter

Virtuelle Umgebung entfernen
============================
rm -rf GMCounter-env


Konfigurationsdateien entfernen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Windows:
========
del /q "%APPDATA%\GMCounter\*"

macOS:
======
rm -rf ~/Library/Application\ Support/GMCounter

Linux:
======
rm -rf ~/.config/GMCounter


Aktualisierung
--------------

Pip-Installation
~~~~~~~~~~~~~~~~

.. code-block:: bash

pip install --upgrade GMCounter


Quellcode-Installation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

cd GMCounter
git pull origin main
pip install -r requirements.txt


Verifizierung
-------------

Nach der Installation können Sie die Funktionalität testen:

.. code-block:: bash

Version anzeigen
================
python -c "import GMCounter; print(GMCounter.__version__)"

Testlauf im Demo-Modus
======================
python main.py --demo


Unterstützung
-------------

Bei Installationsproblemen:

* Konsultieren Sie die `Fehlerbehebung <troubleshooting>`_
* Öffnen Sie ein `Issue auf GitHub <https://github.com/cckssr/GMCounter/issues>`_
* Prüfen Sie die `FAQ <faq>`_

Nächste Schritte
----------------

Nach erfolgreicher Installation:

1. Lesen Sie den `Schnellstart-Guide <quickstart>`_
2. Konfigurieren Sie die `Grundeinstellungen <configuration>`_
3. Verbinden Sie Ihr `Gerät <device-connection>`_
