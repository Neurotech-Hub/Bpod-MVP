#!/usr/bin/env python3
"""Send a known payload out Bpod SERIAL1 or SERIAL2 (module RJ45 UART).

Legacy firmware build 6 (this unit): module UART TX is under the output-override
menu — `b'OS' + byte` → Serial1, `b'OT' + byte` → Serial2 (same pattern as
`b'OW' + mask` for wire terminals). Top-level `'S'` is soft-code (2 args), not
UART; using it leaves the session connected and the status LED green.

Module UART is 115200 8N1, 3.3 V, single-ended.

Wiring (listen with a USB–UART adapter or SAMD21):
  RJ45 pin 2 → GND
  RJ45 pin 3 → adapter RX / SAMD21 RX
  Do not connect RJ45 pin 1 (+5 V) to a 3.3 V rail.

Examples:
  python3 bpod_serial_probe.py /dev/cu.usbmodemXXXX
  python3 bpod_serial_probe.py /dev/cu.usbmodemXXXX --channel 2 --message 'HELLO'
  python3 bpod_serial_probe.py /dev/cu.usbmodemXXXX --listen /dev/cu.usbserialXXXX
  python3 bpod_serial_probe.py /dev/cu.usbmodemXXXX --disconnect
"""

from __future__ import annotations

import argparse
import struct
import sys
import time

import serial
from serial.tools import list_ports


def describe_port(path: str) -> str:
    for info in list_ports.comports():
        if info.device == path:
            bits = [info.product or info.description or "unknown device"]
            if info.vid is not None and info.pid is not None:
                bits.append(f"VID:PID={info.vid:04X}:{info.pid:04X}")
            if info.manufacturer:
                bits.append(info.manufacturer)
            return ", ".join(bits)
    return "unknown device"


def reject_programming_port(path: str) -> None:
    identity = describe_port(path)
    print(f"Bpod USB: {path} ({identity})")
    if "Prog. Port" in identity or "Programming" in identity:
        raise SystemExit(
            "This is the Arduino Due programming port, not Native USB.\n"
            "Connect to the Native USB port and re-run."
        )


def handshake(bpod: serial.Serial, settle: float) -> None:
    time.sleep(settle)
    pending = bpod.in_waiting
    if pending:
        junk = bpod.read(pending)
        print(f"Drained {len(junk)} byte(s) on open: {junk!r}")
    else:
        bpod.reset_input_buffer()

    bpod.write(b"6")
    ack = bpod.read(1)
    if ack == b"\xde":
        ack = bpod.read(1)
    if ack != b"5":
        raise RuntimeError(f"Handshake failed: {ack!r}")
    print("Handshake OK")


def read_firmware_identity(bpod: serial.Serial):
    bpod.write(b"F")
    first = bpod.read(1)
    if not first:
        raise RuntimeError("No firmware response")

    prev_timeout = bpod.timeout
    bpod.timeout = 0.2
    rest = bpod.read(3)
    bpod.timeout = prev_timeout

    if len(rest) == 3:
        firmware, machine_type = struct.unpack("<HH", first + rest)
        return "modern", firmware, machine_type, first + rest

    return "legacy", first[0], None, first


def parse_payload(message: str, hex_payload: str | None) -> bytes:
    if hex_payload is not None:
        cleaned = "".join(hex_payload.split())
        try:
            return bytes.fromhex(cleaned)
        except ValueError as exc:
            raise SystemExit(f"Invalid --hex value: {exc}") from exc
    return message.encode("ascii")


def send_legacy_uart(bpod: serial.Serial, channel: int, payload: bytes, gap_s: float) -> None:
    # Legacy r0.5 build 6: O + 'S'/'T' + data byte (under manualOverrideOutputs).
    # Do not use top-level 'S'/'T' — those are soft-code / other commands.
    prefix = b"OS" if channel == 1 else b"OT"
    for i, byte in enumerate(payload):
        bpod.write(prefix + bytes([byte]))
        if gap_s > 0 and i + 1 < len(payload):
            time.sleep(gap_s)


def send_modern_uart(bpod: serial.Serial, channel: int, payload: bytes) -> None:
    # v17+: 'T' + module_index + nBytes + payload (max typically small).
    if len(payload) > 255:
        raise RuntimeError("Modern 'T' payload limited to 255 bytes")
    module_index = channel - 1  # SERIAL1 → 0, SERIAL2 → 1
    bpod.write(b"T" + bytes([module_index, len(payload)]) + payload)


