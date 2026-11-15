# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

import logging
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)


class SaveState:
    """Track unsaved-data state and the configured base directory.

    This is *not* a writer — all actual I/O goes through
    ``infrastructure.save_service.write_export`` /
    ``infrastructure.save_service.SaveService``.

    Responsibilities:
    - Remember ``base_dir`` for default save-dialog folder suggestions.
    - Expose ``has_unsaved`` / ``mark_saved`` / ``mark_unsaved`` so the UI
      can prompt the user before discarding data.
    """

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        tk_designation: str = "TKXX",
    ) -> None:
        if base_dir is None:
            base_dir = Path.home() / "Documents" / "GMCounter"
        if isinstance(base_dir, str):
            base_dir = Path.home() / "Documents" / base_dir

        self.base_dir = Path(base_dir)
        # tk_designation kept for API symmetry; not used in this class.
        self.tk_designation = tk_designation
        self._unsaved = False

        _log.info("SaveState base dir: %s", self.base_dir)
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            _log.error("Failed to create base dir %s: %s", self.base_dir, exc)

    # ------------------------------------------------------------------
    # Unsaved-state tracking

    def has_unsaved(self) -> bool:
        return self._unsaved

    def mark_saved(self) -> None:
        self._unsaved = False

    def mark_unsaved(self) -> None:
        self._unsaved = True


class MeasurementStateService:
    """Track whether a measurement is currently active.

    Pure domain state — no I/O, no hardware references.
    """

    def __init__(self) -> None:
        self._measurement_active = False

    @property
    def measurement_active(self) -> bool:
        return self._measurement_active

    def start_measurement(self) -> None:
        self._measurement_active = True
        _log.debug("MeasurementStateService: started")

    def stop_measurement(self) -> None:
        self._measurement_active = False
        _log.debug("MeasurementStateService: stopped")

    def reset(self) -> None:
        self._measurement_active = False
        _log.debug("MeasurementStateService: reset")
