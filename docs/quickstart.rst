Quickstart
==========

This guide gets you from installation to your first measurement in five minutes.
No hardware is required — demo mode uses a software-emulated serial port.

1. Install
----------

.. code-block:: bash

   pip install "git+https://github.com/cckssr/gmcounter.git"

2. Start the application
------------------------

.. code-block:: bash

   gmcounter

3. Connect in demo mode
-----------------------

The **Connection** dialog opens automatically.

* Leave the port set to ``Demo (mock device)``.
* Click **Verbinden**.

The main window opens with the ``Zeitverlauf`` (time-series) tab active.

4. Start a measurement
----------------------

Click **Start**. Live event timings appear in the plot within a few seconds.
The status bar shows *Messung läuft*.

5. Switch views
---------------

Three views share the same data:

* **Zeitverlauf** — live time-series plot
* **Histogramm** — distribution of inter-event intervals
* **Liste** — scrollable table of raw values

6. Stop and export
------------------

Click **Stop**, then **Speichern**. A file dialog lets you choose where to save
the CSV file and its JSON sidecar (``_MD.json``).

7. Experiment tabs
------------------

Additional experiment tabs are available:

* **Abstandsgesetz** — 1/r² distance law: sweep a source distance and collect one
  measurement per distance point.
* **Spannungskurve** — Geiger plateau / voltage response: sweep the detector
  voltage.
* **Intervallwiederholung** — MCS-style: slice one continuous acquisition into
  equal-width time bins.

8. Configuration
----------------

All tuneable parameters live in ``gmcounter/config.json`` under the ``"de"`` key.
See :doc:`configuration` for the full reference.

To use a real device, set ``"demo_mode": false`` in the config and select the
correct serial port in the connection dialog.
