Data Analysis and Export
========================

Every experiment tab can export its results via the **Speichern** button or a
file dialog. All exports use the same ``TabExport`` schema and produce two files.

Export format
-------------

Pressing **Speichern** writes two files:

CSV file
~~~~~~~~

Columns vary by experiment:

* **GM Timing:** ``Index``, ``Value (µs)``, ``Time``
* **Distance Law / Voltage Response:** parameter, count, rate (1/s), duration (s), timestamp
* **Interval Repeat:** interval index, count, per-interval timing CSV

JSON sidecar (``_MD.json``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dublin-Core-style metadata dictionary written alongside the CSV:

.. code-block:: json

   {
     "dc:date": "2025-04-01",
     "dc:creator": "SoSe2025_Mo_A",
     "dc:title": "Ra-226",
     "start_time": "2025-04-01T10:00:00",
     "end_time":   "2025-04-01T10:05:00",
     "radioactive_sample": "Ra-226",
     "subgroup": "Gruppe1"
   }

Save path composition
---------------------

The path is composed by ``core.export.compose_save_path()`` from:

* ``base_dir`` (configured in ``config.json → save.base_folder``)
* Today's date (``YYYY_MM_DD``)
* A two-digit index that increments automatically
* The experiment's ``filename_hint`` (e.g. ``gm_timing``, ``abstandsgesetz``)
* Optional filename tokens (e.g. a Dropbox folder structure)

No I/O happens in ``core.export`` — the infrastructure layer
(``infrastructure.save_service``) handles all filesystem access.

Crash-safe session journal
--------------------------

Every acquired data point is appended to a crash-safe journal at:

.. code-block::

   ~/.gmcounter/sessions/<timestamp>/journal.csv

The journal is fsynced every ~1 s. If the application crashes before a formal
save, the journal records all received data. On the next startup,
``find_orphan_journals()`` reports any sessions without a ``finalized`` marker.

TabExport schema
----------------

The ``TabExport`` dataclass is the contract between experiment tabs and the
infrastructure writer:

.. autoclass:: gmcounter.core.export.TabExport
   :members:
   :no-undoc-members:
   :no-index:

.. autofunction:: gmcounter.core.export.compose_save_path
   :no-index:

.. autofunction:: gmcounter.core.export.build_gm_tab_export
   :no-index:

Interval binning (MCS mode)
---------------------------

The ``IntervalBinner`` algorithm is a pure-Python MCS-style binner that can
be reused in other data-acquisition projects:

.. autoclass:: gmcounter.core.interval_binning.IntervalBinner
   :members:
   :no-index:

.. autoclass:: gmcounter.core.interval_binning.IntervalBins
   :members:
   :no-index:

Duration trimming
-----------------

``accumulate_and_trim()`` is a pure budget-trimming utility that keeps points
whose cumulative device-time does not exceed a target. Used to honour a finite
counting time declared in config without needing a hardware timer:

.. autofunction:: gmcounter.core.duration.accumulate_and_trim
   :no-index:
