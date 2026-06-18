User Interface
==============

GMCounter's main window is organised around a tab bar at the top and three
shared control buttons (**Start**, **Stop**, **Speichern**) at the bottom.

Connection dialog
-----------------

The connection dialog opens automatically on startup. Select a serial port and
baud rate (default 1,000,000), or use the **Demo (mock device)** option to
run without hardware. Click **Verbinden** to connect.

Once connected, the main window opens.

Main window layout
------------------

The main window has three areas:

* **Tab bar** — switches between experiment views
* **Central area** — the active experiment's plot, histogram, or table
* **Status bar** — one-line transient status (connection state, measurement
  progress, save confirmation)
* **Event Log** (dockable panel) — timestamped scrollback of every status
  message; survives the status bar's 3–8 s auto-clear

Experiment tabs
---------------

GMTimingTab — Zeitverlauf / Histogramm / Liste
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default GM timing experiment contributes three sub-views of the same
measurement session. Switch between them using the tabs inside the tab bar.

* **Zeitverlauf** — real-time line plot of inter-event intervals (µs) vs index
* **Histogramm** — live histogram of the inter-event distribution
* **Liste** — scrollable table of every acquired data point

All three views are reset when **Start** is clicked for a new measurement. Data
is retained across tab switches within the same session.

Abstandsgesetz (Distance Law)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sweep a radioactive source distance and collect one timing measurement per
distance. Each completed measurement is appended as a row in the summary table
and a point in the 1/r² summary plot.

Enter the distance in the **Probenabstand** spinbox, then click **Start**. After
the firmware stops the acquisition (finite counting time) click **Start** again
for the next distance point. Click **Speichern** after all points are collected
to save the summary CSV and the individual timing CSVs.

Spannungskurve (Voltage Response)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sweep the detector high voltage and record the count rate at each voltage setting.
The current voltage is read back from the device and injected automatically into
the export metadata. Controls are otherwise the same as for the distance-law tab.

Intervallwiederholung (Interval Repeat / MCS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Slice one continuous acquisition into *R* equal-width time intervals. Configure
**Intervallbreite** (µs) and **Wiederholungen** (R), then click **Start**. A bar
chart shows the count per interval as events arrive.

Shared controls
---------------

Start / Stop / Speichern buttons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These three buttons are shared across all tabs. Their behaviour depends on which
tab is active:

* On **GMTimingTab** sub-views — control a single timing measurement session.
* On a **sweep tab** — **Start** begins one parameter point; **Stop** ends it
  without saving; **Speichern** saves the full sweep summary and resets.

Status bar and Event Log
~~~~~~~~~~~~~~~~~~~~~~~~

The status bar shows the most recent status message for 3–8 s. The Event Log
panel (dock, right side) keeps a timestamped record of every message for the
current session. Open or close it from the View menu.

AppController signal contract
------------------------------

The controller exposes the following Qt signals; UI components subscribe to
these and never poll the device directly:

.. code-block:: python

   connection_status_changed = Signal(str, str)   # (state, detail)
   reconnect_attempt         = Signal(int, float)  # (attempt_n, delay_s)
   reconnect_succeeded       = Signal()
   connection_lost           = Signal()
   measurement_started       = Signal()
   measurement_stopped       = Signal()
   frames_ready              = Signal(list)        # list[Frame]
   voltage_updated           = Signal(float)
   count_time_updated        = Signal(int)

See :doc:`api` for the full API reference and :doc:`architecture` for the
design rules that govern this contract.
