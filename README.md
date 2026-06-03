# GMCounter

GMCounter is a PySide6 desktop application for a Geiger-Müller counter connected over USB serial. It measures inter-event timing in microseconds and is used for random number generation research.

## Quick Start

Install the package in editable mode for development:

```bash
pip install -e ".[dev]"
```

Run the application:

```bash
gmcounter
```

Or start it as a module:

```bash
python -m gmcounter
```

## Testing

Run the full test suite:

```bash
pytest
```

Run the package tests with coverage:

```bash
pytest --cov=gmcounter
```

## Project Structure

- `gmcounter/core/`: pure application logic and data models
- `gmcounter/infrastructure/`: device adapters, persistence, and Qt-free services
- `gmcounter/ui/`: PySide6 presentation layer
- `gmcounter/pyqt/`: generated Qt UI code
- `tests/`: automated tests
- `docs/`: Sphinx documentation

## Documentation

Project documentation is published at [gmcounter.readthedocs.io](https://gmcounter.readthedocs.io).

## License

MIT License. See [LICENSE](LICENSE).
