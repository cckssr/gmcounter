"""Tests for PlotTabBase / TabRegistry / GMTimingTab / ModuleRegistry seam — no Qt required for the pure-Python pieces.

The registry and module checks run without PySide6; the GMTimingTab import
is guarded so the whole file can be collected in environments without Qt
(those tests will be skipped).
"""

import pytest

from gmcounter.ui.tabs.registry import TabRegistry
from gmcounter.infrastructure.modules.registry import ModuleRegistry

# ------------------------------------------------------------------
# Registry basics (no Qt needed)


def setup_function():
    TabRegistry.clear()
    ModuleRegistry.clear()


class _FakeTab:
    tab_id = "fake"
    tab_title = "Fake"
    required_modules: set = set()
    required_sources: set = set()


class _GatedTab:
    tab_id = "gated"
    tab_title = "Gated"
    required_modules = {"mock_mod"}
    required_sources: set = set()


def test_register():
    TabRegistry.register(_FakeTab)
    assert _FakeTab in TabRegistry.all_registered()


def test_available_no_modules():
    TabRegistry.register(_FakeTab)
    TabRegistry.register(_GatedTab)
    available = TabRegistry.available({})
    assert _FakeTab in available
    assert _GatedTab not in available


def test_available_with_module():
    TabRegistry.register(_GatedTab)

    class _MockMod:
        @property
        def id(self):
            return "mock_mod"

        def connect(self):
            return True

        def disconnect(self):
            pass

        def is_connected(self):
            return True

        def describe(self):
            return "mock"

    m = _MockMod()
    ModuleRegistry.register(m)
    available = TabRegistry.available(ModuleRegistry.all())
    assert _GatedTab in available


def test_duplicate_register():
    TabRegistry.register(_FakeTab)
    TabRegistry.register(_FakeTab)
    assert TabRegistry.all_registered().count(_FakeTab) == 1


def test_clear():
    TabRegistry.register(_FakeTab)
    TabRegistry.clear()
    assert TabRegistry.all_registered() == []


# ------------------------------------------------------------------
# GMTimingTab tab_id and registration (import guards Qt)


def test_gm_timing_tab_registered():
    pytest.importorskip("PySide6", reason="PySide6 not installed")
    from gmcounter.ui.tabs.gm_timing_tab import GMTimingTab

    TabRegistry.register(GMTimingTab)
    available = TabRegistry.available({})
    ids = [t.tab_id for t in available]
    assert "gm_timing" in ids


def test_gm_timing_tab_always_available():
    pytest.importorskip("PySide6", reason="PySide6 not installed")
    from gmcounter.ui.tabs.gm_timing_tab import GMTimingTab

    TabRegistry.register(GMTimingTab)
    # available with empty modules dict — GM tab needs no modules
    available = TabRegistry.available({})
    assert any(t.tab_id == "gm_timing" for t in available)
