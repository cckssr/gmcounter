"""GMCounter Package.

A GUI application for GM-counter control and data acquisition.
"""

__version__ = "1.2.3"
__author__ = "C. Kessler"

# main is NOT imported here so that core/ and infrastructure/ tests can import
# gmcounter subpackages without triggering the PySide6 dependency.
# Use `python -m gmcounter` or the `gmcounter` entry point to launch the app.

__all__ = ["__version__", "__author__"]
