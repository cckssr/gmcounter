# Layer: ui/controllers — SessionController: what Start / Stop / Save / Reset mean.
#
# The shared buttons serve every experiment tab. The controller runs the measurement
# session of the selected tab (single, parameter sweep or interval series), guards unsaved
# data, injects the metadata and writes the summary and detail files. It branches on
# ``tab.session_kind``, never on concrete tab classes, and talks to the user only through
# the injected prompt, so it can be tested without a window.

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import QObject, Signal

import gmcounter

from ...infrastructure.config import AppConfig
from ...infrastructure.save_service import write_export

if TYPE_CHECKING:
    from ..common.prompt import Prompt
    from ..tabs.base import PlotTabBase

_log = logging.getLogger(__name__)

STATUS_MESSAGE_MS = 5000
SAVED_MESSAGE_MS = 3000


class SessionController(QObject):
    """Owns the measurement sessions behind the shared Start / Stop / Save / Reset buttons.

    Outbound signals (the window forwards them to its panels):
        buttons_changed(start, stop, reset, save)  enabled state of the four buttons
        status_changed(text, colour)               status indicator (colour: green, blue, ...)
        settings_locked(bool)                      device controls are locked while measuring
        tabs_locked(tab | None)                    only ``tab`` stays usable; None unlocks all
        progress_cleared()                         reset the progress display
        message(text, duration_ms)                 transient status-bar message

    Wiring contract: connect ``ctrl.measurement_started`` / ``measurement_stopped`` to
    :meth:`on_measurement_started` / :meth:`on_measurement_stopped` after the timing tab
    became the ctrl's active tab, so the timing tab sees a measurement end first.
    """

    buttons_changed = Signal(bool, bool, bool, bool)
    status_changed = Signal(str, str)
    settings_locked = Signal(bool)
    tabs_locked = Signal(object)
    progress_cleared = Signal()
    message = Signal(str, int)

    def __init__(
        self,
        config: AppConfig,
        ctrl: Any,
        timing: "PlotTabBase | Any",
        save_service: Any,
        file_dialogs: Any,
        prompt: "Prompt",
        *,
        current_tab: Callable[[], "PlotTabBase"],
        duration_s: Callable[[], int],
        sample_metadata: Callable[[], dict],
        apply_settings: Callable[[], None],
        dialog_parent: Any = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._ctrl = ctrl
        self._timing = timing
        self._save_service = save_service
        self._file_dialogs = file_dialogs
        self._prompt = prompt
        self._current_tab = current_tab
        self._duration_s = duration_s
        self._sample_metadata = sample_metadata
        self._apply_settings = apply_settings
        self._dialog_parent = dialog_parent

        self._tab: Optional["PlotTabBase"] = (
            None  # tab of the running sweep / interval session
        )
        self._buttons = [True, False, False, False]  # start, stop, reset, save
        self._connected = True  # Start needs a connected device; see set_connected()
        self._device_info: dict = {}

    # ------------------------------------------------------------------
    # State

    @property
    def session_tab(self) -> Optional["PlotTabBase"]:
        """The tab of the active sweep / interval session, or None."""
        return self._tab

    def initial_state(self) -> None:
        """Publish the idle state (Start enabled once connected, status "ready")."""
        self._set_buttons(start=True, stop=False, reset=False, save=False)
        if self._connected:
            self._set_status("status_ready", "green")
        else:
            self._set_status("status_disconnected", "off")

    def set_connected(self, connected: bool) -> None:
        """Device link up or down: Start is offered only while connected."""
        if connected == self._connected:
            return
        self._connected = connected
        if not self._ctrl.is_measuring:
            self._set_status(
                "status_ready" if connected else "status_disconnected",
                "green" if connected else "off",
            )
        self._set_buttons()

    def set_device_info(self, info: dict) -> None:
        """Firmware version / OpenBIS code, written into the saved metadata."""
        self._device_info = dict(info)

    def has_unsaved(self) -> bool:
        """``True`` if measured data would be lost when the window closed."""
        tab = self._tab
        return self._save_service.has_unsaved() or (
            tab is not None and tab.has_unsaved_data()
        )

    def is_busy(self) -> bool:
        """``True`` while a measurement or a sweep / interval session is running."""
        return self._ctrl.is_measuring or self._tab is not None

    def confirm_close(self) -> bool:
        """``True`` if the window may close (no unsaved data, or the user discards it)."""
        if not self.has_unsaved():
            return True
        return self._prompt.ask(self._m("unsaved_data_end"), self._m("title_warning"))

    # ------------------------------------------------------------------
    # Frame routing

    def on_tab_changed(self, tab: "PlotTabBase | None") -> None:
        """Route the acquired frames: to the selected tab if it consumes them itself,
        else to the timing tab (not while an own-frames session is running)."""
        if tab is None:
            return
        if tab.receives_frames:
            self._ctrl.set_active_tab(tab)
        elif self._tab is None or not self._tab.receives_frames:
            self._ctrl.set_active_tab(self._timing)

    # ------------------------------------------------------------------
    # Button intents

    def start(self) -> None:
        tab = self._current_tab()
        kind = tab.session_kind
        if kind == "interval":
            self._start_interval(tab)
        elif kind == "sweep":
            self._start_sweep(tab)
        else:
            self._start_single()

    def stop(self) -> None:
        self._ctrl.stop_measurement()

    def save(self) -> None:
        tab = self._tab
        if tab is not None and tab.has_data():
            self._save_session(tab)
        else:
            self._save_single()

    def reset(self) -> None:
        if self._ctrl.is_measuring:
            self._warn("measurement_running_warning")
            return

        tab = self._tab
        if tab is not None:
            if tab.has_data() and not self._confirm_discard():
                return
            tab.reset_session()
            self._end_session()
        elif self._save_service.has_unsaved() and not self._confirm_discard():
            return

        if tab is None or not tab.receives_frames:
            self._timing.on_reset()
        self._save_service.mark_saved()
        self._set_buttons(start=True, save=False)
        self._set_status("status_ready", "green")

    # ------------------------------------------------------------------
    # Measurement lifecycle (AppController signals)

    def on_measurement_started(self) -> None:
        self._set_buttons(start=False, stop=True, reset=False, save=False)
        self.settings_locked.emit(True)
        self._set_status("status_measuring", "blue")
        tab = self._tab
        if tab is not None and not tab.receives_frames:
            tab.on_measurement_started()

    def on_measurement_stopped(self) -> None:
        self.settings_locked.emit(False)
        self._set_status("status_stopped", "yellow")
        self.progress_cleared.emit()
        tab = self._tab
        if tab is not None and not tab.receives_frames:
            # The timing tab has already seen the end, so its export is complete.
            tab.on_measurement_stopped()

        # Sweep sessions allow the next point right away; everything else waits for save / reset.
        start = tab is not None and tab.session_kind == "sweep"
        if tab is None:
            self._save_service.mark_unsaved()
        self._set_buttons(start=start, stop=False, reset=True, save=True)

    def on_reconnect_succeeded(self) -> None:
        self._set_buttons(start=True)
        self._set_status("status_connected", "green")

    def on_connection_lost(self) -> None:
        """All reconnect attempts failed."""
        self._set_status("status_disconnected", "red")
        self._prompt.error(
            self._m("connection_lost_terminal"), self._m("title_connection_error")
        )

    # ------------------------------------------------------------------
    # Start variants

    def _start_single(self) -> None:
        if self._save_service.has_unsaved():
            self._warn("save_or_discard_first")
            return
        self._set_metadata()
        self._ctrl.start_measurement(total_seconds=self._duration_s())

    def _start_sweep(self, tab: "PlotTabBase") -> None:
        total = self._duration_s()
        new_session = self._tab is None
        # Warn on an infinite measurement time only at the first point of a session.
        if total == 0 and new_session:
            if not self._prompt.ask(
                self._m("sweep_infinite_time"), self._m("title_sweep_infinite")
            ):
                return
        # The previous point is already captured in on_measurement_stopped; bypass the
        # unsaved-data guard for repeated measurements in the same session.
        self._save_service.mark_saved()
        if new_session:
            self._begin_session(tab)
        # Tabs that sweep the device voltage push the setpoint so the read-back is current.
        if getattr(tab, "applies_device_voltage_on_start", False):
            self._apply_settings()
        self._set_metadata()
        if not self._ctrl.start_measurement(total_seconds=total) and new_session:
            self._end_session()

    def _start_interval(self, tab: "PlotTabBase") -> None:
        total = int(tab.width_s * tab.repeat_count)  # type: ignore[attr-defined]
        self._begin_session(tab)
        if not self._ctrl.start_measurement(total_seconds=total):
            self._end_session()

    def _set_metadata(self) -> None:
        meta = self._sample_metadata()
        self._timing.set_measurement_metadata(
            rad_sample=meta.get("sample", ""),
            group=meta.get("group", ""),
            subterm=meta.get("suffix", ""),
        )

    def _begin_session(self, tab: "PlotTabBase") -> None:
        """Lock the other tabs and keep the timing tab from stealing the view."""
        self._tab = tab
        self.tabs_locked.emit(tab)
        self._timing.set_high_speed_autoswitch(False)

    def _end_session(self) -> None:
        self._tab = None
        self.tabs_locked.emit(None)
        self._timing.set_high_speed_autoswitch(True)

    # ------------------------------------------------------------------
    # Save variants

    def _save_session(self, tab: "PlotTabBase") -> None:
        """Summary file plus one automatically named file per detail export."""
        kind = tab.session_kind
        summary = tab.summary_export()
        if not summary:
            self._info("no_interval_data" if kind == "interval" else "no_summary_data")
            return

        meta = self._sample_metadata()
        extra: dict = {}
        if meta.get("detector"):
            extra["detector_code"] = meta["detector"]
        if kind == "sweep" and meta.get("distance_cm", 0.0) > 0.0:
            extra["sample_distance_cm"] = meta["distance_cm"]
        summary.metadata.update(extra)

        saved = self._save_dialog(summary, meta)
        if not saved or not saved.exists():
            return

        details = tab.session_exports()
        ok_count = 0
        for i, export in enumerate(details):
            export.metadata.update(extra)
            name = f"{saved.stem}_{tab.session_file_name(export, i)}.csv"
            try:
                write_export(export, saved.parent / name)
                ok_count += 1
            except Exception as exc:  # pylint: disable=broad-except
                _log.warning("Could not write session export %s: %s", name, exc)

        tab.mark_saved()
        tab.reset_session()
        self._end_session()
        if not tab.receives_frames:
            self._timing.on_reset()
        self._save_service.mark_saved()
        self._ctrl.finalize_journal()

        self._set_buttons(start=True, save=False)
        self.message.emit(
            self._m(f"summary_saved_{kind}", ok=ok_count, total=len(details)),
            STATUS_MESSAGE_MS,
        )
        self._set_status("status_ready", "green")

    def _save_single(self) -> None:
        if not self._save_service.has_unsaved():
            self._info("no_unsaved_data")
            return
        export = self._timing.export()
        if not export:
            self._error("no_export_data")
            return

        meta = self._sample_metadata()
        extra: dict = {"gui_version": gmcounter.__version__}
        openbis = self._device_info.get("openbis", "")
        if openbis and openbis != "unknown":
            extra["counter_openbis_code"] = openbis
        firmware = self._device_info.get("version", "")
        if firmware and firmware != "unknown":
            extra["counter_firmware_version"] = firmware
        if export.rows:
            extra["total_count"] = len(export.rows)
        if meta.get("detector"):
            extra["detector_code"] = meta["detector"]
        if meta.get("distance_cm", 0.0) > 0.0:
            extra["sample_distance_cm"] = meta["distance_cm"]
        export.metadata.update(extra)

        saved = self._save_dialog(export, meta)
        if saved and saved.exists():
            self._save_service.mark_saved()
            self._ctrl.finalize_journal()
            self._set_buttons(start=True, save=False)
            self.message.emit(self._m("saved"), SAVED_MESSAGE_MS)
        else:
            self._error("save_failed")

    def _save_dialog(self, export: Any, meta: dict) -> Any:
        return self._file_dialogs.manual_save_export(
            self._dialog_parent,
            export,
            meta.get("sample", ""),
            meta.get("group", ""),
            meta.get("suffix", ""),
        )

    # ------------------------------------------------------------------
    # Helpers

    def _m(self, key: str, **fmt: object) -> str:
        return self._config.message(key, **fmt)

    def _warn(self, key: str) -> None:
        self._prompt.warn(self._m(key), self._m("title_warning"))

    def _info(self, key: str) -> None:
        self._prompt.info(self._m(key), self._m("title_info"))

    def _error(self, key: str) -> None:
        self._prompt.error(self._m(key), self._m("title_error"))

    def _confirm_discard(self) -> bool:
        return self._prompt.ask(self._m("unsaved_data"), self._m("title_warning"))

    def _set_buttons(
        self,
        start: Optional[bool] = None,
        stop: Optional[bool] = None,
        reset: Optional[bool] = None,
        save: Optional[bool] = None,
    ) -> None:
        for i, value in enumerate((start, stop, reset, save)):
            if value is not None:
                self._buttons[i] = value
        start_now, stop_now, reset_now, save_now = self._buttons
        self.buttons_changed.emit(
            start_now and self._connected, stop_now, reset_now, save_now
        )

    def _set_status(self, key: str, colour: str) -> None:
        self.status_changed.emit(self._m(key), colour)
