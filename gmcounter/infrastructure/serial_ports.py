# Layer: infrastructure — serial port enumeration (pyserial).

"""Serial ports the connection panel offers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from serial.tools import list_ports


@dataclass(frozen=True)
class SerialPortInfo:
    """One selectable serial port.

    Holds the device path, a human-readable description and whether it is a USB serial
    adapter (the GM counter's Arduino always is).
    """

    device: str
    description: str = ""
    usb: bool = False


def _known(value: object) -> str:
    """``value`` as text, empty for ``None`` and pyserial's ``"n/a"`` placeholder."""
    text = str(value or "").strip()
    return "" if text.lower() == "n/a" else text


def describe_port(port: object) -> SerialPortInfo:
    """Build a :class:`SerialPortInfo` from a pyserial ``ListPortInfo``.

    pyserial leaves the description at ``"n/a"`` on some platforms (often on Windows); the
    product, the manufacturer, the USB ids or the hardware id are used instead.
    """
    device = _known(getattr(port, "device", ""))
    vid = getattr(port, "vid", None)
    pid = getattr(port, "pid", None)
    description = _known(getattr(port, "description", ""))
    if not description:
        product = _known(getattr(port, "product", None))
        manufacturer = _known(getattr(port, "manufacturer", None))
        if product:
            description = product
        elif manufacturer:
            description = manufacturer
        elif vid is not None and pid is not None:
            description = f"USB (VID:{vid:04X} PID:{pid:04X})"
        else:
            description = _known(getattr(port, "hwid", None))
    return SerialPortInfo(device=device, description=description, usb=vid is not None)


def list_serial_ports() -> list[SerialPortInfo]:
    """All serial ports of the system, sorted by device path."""
    ports = [describe_port(port) for port in list_ports.comports()]
    return sorted((p for p in ports if p.device), key=lambda p: p.device)


def preferred_port(
    ports: Sequence[SerialPortInfo],
    last_port: str | None = None,
    hint: str | None = None,
) -> int:
    """Index of the port to preselect, or -1 for an empty list.

    The last used port wins; otherwise the first port whose path or description contains
    ``hint`` (e.g. ``"UNO"``); otherwise the first USB port (not a Bluetooth or modem port);
    otherwise the first port.
    """
    if not ports:
        return -1
    if last_port:
        for index, port in enumerate(ports):
            if port.device == last_port:
                return index
    if hint:
        needle = hint.lower()
        for index, port in enumerate(ports):
            if needle in port.device.lower() or needle in port.description.lower():
                return index
    for index, port in enumerate(ports):
        if port.usb:
            return index
    return 0


def with_port(
    ports: Iterable[SerialPortInfo], device: str, description: str = ""
) -> list[SerialPortInfo]:
    """``ports`` plus ``device`` at the front if it is not among them (a connected port)."""
    result = list(ports)
    if device and all(port.device != device for port in result):
        result.insert(0, SerialPortInfo(device=device, description=description))
    return result
