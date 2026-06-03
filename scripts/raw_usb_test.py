#!/usr/bin/env python3
"""Serial Data Reader for HRNG (Hardware Random Number Generator).

Connects to cu.usbmodem101 and continuously reads 6-byte packets:
- Byte 0: 0xAA (start marker)
- Bytes 1-4: 32-bit unsigned integer (little-endian tick delta)
- Byte 5: 0x55 (end marker)

Reads in bulk chunks to keep up with high data rates (tested to 10 kHz).
Prints a rolling summary line every PRINT_INTERVAL seconds instead of
one line per packet — terminal I/O is the bottleneck at high rates, not USB.
"""

import serial
import sys
import argparse
from serial.tools import list_ports
from datetime import datetime
from collections import deque
from time import monotonic, sleep

TICKS_PER_US = 48  # RA4M1 Cortex-M4 @ 48 MHz — must match firmware TICKS_PER_US
READ_CHUNK = 4096  # bytes per read() call — amortises syscall overhead
PRINT_INTERVAL = 1.0  # seconds between summary lines


def find_serial_port(selection: str | None = None, default_port="cu.usbmodem2101"):
    """Resolve a serial port from a selection.

    If selection is None, list available ports and prompt the user to choose by
    number. If selection is a decimal number (string or numeric), treat it as
    an index into the displayed list. Otherwise treat selection as a port
    device name or basename and return /dev/<selection> when appropriate.
    """
    ports = list(list_ports.comports())
    if selection is None:
        if not ports:
            return f"/dev/{default_port}"
        print("Available serial ports:")
        for i, p in enumerate(ports):
            print(f"  [{i}] {p.device}  {p.description}")
        choice = input("Select port number: ").strip()
    else:
        choice = str(selection).strip()

    # numeric selection -> index
    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(ports):
            return ports[idx].device
        else:
            raise SystemExit(f"Invalid port index: {idx}")

    # if looks like a device path, return directly
    if choice.startswith("/dev/"):
        return choice

    # otherwise treat as basename under /dev
    return f"/dev/{choice}"


def parse_packets(buf: bytearray) -> list:
    """Parse all complete framed packets from buf in-place.

    Scans for 0xAA ... 0x55 frames.  Bytes that don't form a valid frame are
    skipped one at a time (re-sync).  The 0xFF×6 acquisition start marker is
    harmless: 0xFF != 0xAA so those bytes are just skipped.

    Returns a list of µs floats.  buf is modified in-place: consumed bytes are
    removed; any trailing partial packet is left for the next call.
    """
    values = []
    i = 0
    end = len(buf) - 5  # need at least 6 bytes from position i
    while i <= end:
        if buf[i] == 0xAA and buf[i + 5] == 0x55:
            ticks = buf[i + 1] | buf[i + 2] << 8 | buf[i + 3] << 16 | buf[i + 4] << 24
            values.append(ticks / TICKS_PER_US)
            i += 6
        else:
            i += 1
    del buf[:i]
    return values


def send_command(ser, cmd: str) -> None:
    ser.write((cmd + "\n").encode("utf-8"))
    ser.flush()


def read_diag_stat(ser, timeout: float = 2.0) -> dict:
    """Send DIAG:STAT? and parse the CSV response: dur_ms,npoints,debounced,overflows,tx_drops."""
    ser.timeout = timeout
    send_command(ser, "DIAG:STAT?")
    line = ser.readline().decode("utf-8", errors="replace").strip()
    parts = line.split(",")
    if len(parts) >= 4:
        try:
            return {
                "duration_ms": int(parts[0]),
                "n_points": int(parts[1]),
                "debounced": int(parts[2]),
                "overflows": int(parts[3]),
                "tx_drops": int(parts[4]) if len(parts) > 4 else 0,
            }
        except ValueError:
            pass
    return {"raw": line}


def main():
    p = argparse.ArgumentParser(description="Raw USB HRNG reader")
    p.add_argument("-p", "--port", help="port device or index from the list")
    args = p.parse_args()

    try:
        port = find_serial_port(args.port)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error selecting port: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"Connecting to {port}...")
        # 50 ms read timeout — read() returns whatever arrived, up to READ_CHUNK bytes.
        # Never blocks longer than 50 ms, so the print loop stays responsive.
        ser = serial.Serial(port, baudrate=1000000, timeout=0.05)
        print(f"Connected to {port}")

        send_command(ser, "ABOR")
        sleep(0.2)
        send_command(ser, "CONF:TIME 0")
        send_command(ser, "INIT")
        print("Sent INIT — streaming started.")
        print(f"Summary line every {PRINT_INTERVAL:.1f} s  |  Ctrl-C to stop")
        print("-" * 70)

        buf = bytearray()
        packet_count = 0
        data_values = deque(maxlen=100_000)
        interval_count = 0
        last_print = monotonic()

        while True:
            chunk = ser.read(READ_CHUNK)
            if chunk:
                buf.extend(chunk)
                new_values = parse_packets(buf)
                n = len(new_values)
                if n:
                    packet_count += n
                    interval_count += n
                    data_values.extend(new_values)

            now = monotonic()
            if now - last_print >= PRINT_INTERVAL:
                elapsed = now - last_print
                rate = interval_count / elapsed if elapsed > 0 else 0.0
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                if data_values:
                    last_val = data_values[-1]
                    dv = list(data_values)
                    mn, mx, avg = min(dv), max(dv), sum(dv) / len(dv)
                    print(
                        f"[{ts}]  total={packet_count:>9,d}  "
                        f"rate={rate:>7,.0f} Hz  "
                        f"last={last_val:>12,.2f} µs  "
                        f"min={mn:>10,.2f}  max={mx:>12,.2f}  avg={avg:>10,.2f} µs"
                    )
                else:
                    print(f"[{ts}]  waiting for data...")
                sys.stdout.flush()
                interval_count = 0
                last_print = now

    except KeyboardInterrupt:
        print("\n" + "-" * 70)
        print(f"Stopped.  Total packets received: {packet_count:,d}")
        if data_values:
            dv = list(data_values)
            print(f"  Min : {min(dv):,.2f} µs")
            print(f"  Max : {max(dv):,.2f} µs")
            print(f"  Avg : {sum(dv) / len(dv):,.2f} µs")

    except serial.SerialException as e:
        print(f"Error: could not connect to {port}")
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if "ser" in locals() and ser.is_open:
            send_command(ser, "ABOR\n")
            ser.read_all()  # flush any remaining data
            ser.flush()
            print("Sent ABOR — acquisition stopped.")
            sleep(1)
            send_command(ser, "DIAG:STAT?")

            stats = read_diag_stat(ser)
            print("\nDIAG:STAT? — last acquisition statistics:")
            if "raw" in stats:
                print(f"  (raw response) {stats['raw']}")
            else:
                dur_s = stats["duration_ms"] / 1000
                print(f"  Duration  : {stats['duration_ms']:,d} ms ({dur_s:.2f} s)")
                print(f"  Points    : {stats['n_points']:,d}")
                print(f"  Debounced : {stats['debounced']:,d}")
                print(f"  Overflows : {stats['overflows']:,d}")
                print(f"  TX drops  : {stats['tx_drops']:,d}")

            ser.close()
            print(f"Disconnected from {port}")


if __name__ == "__main__":
    main()
