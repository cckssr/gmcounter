"""Message-box prompts behind the small ask / warn / info / error interface."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QWidget

from . import dialogs


class Prompt(Protocol):
    """What the session controller needs to talk to the user (texts arrive translated)."""

    def ask(self, text: str, title: str) -> bool:
        """Yes / no question; ``True`` for yes."""
        ...

    def warn(self, text: str, title: str) -> None: ...  # noqa: E704

    def info(self, text: str, title: str) -> None: ...  # noqa: E704

    def error(self, text: str, title: str) -> None: ...  # noqa: E704


class MessageBoxPrompt:
    """Prompt backed by modal ``QMessageBox`` dialogs on ``parent``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self.parent = parent

    def ask(self, text: str, title: str) -> bool:
        return dialogs.ask_question(self.parent, text, title)

    def warn(self, text: str, title: str) -> None:
        dialogs.show_warning(self.parent, text, title)

    def info(self, text: str, title: str) -> None:
        dialogs.show_info(self.parent, text, title)

    def error(self, text: str, title: str) -> None:
        dialogs.show_error(self.parent, text, title)
