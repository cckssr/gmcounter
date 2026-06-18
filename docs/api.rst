API Reference
=============

Autodoc reference generated from Python docstrings. See :doc:`architecture`
for how the layers interact.

Core — Pure Domain Logic
------------------------

The ``core`` layer contains pure Python: no Qt, no serial, no file I/O.
All modules here are testable without any external dependency.

.. automodule:: gmcounter.core.models
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.export
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.services
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.reconnect_service
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.duration
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.interval_binning
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.utils
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.core.ports
   :members:
   :undoc-members:
   :show-inheritance:

Infrastructure — Adapters
--------------------------

The ``infrastructure`` layer provides device adapters, file I/O, configuration,
and logging. Qt is restricted to ``qt_threads.py`` — every other module in this
layer is testable without a running ``QApplication``.

.. automodule:: gmcounter.infrastructure.config
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.logging
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.serial_device
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.device_manager
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.packet_parser
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.qt_threads
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.session_journal
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.save_service
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.devices.gm_counter
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.infrastructure.modules.registry
   :members:
   :undoc-members:
   :show-inheritance:

UI — Presentation Layer
------------------------

The ``ui`` layer contains all PySide6 windows, tabs, widgets, dialogs, and
the single AppController. No domain logic belongs here.

Controllers
~~~~~~~~~~~

.. automodule:: gmcounter.ui.controllers.app_controller
   :members:
   :undoc-members:
   :show-inheritance:

Windows and Dialogs
~~~~~~~~~~~~~~~~~~~~

.. automodule:: gmcounter.ui.windows.main_window
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.dialogs.connection
   :members:
   :undoc-members:
   :show-inheritance:

Experiment Tabs
~~~~~~~~~~~~~~~~

.. automodule:: gmcounter.ui.tabs.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.registry
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.gm_timing_tab
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.parameter_sweep_base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.distance_law_tab
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.voltage_response_tab
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.tabs.interval_repeat_tab
   :members:
   :undoc-members:
   :show-inheritance:

Widgets
~~~~~~~~

.. automodule:: gmcounter.ui.widgets.plot
   :members:
   :show-inheritance:

.. automodule:: gmcounter.ui.widgets.event_log_panel
   :members:
   :undoc-members:
   :show-inheritance:

Common Utilities
~~~~~~~~~~~~~~~~~

.. automodule:: gmcounter.ui.common.statusbar
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.common.dialogs
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.common.file_dialogs
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: gmcounter.ui.resources.stylesheet
   :members:
   :undoc-members:
   :show-inheritance:
