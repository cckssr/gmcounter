# Layer: infrastructure/modules — HostModule Protocol + ModuleRegistry.
"""Host-module Protocol and runtime registry (§8).

:class:`HostModule` is a structural Protocol for host-side peripherals
(USB motion stages, power supplies, etc.).  :class:`ModuleRegistry` is a
class-level registry that tabs query to decide whether their
``required_modules`` are available.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class HostModule(Protocol):
    """Protocol for host-side peripherals (USB stages, power meters, etc.).

    Tabs declare required_modules = {"kdc101"} to gate themselves behind a
    module. The main window calls tab.inject_modules(ModuleRegistry.all())
    whenever the registry changes.
    """

    @property
    def id(self) -> str: ...  # noqa: E704

    def connect(self) -> bool: ...  # noqa: E704

    def disconnect(self) -> None: ...  # noqa: E704

    def is_connected(self) -> bool: ...  # noqa: E704

    def describe(self) -> str: ...  # noqa: E704


class ModuleRegistry:
    """Runtime registry of connected host-side modules."""

    _registry: dict[str, object] = {}

    @classmethod
    def register(cls, module: object) -> None:
        """Register *module* under its ``id``.

        Raises:
            TypeError: If *module* does not satisfy :class:`HostModule`.
        """
        if not isinstance(module, HostModule):
            raise TypeError(f"{module!r} does not satisfy HostModule Protocol")
        cls._registry[module.id] = module  # type: ignore[attr-defined]

    @classmethod
    def unregister(cls, module_id: str) -> None:
        """Remove the module with *module_id* from the registry (no-op if absent)."""
        cls._registry.pop(module_id, None)

    @classmethod
    def get(cls, module_id: str) -> object:
        """Return the module registered under *module_id*, or None."""
        return cls._registry.get(module_id)

    @classmethod
    def all(cls) -> dict[str, object]:
        """Return a shallow copy of the full registry dict."""
        return dict(cls._registry)

    @classmethod
    def clear(cls) -> None:
        """Remove all registered modules (useful in tests)."""
        cls._registry.clear()
