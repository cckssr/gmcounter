"""Tests for infrastructure/modules/registry.py — no Qt required."""

import pytest
from gmcounter.infrastructure.modules.registry import HostModule, ModuleRegistry


class GoodModule:
    """Minimal HostModule implementation."""

    def __init__(self, module_id: str) -> None:
        self._id = module_id
        self._connected = False

    @property
    def id(self) -> str:
        return self._id

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def describe(self) -> str:
        return f"Module {self._id}"


def setup_function():
    ModuleRegistry.clear()


def test_register_and_get():
    m = GoodModule("test_mod")
    ModuleRegistry.register(m)
    assert ModuleRegistry.get("test_mod") is m


def test_all_returns_copy():
    m = GoodModule("a")
    ModuleRegistry.register(m)
    d = ModuleRegistry.all()
    assert "a" in d
    # mutating the returned dict doesn't affect the registry
    d["extra"] = object()
    assert "extra" not in ModuleRegistry.all()


def test_unregister():
    m = GoodModule("b")
    ModuleRegistry.register(m)
    ModuleRegistry.unregister("b")
    assert ModuleRegistry.get("b") is None


def test_protocol_check():
    assert isinstance(GoodModule("x"), HostModule)


def test_bad_module_raises():
    class BadModule:
        pass

    with pytest.raises(TypeError):
        ModuleRegistry.register(BadModule())


def test_clear():
    ModuleRegistry.register(GoodModule("c"))
    ModuleRegistry.clear()
    assert ModuleRegistry.all() == {}