def end_session(bpod: serial.Serial) -> None:
    """Send 'Z' so firmware clears connectionState and turns the green LED off."""
    # If a prior bad command left the parser waiting for an arg byte, pad once.
    bpod.write(b"\x00Z")
    bpod.flush()
    prev_timeout = bpod.timeout
    bpod.timeout = 0.5
    ack = bpod.read(8)
    bpod.timeout = prev_timeout
    if b"1" in ack:
        print("Disconnect OK (firmware ack '1'; status LED should leave solid green)")
    else:
        print(
            f"Disconnect sent; unexpected ack {ack!r}. "
            "If the LED stays green, power-cycle or re-run with --disconnect.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "TX test for Bpod module UART (SERIAL1/SERIAL2) via USB override."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("port", help="Bpod Native USB serial device")
    parser.add_argument(
        "--channel",
        type=int,
        choices=(1, 2),
        default=1,
        help="Module UART: 1=SERIAL1 (legacy 'S'), 2=SERIAL2 (legacy 'T')",
    )
    parser.add_argument(
        "--message",
        default="BPOD",
        help="ASCII payload to send (default: BPOD)",
    )
    parser.add_argument(
        "--hex",
        dest="hex_payload",
        default=None,
        help="Hex payload instead of --message (e.g. '01 02 FF')",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=0.002,
        help="Delay between legacy per-byte USB writes (default: 0.002 s)",
    )
    parser.add_argument(
        "--listen",
        metavar="PORT",
        help="Optional host UART (USB–UART on RJ45 TX) to confirm reception",
    )
    parser.add_argument(
        "--listen-baud",
        type=int,
        default=115200,
        help="Baud for --listen port (default: 115200)",
    )
    parser.add_argument(
        "--listen-timeout",
        type=float,
        default=1.0,
        help="Seconds to wait for listened bytes after TX (default: 1.0)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.5,
        help="Seconds to wait after opening Bpod USB (default: 0.5)",
    )
    parser.add_argument(
        "--disconnect",
        action="store_true",
        help="Only send disconnect ('Z') to clear a stuck green connected LED",
    )
    args = parser.parse_args()

    reject_programming_port(args.port)

    if args.disconnect:
        with serial.Serial(args.port, 115200, timeout=2, write_timeout=2) as bpod:
            time.sleep(args.settle)
            bpod.reset_input_buffer()
            end_session(bpod)
        return 0

    payload = parse_payload(args.message, args.hex_payload)
    if not payload:
        raise SystemExit("Payload is empty")

    listener = None
    if args.listen:
        print(
            f"Listen:  {args.listen} @ {args.listen_baud} "
            f"({describe_port(args.listen)})"
        )
        listener = serial.Serial(
            args.listen,
            args.listen_baud,
            timeout=0.1,
            write_timeout=2,
        )
        time.sleep(0.1)
        listener.reset_input_buffer()

    try:
        with serial.Serial(args.port, 115200, timeout=2, write_timeout=2) as bpod:
            handshake(bpod, args.settle)
            kind, firmware, machine_type, raw = read_firmware_identity(bpod)

            if kind == "modern":
                print(
                    f"Firmware: {firmware}, machine type: {machine_type} "
                    f"(raw: {raw.hex()})"
                )
                send_modern_uart(bpod, args.channel, payload)
                path = f"modern T module_index={args.channel - 1}"
            else:
                print(
                    f"Legacy firmware build: {firmware} "
                    f"(1-byte 'F' reply; raw: {raw.hex()})"
                )
                if firmware != 6:
                    raise RuntimeError(
                        f"Unexpected legacy build {firmware}; "
                        "SERIAL override map not confirmed"
                    )
                send_legacy_uart(bpod, args.channel, payload, args.gap)
                override = "OS" if args.channel == 1 else "OT"
                path = f"legacy '{override}' (SERIAL{args.channel})"

            print(
                f"Sent {len(payload)} byte(s) via {path}: "
                f"{payload!r} hex={payload.hex()}"
            )
            print(
                "No USB ACK for UART TX — confirm on RJ45 pin 3 (TX) vs pin 2 (GND), "
                "or with --listen."
            )

            received = b""
            if listener is not None:
                deadline = time.time() + args.listen_timeout
                while time.time() < deadline and len(received) < len(payload):
                    chunk = listener.read(len(payload) - len(received))
                    if chunk:
                        received += chunk
                    else:
                        time.sleep(0.01)
                print(f"Heard {len(received)} byte(s): {received!r} hex={received.hex()}")
                if received == payload:
                    print("Listen match OK")
                else:
                    print("Listen mismatch or incomplete", file=sys.stderr)
                    end_session(bpod)
                    return 1

            end_session(bpod)
    finally:
        if listener is not None:
            listener.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
