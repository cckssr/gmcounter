Installation
============

Requirements
------------

* Python 3.10 or newer
* PySide6 ≥ 6.5
* pyserial, numpy, scipy, pyqtgraph, pillow

All runtime dependencies are declared in ``pyproject.toml`` and installed
automatically by pip.

From the repository (no clone needed)
--------------------------------------

.. code-block:: bash

   pip install "git+https://github.com/cckssr/gmcounter.git"

Pin a specific release:

.. code-block:: bash

   pip install "git+https://github.com/cckssr/gmcounter.git@v2.1.2"

From a local clone
------------------

.. code-block:: bash

   git clone https://github.com/cckssr/gmcounter.git
   cd gmcounter
   pip install .

Development install (editable, with linting and test tools):

.. code-block:: bash

   pip install -e ".[dev]"

Running the application
-----------------------

After installation, start the GUI with:

.. code-block:: bash

   gmcounter

or:

.. code-block:: bash

   python -m gmcounter

The connection dialog opens first. Select a serial port or accept the default
demo-mode mock port. No physical hardware is needed — demo mode is on by default
(``demo_mode: true`` in ``gmcounter/config.json``).

Hardware requirements
---------------------

For hardware-backed operation you need:

* An **Arduino UNO R4 Minima** running the matching firmware from the
  ``firmware/`` directory.
* A **Geiger-Müller tube** connected to the Arduino's event-input circuit.
* A **USB cable** connecting the Arduino to the host at 1,000,000 baud.

See :doc:`hardware/firmware` for building and flashing the firmware.
