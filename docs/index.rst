GMCounter Documentation
=======================

GMCounter is a PySide6 desktop application for a Geiger-Müller counter connected
over USB serial. It records inter-event timings in microseconds, presents the data
live, and supports analysis workflows for random-number research and detector
characterisation.

No hardware required to try it — demo mode is on by default.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   quickstart
   installation
   configuration
   user-interface
   data-analysis

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture
   principles
   hardware/gm-counter-protocol
   hardware/firmware
   hardware/timing

.. toctree::
   :maxdepth: 1
   :caption: Developer Reference

   api
   troubleshooting
   faq

Project info
------------

* **Author:** Cedric Kessler
* **License:** MIT
* **Source:** https://github.com/cckssr/gmcounter
* **Version:** 2.1.2
