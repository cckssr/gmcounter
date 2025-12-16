#!/usr/bin/env python3
"""
Serial Data Reader for HRNG (Hardware Random Number Generator)
Connects to cu.usbmodem144201 and continuously reads 6-byte packets:
- Byte 0: 0xAA (start marker)
- Bytes 1-4: 32-bit unsigned integer (LSB format)
- Byte 5: 0x55 (end marker)

Outputs the decoded decimal values.
"""

import serial
import sys
import struct
from datetime import datetime
import threading
import plotly.graph_objects as go
from collections import deque


def find_serial_port(default_port="cu.usbmodem144201"):
    """Find and return the serial port device."""
    return f"/dev/{default_port}"


def read_packet(ser, timeout=1.0):
    """
    Read a single 6-byte packet from serial port.
    Returns (success: bool, value: int or None)

    Packet format:
    [0xAA][LSB_byte0][byte1][byte2][MSB_byte3][0x55]
    """
    try:
        # Wait for start byte (0xAA)
        while True:
            byte = ser.read(1)
            if not byte:
                return False, None
            if byte[0] == 0xAA:
                break

        # Read 4 data bytes
        data_bytes = ser.read(4)
        if len(data_bytes) < 4:
            return False, None

        # Read end byte (0x55)
        end_byte = ser.read(1)
        if not end_byte or end_byte[0] != 0x55:
            print(
                f"Warning: Invalid end byte received (0x{end_byte[0]:02X}), expected 0x55",
                file=sys.stderr,
            )
            return False, None

        # Unpack as 32-bit unsigned integer (little-endian)
        value = struct.unpack("<I", data_bytes)[0]
        return True, value

    except serial.SerialException as e:
        print(f"Serial error: {e}", file=sys.stderr)
        return False, None
    except Exception as e:
        print(f"Error reading packet: {e}", file=sys.stderr)
        return False, None


def main():
    """Main loop to continuously read and decode serial data with live histogram."""
    port = find_serial_port()

    try:
        print(f"Connecting to {port}...")
        ser = serial.Serial(port, baudrate=1000000, timeout=1)
        print(f"Connected to {port}")
        print("Waiting for packets (format: 0xAA + 4 bytes LSB + 0x55)...")
        print("Histogram will be opened in your browser...")
        print("-" * 60)

        packet_count = 0
        data_values = deque(maxlen=10000)  # Store last 10000 values for histogram
        import webbrowser
        import time
        import os

        # Create initial histogram file
        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=[0],
                nbinsx=50,
                name="Time Intervals (µs)",
                marker=dict(color="rgba(0, 100, 200, 0.7)"),
            )
        )
        fig.update_layout(
            title="Time Interval Distribution (Packets: 0)",
            xaxis_title="Time Interval (microseconds)",
            yaxis_title="Frequency",
            hovermode="x unified",
            showlegend=False,
            plot_bgcolor="rgba(240, 240, 240, 0.5)",
            height=600,
            width=1000,
        )
        html_path = os.path.abspath("histogram.html")
        fig.write_html(html_path)
        print(f"Opening histogram at: {html_path}")

        # Open histogram in browser
        time.sleep(0.5)
        webbrowser.open(f"file://{html_path}")

        def update_histogram():
            """Update histogram every 50 packets."""
            nonlocal packet_count
            last_update = 0

            while True:
                if packet_count > last_update + 50 and len(data_values) > 0:
                    # Update histogram
                    fig_new = go.Figure()
                    fig_new.add_trace(
                        go.Histogram(
                            x=list(data_values),
                            nbinsx=50,
                            name="Time Intervals (µs)",
                            marker=dict(color="rgba(0, 100, 200, 0.7)"),
                        )
                    )

                    fig_new.update_layout(
                        title=f"Time Interval Distribution (Packets: {packet_count})",
                        xaxis_title="Time Interval (microseconds)",
                        yaxis_title="Frequency",
                        hovermode="x unified",
                        showlegend=False,
                        plot_bgcolor="rgba(240, 240, 240, 0.5)",
                        height=600,
                        width=1000,
                    )

                    fig_new.write_html(html_path)
                    last_update = packet_count

                threading.Event().wait(0.5)  # Update every 500ms

        # Start histogram update thread
        histogram_thread = threading.Thread(target=update_histogram, daemon=True)
        histogram_thread.start()

        while True:
            success, value = read_packet(ser)

            if success:
                packet_count += 1
                data_values.append(value)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"[{timestamp}] Packet #{packet_count:6d}: {value:10d} (0x{value:08X})"
                )
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n" + "-" * 60)
        print(f"Stopped. Received {packet_count} packets.")
        if len(data_values) > 0:
            print(f"Min interval: {min(data_values)} µs")
            print(f"Max interval: {max(data_values)} µs")
            print(f"Avg interval: {sum(data_values) / len(data_values):.2f} µs")

    except serial.SerialException as e:
        print(f"Error: Could not connect to {port}")
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()
            print(f"Disconnected from {port}")


if __name__ == "__main__":
    main()
