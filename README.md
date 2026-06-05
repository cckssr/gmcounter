# GMCounter

GMCounter is a PySide6 desktop application for a Geiger-Müller counter connected over USB serial. It records inter-event timings in microseconds, presents the data live, and supports analysis workflows for random-number research and detector characterization.

## What It Does

GMCounter is designed to be the control and analysis layer for a GM counter setup. The application lets you connect to the device, start and stop measurements, inspect the data as it arrives, and export results for later analysis.

Typical capabilities include:

- live time-series plotting of incoming events
- histogram and tabular views of measurements
- measurement export to CSV with a sidecar metadata JSON file
- parameter-sweep workflows for experiments such as distance-law and voltage-response measurements
- a demo/testing path that uses the repository's mock serial device when available

## Installation

### Install from this repository with pip

You can install the package directly from the Git repository without cloning it first:

```bash
pip install "git+https://github.com/cckssr/gmcounter.git"
```

If you want a specific branch or revision, pin it explicitly:

```bash
pip install "git+https://github.com/cckssr/gmcounter.git@main"
```

### Install from a local clone

If you already have the repository checked out locally, install the current working tree with pip:

```bash
pip install .
```

For development, install the editable package with the development extras:

```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.10 or newer
- PySide6
- pyserial
- numpy, scipy, matplotlib, pyqtgraph, pillow
- a GM counter connected over USB serial for hardware-backed operation

## Running The Application

After installation, start the GUI with either of the following commands:

```bash
gmcounter
```

or

```bash
python -m gmcounter
```

When the application launches, it opens the connection dialog first. From there you can choose a serial device or use the demo/testing path when the mock serial port helper is available.

## Project Structure

- gmcounter/core/: pure domain logic, data models, exports, and services
- gmcounter/infrastructure/: serial adapters, persistence, configuration, logging, and Qt-free helpers
- gmcounter/ui/: PySide6 user interface, controllers, dialogs, tabs, and widgets
- gmcounter/pyqt/: generated Qt UI code from the designer files
- tests/: unit, integration, and UI tests
- docs/: Sphinx documentation and user guides

## Main Features

The application is organized around a small number of focused workflows:

1. Connect to a device through the serial connection dialog.
2. Configure voltage, counting time, and measurement mode.
3. Start acquisition and monitor the live signal in the main window.
4. Switch between time-series, histogram, and list views for the same data set.
5. Save or export results for later processing.
6. Use sweep-style tabs for experiments that collect multiple measurements across changing parameters.

## Testing

Run the full test suite with pytest:

```bash
pytest
```

Run the package tests with coverage:

```bash
pytest --cov=gmcounter
```

UI tests require Qt to run headlessly:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/ui/
```

## Documentation

The full documentation lives in the docs folder and is published at [gmcounter.readthedocs.io](https://gmcounter.readthedocs.io).

## License

MIT License. See [LICENSE](LICENSE).
