import os
import pty
import tty
import select
import time
import sys
import random
import argparse
from typing import Optional, Dict, Union
from tempfile import gettempdir

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um src zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gmcounter.infrastructure.logging import Debug


class MockGMCounter:
    """
    Eine Mock-Klasse für GMCounter, die dessen Verhalten für Testzwecke simuliert,
    ohne ein physisches Gerät zu benötigen.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        max_tick: float = 1.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_tick = max_tick
        self._min_tick = 0.000_08  # Minimal tick (80 us)
        self._voltage = 500
        self._repeat = False
        self._counting = False
        self._counting_time_mode = 2
        self._count = 0
        self._last_count = 0
        self._measurement_start_time = 0.0
        self._last_pulse_time = 0.0
        self.next_pulse_time = 0
        self._next_pulse_interval = 0.0  # Das nächste zufällige Intervall
        self._stream_mode = 0  # Stream-Modus (0=aus, 1=bei Messung, etc.)
        self._start_marker_pending = False  # Flag: Start-Marker muss gesendet werden
        Debug.info(f"MockGMCounter für Port {port} initialisiert")
        print(
            f"Baudrate: {self.baudrate}, timeout: {self.timeout:2f}, max_tick: {self.max_tick:6f}"
        )

    def get_data(self) -> Optional[Dict[str, Union[int, bool]]]:
        counting_time_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        ct = counting_time_map.get(self._counting_time_mode, 0)

        progress = 0
        if self._counting and ct > 0:
            elapsed = time.time() - self._measurement_start_time
            progress = min(100, int((elapsed / ct) * 100))

        data = {
            "count": self._count,
            "last_count": self._last_count,
            "counting_time": ct,
            "repeat": self._repeat,
            "progress": progress,
            "voltage": self._voltage,
        }
        return data if data["voltage"] != 0 else None

    def read_time_fast(self) -> Optional[int]:
        if not self._counting:
            return None
        current_time = time.time()
        if self._last_pulse_time == 0.0:
            self._last_pulse_time = current_time
            return None
        delta_micros = (current_time - self._last_pulse_time) * 1_000_000
        self._last_pulse_time = current_time
        print(current_time)
        return int(delta_micros)

    def get_information(self) -> Dict[str, str]:
        return {
            "copyright": "(C) 2024 TU Berlin - Mock GM Counter",
            "version": "Mock v1.0.0 (HRNGGUI Test Device)",
            "openbis": "MOCK-001",
        }

    def get_openbis_code(self) -> str:
        return "MOCK-001"

    def set_voltage(self, value: int = 500):
        if 300 <= value <= 700:
            self._voltage = value
            Debug.info(f"MockGMCounter: Spannung auf {self._voltage}V gesetzt.")

    def set_repeat(self, value: bool = False):
        self._repeat = value
        Debug.info(f"MockGMCounter: Wiederholungsmodus auf {self._repeat} gesetzt.")

    def set_counting(self, value: bool = False):
        if value and not self._counting:  # Start counting
            self._counting = True
            self._last_count = self._count
            self._count = 0
            self._measurement_start_time = time.time()
            self._start_marker_pending = True  # Signal that start marker should be sent

            # Generiere das erste zufällige Intervall
            self._next_pulse_interval = random.uniform(self._min_tick, self.max_tick)
            self.next_pulse_time = time.time() + self._next_pulse_interval

            Debug.info(
                f"MockGMCounter: Zählung gestartet. Start-Marker wird gesendet. "
                f"Erstes Intervall: {self._next_pulse_interval:.6f}s"
            )
        elif not value and self._counting:  # Stop counting
            self._counting = False
            Debug.info(f"MockGMCounter: Zählung gestoppt. Finaler Count: {self._count}")

    def set_speaker(self, gm: bool = False, ready: bool = False):
        Debug.info(f"MockGMCounter: Lautsprecher auf gm={gm}, ready={ready} gesetzt.")

    def set_counting_time(self, value: int = 0):
        if 0 <= value <= 5:
            self._counting_time_mode = value
            Debug.info(f"MockGMCounter: Zählzeit-Modus auf {value} gesetzt.")

    def handle_command(self, command: str) -> Optional[str]:
        """Verarbeitet einen Befehl und gibt eine Antwortzeichenfolge zurück."""
        command = command.strip()

        # Stream-Befehle (b0-b8) sind immer erlaubt
        if command.startswith("b"):
            try:
                mode = int(command[1:])
                self._stream_mode = mode
                Debug.info(f"MockGMCounter: Stream-Modus auf {mode} gesetzt.")
                if mode == 0:
                    # Stream stoppen - keine Antwort
                    return None
                elif mode == 2:
                    # Daten jetzt senden
                    data_dict = self.get_data()
                    if data_dict:
                        return (
                            f"{data_dict['count']},"
                            f"{data_dict['last_count']},"
                            f"{data_dict['counting_time']},"
                            f"{int(data_dict['repeat'])},"
                            f"{data_dict['progress']},"
                            f"{data_dict['voltage']},"
                        )
            except ValueError:
                pass
            return None

        # Copyright und Version sind immer erlaubt
        if command == "c":
            return self.get_information()["copyright"]
        elif command == "v":
            return self.get_information()["version"]
        elif command == "info":
            # OpenBIS code request - format matching Arduino
            return f"OpenBIS code: {self.get_openbis_code()}"

        # Während der Zählung nur 's0' (Stopp) erlauben
        if self._counting and command != "s0":
            return None

        response = None
        if command.startswith("j"):
            try:
                self.set_voltage(int(command[1:]))
            except ValueError:
                pass
        elif command.startswith("o"):
            try:
                self.set_repeat(bool(int(command[1:])))
            except ValueError:
                pass
        elif command.startswith("s"):
            try:
                is_counting = bool(int(command[1:]))
                self.set_counting(is_counting)
            except ValueError:
                pass
        elif command.startswith("U"):
            try:
                val = int(command[1:])
                self.set_speaker(gm=bool(val & 1), ready=bool(val & 2))
            except ValueError:
                pass
        elif command.startswith("f"):
            try:
                self.set_counting_time(int(command[1:]))
            except ValueError:
                pass
        elif command == "r":
            # Register löschen
            self._count = 0
            self._last_count = 0
            Debug.info("MockGMCounter: Register gelöscht.")
        return response

    def tick(self) -> Optional[int]:
        """Wird periodisch aufgerufen, um spontane Daten zu erzeugen.

        Returns:
            Optional[int]: Zeitintervall in Mikrosekunden als int, oder None wenn keine Daten
        """
        if not self._counting:
            return None

        # Prüfen, ob die Zählzeit abgelaufen ist
        counting_time_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        time_limit = counting_time_map.get(self._counting_time_mode, 0)
        if time_limit > 0:
            elapsed_time = time.time() - self._measurement_start_time
            if elapsed_time >= time_limit:
                self.set_counting(False)
                return None  # Messung ist beendet, keine weiteren Pulse senden

        # Nächsten Impuls erzeugen
        if time.time() >= self.next_pulse_time:
            current_time = time.time()

            # Verwende das vorgenerierte Intervall für diesen Puls
            current_interval_us = int(self._next_pulse_interval * 1_000_000)

            self._count += 1  # Zähler bei einem Impuls erhöhen

            # Generiere das nächste zufällige Intervall
            self._next_pulse_interval = random.uniform(self._min_tick, self.max_tick)
            self.next_pulse_time = current_time + self._next_pulse_interval

            Debug.debug(
                f"Mock Pulse! Count: {self._count}, Time: {current_interval_us} us, Next in: {self._next_pulse_interval:.6f}s"
            )
            return current_interval_us  # Rückgabe als int, nicht als String
        return None


def main(device_class=MockGMCounter):
    """
    Erstellt eine virtuelle serielle Schnittstelle und simuliert ein Gerät.
    """
    port_file = os.path.join(gettempdir(), "virtual_serial_port.txt")

    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    print(f"Virtueller serieller Port erstellt: {slave_name}")

    # Schreibe den Port-Namen in eine Datei, damit andere Prozesse ihn lesen können
    try:
        with open(port_file, "w", encoding="utf-8") as f:
            f.write(slave_name)
        print(f"Port-Name wurde in '{port_file}' geschrieben.")
    except IOError as e:
        print(f"Fehler beim Schreiben der Port-Datei: {e}")

    print("Sie können sich mit Ihrer Anwendung mit diesem Port verbinden.")
    print("Drücken Sie Strg+C zum Beenden.")

    tty.setraw(master)

    mock_device = device_class(port=slave_name)

    try:
        while True:
            r, _, _ = select.select(
                [master], [], [], 0.01
            )  # Kürzeres Timeout für schnellere Reaktion

            if r:
                try:
                    raw_data = os.read(master, 1024)
                    if not raw_data:
                        print("Verbindung geschlossen.")
                        break

                    # Verarbeite jede Zeile separat (Befehle enden mit \n)
                    data = raw_data.decode(errors="ignore")
                    commands = [cmd.strip() for cmd in data.split("\n") if cmd.strip()]

                    for cmd in commands:
                        print(f"Empfangen: '{cmd}'")
                        response = mock_device.handle_command(cmd)

                        if response:
                            print(f"Sende Antwort: '{response}'")
                            os.write(master, (response + "\n").encode("utf-8"))

                except (OSError, ValueError) as e:
                    print(f"Fehler: {e}")
                    break

            # Check if start marker needs to be sent (measurement just started)
            if mock_device._start_marker_pending:
                start_marker = b"\xff\xff\xff\xff\xff\xff"
                print(f"Sende Start-Marker: 0x{start_marker.hex()}")
                os.write(master, start_marker)
                mock_device._start_marker_pending = False

            # Spontane Daten vom Gerät verarbeiten
            spontaneous_data = mock_device.tick()
            if spontaneous_data:
                # Korrektes Binärformat: 0xAA + 4 Bytes (little-endian) + 0x55
                packet = (
                    bytes([0xAA])  # Start-Byte
                    + spontaneous_data.to_bytes(
                        4, byteorder="little"
                    )  # 4 Daten-Bytes (little-endian)
                    + bytes([0x55])  # End-Byte
                )
                print(
                    f"Sende Binärpaket: 0x{packet.hex()} (Wert: {spontaneous_data} µs)"
                )
                os.write(master, packet)

    except KeyboardInterrupt:
        print("\nProgramm wird beendet...")
    finally:
        os.close(master)
        os.close(slave)
        print("Virtueller serieller Port geschlossen.")
        # Räume die Port-Datei auf
        if os.path.exists(port_file):
            try:
                os.remove(port_file)
                print(f"Port-Datei '{port_file}' wurde entfernt.")
            except OSError as e:
                print(f"Fehler beim Entfernen der Port-Datei: {e}")


if __name__ == "__main__":
    # Hier könnte man z.B. über Kommandozeilenargumente eine andere Geräteklasse auswählen.
    # z.B. main(device_class=MyOtherMockDevice)
    parser = argparse.ArgumentParser(description="Starte das Mock-Serial-Gerät.")
    parser.add_argument(
        "--baudrate", type=int, default=9600, help="Baudrate für das Mock-Gerät"
    )
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Timeout für das Mock-Gerät"
    )
    parser.add_argument(
        "--max-tick",
        type=float,
        default=1.0,
        help="Maximale Zeit zwischen Impulsen (Sekunden)",
    )
    args = parser.parse_args()

    # Konfigurierte MockGMCounter-Klasse erstellen
    class ConfiguredMockGMCounter(MockGMCounter):
        def __init__(self, port):
            super().__init__(
                port=port,
                baudrate=args.baudrate,
                timeout=args.timeout,
                max_tick=args.max_tick,
            )

    main(device_class=ConfiguredMockGMCounter)
