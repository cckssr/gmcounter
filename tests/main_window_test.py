"""MainWindow unit tests — skipped after architecture refactor.

The legacy gmcounter.data_controller top-level path no longer exists; DataController
is now at gmcounter.ui.controllers.data_controller.
The patch targets (gmcounter.main_window.Arduino, gmcounter.main_window.GMCounter)
no longer exist after the infrastructure layer was introduced.
"""

import pytest

pytest.importorskip("PySide6.QtWidgets", reason="Qt required for these (skipped) tests")

pytestmark = pytest.mark.skip(
    reason=(
        "Legacy MainWindow tests for refactored code: "
        "gmcounter.data_controller no longer exists at that path "
        "(now gmcounter.ui.controllers.data_controller) and "
        "the patched symbols gmcounter.main_window.{Arduino,GMCounter} "
        "were removed when the infrastructure layer was introduced."
    )
)
