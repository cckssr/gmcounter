Troubleshooting
===============

Device not found / connection failed
-------------------------------------

1. Check the USB cable and try a different port.
2. On Linux/macOS, confirm the user is in the ``dialout`` / ``uucp`` group::

      sudo usermod -aG dialout $USER   # Linux
      # or: add /dev/tty.usbserial* to udev rules

3. Confirm the baud rate in the connection dialog matches the firmware
   (default: **1,000,000 baud**).
4. Run the application in demo mode first (no port selection needed) to confirm
   the software works independently of the hardware.

No data received after connecting
----------------------------------

The acquisition thread waits for the firmware's start marker (``0xFF × 6``)
before accepting data packets. If no marker arrives within ~2 s, the thread
emits ``connection_lost``.

* Confirm the firmware is running (the Arduino's RX/TX LEDs should flicker).
* Confirm ``demo_mode: false`` in ``gmcounter/config.json`` (if using real hardware).
* Try sending ``*RST`` via a serial terminal to reset the firmware state.

Reconnect loop / status bar shows "Wiederverbindung..."
---------------------------------------------------------

The reconnect FSM uses exponential backoff (500 ms → 1 s → 2 s → … → 16 s,
up to 8 attempts). Parameters are in ``config.json → connection``:

.. code-block:: json

   "connection": {
     "max_attempts": 8,
     "initial_delay_ms": 500,
     "max_delay_ms": 16000,
     "backoff_factor": 2.0
   }

Inputs are **not** disabled during reconnect — you can continue configuring
the next measurement. If all attempts fail, a status message in the Event Log
panel notes the session journal path so you can recover partial data.

Data recovery after a crash
-----------------------------

Every acquired data point is written to a crash-safe journal at::

   ~/.gmcounter/sessions/<timestamp>/journal.csv

If the application crashes before a formal save, the journal still contains all
received data. On the next startup, ``find_orphan_journals()`` reports sessions
without a ``finalized`` marker. You can open the CSV directly in any spreadsheet
application.

Demo mode not starting
-----------------------

If the mock device fails to start:

* Ensure ``MockGMCounter`` is available (it is excluded from the installed wheel
  but present in the cloned repository under
  ``gmcounter/infrastructure/mocks/``).
* Check for PTY creation errors in the console output (``pty.openpty()`` can fail
  if the system runs out of PTY slots).

Import / module errors
-----------------------

.. code-block:: text

   ModuleNotFoundError: No module named 'gmcounter'

Ensure the package is installed (``pip install -e .`` from the project root).
If installed, confirm the active Python environment is the one pip installed into.

Performance: plot lags at high event rates
-------------------------------------------

The default GUI update timer is 200 ms (``timers.gui_update_interval`` in config).
At very high event rates (> 10 kHz), increase it:

.. code-block:: json

   "timers": {
     "gui_update_interval": 500
   }

The acquisition thread always buffers data at full speed; only the plot refresh
rate is affected.
