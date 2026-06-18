"""Integration tests for MainWindow + DeviceManager — skipped after architecture refactor.

The legacy gmcounter.device_manager top-level path no longer exists; DeviceManager
is now at gmcounter.infrastructure.device_manager and is Qt-free (no signals).
MainWindow integration tests also require a full display context.

To write new integration tests use tests/hardware/test_device.py (gm_adapter fixture)
or tests/integration/ for in-process MockGMCounter tests.
"""

import pytest

pytest.importorskip("PySide6.QtWidgets", reason="Qt required for these (skipped) tests")

pytestmark = pytest.mark.skip(
    reason=(
        "Legacy integration tests for refactored code: "
        "gmcounter.device_manager no longer exists at that path "
        "(now gmcounter.infrastructure.device_manager) and "
        "MainWindow instantiation requires a real display context."
    )
)
