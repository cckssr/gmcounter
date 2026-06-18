Firmware
========

The GMCounter firmware is a `PlatformIO <https://platformio.org/>`_ project
targeting the **Arduino UNO R4 Minima** (Renesas RA4M1, 48 MHz). It lives in
the ``firmware/`` directory of the repository.

Architecture overview
----------------------

The firmware has two communication layers:

1. **Host ↔ firmware (USB CDC, ``Serial``):** SCPI commands at 1 Mbaud.
   The Python application sends SCPI commands and reads responses on this port.

2. **Firmware ↔ GM counter module (UART, ``Serial1``):** Single-character
   legacy commands to the downstream Frederiksen-style GM counter hardware.
   The firmware translates between the two layers.

Source layout::

   firmware/
     src/
       main.cpp          Main loop: SCPI line reader and dispatcher
       scpi.cpp / .h     SCPI parser and command handlers
       gm_core.cpp / .h  GM counter state machine and data accumulation
       state.cpp / .h    Global device state (gmState)
       config.h          Compile-time constants and limits
     test/
       test_scpi_parser/     Unity test suite for SCPI parsing
       test_scpi_dispatch/   Unity test suite for command dispatch
       test_error_queue/     Unity test suite for the error queue
       test_gm_core/         Unity test suite for the GM core logic
       Arduino.h             Arduino API stubs for native builds
     platformio.ini

PlatformIO environments
------------------------

.. list-table::
   :header-rows: 1

   * - Environment
     - Purpose
   * - ``uno_r4_minima``
     - Generic build (``DEVICE_SERIAL="UNKWN"``)
   * - ``uno_E20134`` / ``uno_E97675`` / …
     - Device-specific build with baked-in serial number
   * - ``native``
     - Host-side unit tests (no hardware needed)

Build a specific environment:

.. code-block:: bash

   pio run -e uno_E20134 --target upload

The per-device environments all extend ``uno_r4_minima`` and differ only in the
``DEVICE_SERIAL`` build flag, which is returned by ``*IDN?``.

Native unit tests
-----------------

Run on the host without any microcontroller:

.. code-block:: bash

   pio test -e native

Each ``firmware/test/<suite>/`` directory compiles independently and includes
exactly the ``.cpp`` files it needs. The ``firmware/test/Arduino.h`` shim stubs
``Serial``, ``String``, ``millis()``, ``delay()``, etc. so the logic can compile
without hardware headers.

SCPI command reference
-----------------------

Commands use IEEE 488.2 syntax. Both short (``CONF:VOLT``) and long
(``CONFIGURE:VOLTAGE``) forms are accepted. A query adds ``?``; a command
form sets a value.

IEEE 488.2 Common Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``*IDN?``
     - query only
     - Device identification string: ``MFR,MODEL,SERIAL,FW_VERSION``
   * - ``*RST``
     - command only
     - Reset device to defaults, stop acquisition, clear error queue
   * - ``*CLS``
     - command only
     - Clear the SCPI error queue
   * - ``*TST?``
     - query only
     - Self-test (always returns 0)
   * - ``*OPC?``
     - query only
     - Operation complete (always returns 1)

CONFigure subsystem
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``CONF:VOLT [300..900]``
     - query/set
     - High voltage in V. Short: ``CONF:VOLT``, long: ``CONFIGURE:VOLTAGE``
   * - ``CONF:TIME [0..9]``
     - query/set
     - Counting time mode index (0 = continuous). ``CONFIGURE:TIME``
   * - ``CONF:REP [ON|OFF|1|0]``
     - query/set
     - Repeat mode. ``CONFIGURE:REPEAT``
   * - ``CONF:STR [0..4]``
     - query/set
     - Stream mode (4 = continuous binary stream). ``CONFIGURE:STREAM``
   * - ``CONF:SPKR [0..3]``
     - command only
     - Speaker mode: 0 = off, 1 = click, 2 = tone, 3 = both. ``CONFIGURE:SPEAKER``

INITiate / ABORt
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``INIT``
     - command only
     - Start acquisition. Arms end-of-period detection if counting time > 0 and
       repeat is off. Sends the binary start marker (``0xFF × 6``).
   * - ``ABOR``
     - command only
     - Stop acquisition. Sends the binary end-of-period marker (``0xEE × 6``).

FETCh subsystem
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``FETC:STAT?``
     - query only
     - GM counter status as CSV: ``count, last_count, counting_time, repeat,
       progress, voltage``

SYSTem subsystem
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``SYST:ERR?``
     - query only
     - Pop the next error from the error queue (FIFO). Returns
       ``0,"No error"`` when empty.
   * - ``SYST:CLR``
     - command only
     - Clear the GM counter's event register (``SYSTEM:CLEAR``)
   * - ``SYST:DEB [ON|OFF|1|0]``
     - query/set
     - Enable or disable debug output on ``Serial`` (``SYSTEM:DEBUG``)
   * - ``SYST:VERS?``
     - query only
     - SCPI version string (returns ``"1999.0"``)

DIAGnostic subsystem
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Command
     - Form
     - Description
   * - ``DIAG:STAT?``
     - query only
     - Last-acquisition statistics as CSV
   * - ``DIAG:PASS``
     - toggle
     - Toggle ``Serial1`` passthrough mode — relays host bytes directly to the
       downstream GM hardware for diagnostics

HELP command
~~~~~~~~~~~~~

``HELP?`` — print all available commands to ``Serial``. Equivalent to the table
above.

Binary data stream
------------------

When ``INIT`` is sent, the firmware emits a binary stream on ``Serial`` (not text
SCPI responses). See :doc:`gm-counter-protocol` for the single-character commands
and :doc:`timing` for the binary packet format.

In brief:

* **Start marker:** ``0xFF × 6`` — acquisition thread discards bytes before this
* **Data packet:** ``[0xAA, b0, b1, b2, b3, 0x55]`` — b0..b3 = inter-event
  delta in RA4M1 DWT cycle-counter ticks; divide by ``ticks_per_us`` (48) for µs
* **End-of-period:** ``0xEE × 6`` — firmware signals counting period complete

Firmware versioning
--------------------

The firmware version is baked in at compile time via the ``FW_VERSION`` build flag
in ``platformio.ini`` (current: ``"2.2.1"``). It is reported by ``*IDN?`` and
stored in ``gmcounter/config.json → de.application.version``.

The host application version (``pyproject.toml``) and the firmware version are
managed independently. Compatibility is documented in the release notes.
