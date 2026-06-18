FAQ
===

Can I use GMCounter without a Geiger-Müller counter?
------------------------------------------------------

Yes. Demo mode (``demo_mode: true`` in ``gmcounter/config.json``) is on by
default and uses a software-emulated serial port (``MockGMCounter``). All
analysis, export, and parameter-sweep features work identically.

To toggle demo mode, edit ``gmcounter/config.json``:

.. code-block:: json

   "connection": {
     "demo_mode": false
   }

Which Arduino board is supported?
----------------------------------

The firmware is written for the **Arduino UNO R4 Minima** (Renesas RA4M1,
48 MHz). The ``ticks_per_us`` setting in ``config.json → acquisition`` must
match the firmware's timer frequency (48 for a 48 MHz clock):

.. code-block:: json

   "acquisition": {
     "ticks_per_us": 48
   }

See :doc:`hardware/firmware` for the full firmware documentation.

Where are saved files stored?
------------------------------

By default, CSV files and JSON sidecars are written to::

   ~/Documents/GMCounter/

The base folder is configured in ``config.json → save.base_folder``. Each export
gets a date-stamped filename (``YYYY_MM_DD-01-gm_timing.csv``).

The crash-safe session journal lives at::

   ~/.gmcounter/sessions/<timestamp>/journal.csv

What is the binary protocol?
------------------------------

See :doc:`hardware/gm-counter-protocol` for the single-character legacy command
set and :doc:`hardware/timing` for the binary packet format used during data
streaming.

In brief:

* Start marker: ``0xFF × 6`` — acquisition thread ignores bytes before this
* Data packet: ``[0xAA, b0, b1, b2, b3, 0x55]`` — b0..b3 are the inter-event
  delta in firmware timer ticks (LE 32-bit); divide by ``ticks_per_us`` for µs
* End-of-period: ``0xEE × 6`` — firmware signals that a finite counting time
  has elapsed

How do I add a new experiment tab?
------------------------------------

See :doc:`architecture` section §6 (Extensibility: experiment tabs as a plugin
point). Short version:

* **Frame-based tab** (receives every data point live): subclass ``PlotTabBase``,
  implement ``build()`` and ``on_frames()``, call ``TabRegistry.register(MyTab)``.
* **Parameter-sweep tab** (one measurement per parameter value): subclass
  ``ParameterSweepTabBase``, set six class attributes, do NOT register in
  ``TabRegistry`` — wire it explicitly in ``MainWindow.__init__``.

Is there an API / how do I use the core modules in another project?
---------------------------------------------------------------------

Several core modules are designed as reusable building blocks:

* :class:`~gmcounter.core.interval_binning.IntervalBinner` — MCS-style binning
* :func:`~gmcounter.core.duration.accumulate_and_trim` — budget-trimming for
  finite counting time
* :class:`~gmcounter.infrastructure.packet_parser.PacketParser` — binary
  packet decoder
* :class:`~gmcounter.core.reconnect_service.ConnectionRetryService` — exponential
  backoff reconnect loop

See :doc:`api` for the full autodoc reference.
