"""Serial port listing helpers of the connection panel."""

from __future__ import annotations

from types import SimpleNamespace

from gmcounter.infrastructure.serial_ports import (
    SerialPortInfo,
    describe_port,
    preferred_port,
    with_port,
)

PORTS = [
    SerialPortInfo("/dev/cu.Bluetooth", "Bluetooth"),
    SerialPortInfo("/dev/cu.usbmodem1101", "Arduino UNO R4 Minima", usb=True),
    SerialPortInfo("/dev/cu.usbmodem2201", "Arduino UNO R4 Minima", usb=True),
]


def test_a_port_without_description_is_described_by_product_or_usb_ids():
    port = SimpleNamespace(
        device="COM3",
        description="n/a",
        product=None,
        manufacturer=None,
        vid=0x2341,
        pid=0x69,
    )
    assert describe_port(port) == SerialPortInfo(
        "COM3", "USB (VID:2341 PID:0069)", usb=True
    )
    port.product = "UNO R4"
    assert describe_port(port).description == "UNO R4"


def test_n_a_placeholders_leave_a_bluetooth_port_without_description():
    port = SimpleNamespace(
        device="/dev/cu.Bluetooth-Incoming-Port",
        description="n/a",
        hwid="n/a",
        vid=None,
        pid=None,
    )
    assert describe_port(port) == SerialPortInfo("/dev/cu.Bluetooth-Incoming-Port")


def test_the_last_used_port_is_preselected():
    assert preferred_port(PORTS, last_port="/dev/cu.usbmodem2201", hint="UNO") == 2


def test_without_a_last_port_the_hint_selects_the_first_match():
    assert preferred_port(PORTS, last_port="/dev/gone", hint="uno") == 1


def test_without_a_match_the_first_usb_port_is_selected():
    assert preferred_port(PORTS, hint="Nano") == 1


def test_without_usb_ports_the_first_port_is_selected_and_an_empty_list_selects_none():
    assert preferred_port(PORTS[:1], hint="Nano") == 0
    assert preferred_port([], last_port="x") == -1


def test_a_connected_port_missing_from_the_scan_is_added_in_front():
    ports = with_port(PORTS, "/dev/ttys004")
    assert ports[0].device == "/dev/ttys004" and len(ports) == 4
    assert with_port(PORTS, "/dev/cu.Bluetooth") == PORTS
