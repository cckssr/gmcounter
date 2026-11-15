"""The window stays usable on the small lab screens (1366x768, 1280x800) with both docks."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

SCREENS = [(1366, 768), (1280, 800)]
TAB_MAX_W = 900  # widest minimum of a central tab


def _side_scrolls(window):
    return [window.ui.scrollControls, window.ui.scrollLive]


def _assert_no_horizontal_scrolling(window) -> None:
    for scroll in _side_scrolls(window):
        assert (
            scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        assert not scroll.horizontalScrollBar().isVisible()
        # nothing is clipped: the viewport is at least as wide as the content needs
        assert scroll.widget().minimumSizeHint().width() <= scroll.viewport().width()


@pytest.mark.parametrize(("width", "height"), SCREENS)
def test_minimum_width_fits_the_screen_with_both_docks(qtbot, window, width, height):
    assert window.ui.dockControls.isVisible() and window.ui.dockLive.isVisible()
    assert window.minimumSizeHint().width() <= width
    window.resize(width, height)
    qtbot.wait(50)
    assert window.width() == width
    _assert_no_horizontal_scrolling(window)
    for dock in (window.ui.dockControls, window.ui.dockLive):
        assert dock.width() >= dock.minimumWidth()


@pytest.mark.parametrize(("width", "height"), SCREENS)
def test_every_tab_fits_the_screen(qtbot, window, width, height):
    window.resize(width, height)
    for index, (tab_id, tab) in enumerate(window.tabs.items()):
        window.ui.tabWidget.setCurrentIndex(index)
        qtbot.wait(20)
        assert tab.minimumSizeHint().width() <= TAB_MAX_W, tab_id
        assert window.minimumSizeHint().width() <= width, tab_id
    _assert_no_horizontal_scrolling(window)


def test_the_log_dock_opens_without_widening_the_window(qtbot, window):
    window.resize(1366, 768)
    window.ui.actionToggleLog.setChecked(True)
    qtbot.wait(50)
    assert window.ui.dockLog.isVisible()
    assert window.minimumSizeHint().width() <= 1366


def test_the_side_columns_have_a_sensible_minimum(window):
    for scroll in _side_scrolls(window):
        assert 200 <= scroll.minimumWidth() <= 420
        assert scroll.verticalScrollBarPolicy() != Qt.ScrollBarPolicy.ScrollBarAlwaysOff
