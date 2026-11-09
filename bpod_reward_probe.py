#!/usr/bin/env python3
"""Test the Bpod reward routine: UART arm, then GPIO fire.

Strategy (see README):
  1. Send two bytes on SERIAL1/2: [device_id, reward_amt]
  2. Pulse spring terminal 2 (Due D43) to release reward

Legacy firmware build 6:
  UART TX  → b'OS' + byte (SERIAL1) or b'OT' + byte (SERIAL2)
  GPIO     → b'OW\\x01' high / b'OW\\x00' low  (terminal 2)
  Cleanup  → b'Z'  (clears solid green connected LED)

Examples:
  python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --device-id 1 --amount 5
  python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --device-id 1 --amount 5 --listen /dev/cu.usbserialXXXX
  python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --serial-only --device-id 2 --amount 10
  python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --gpio-only --pulse-ms 20
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


def require_legacy_build6(kind: str, firmware, machine_type, raw: bytes) -> None:
    if kind == "modern":
        print(
            f"Firmware: {firmware}, machine type: {machine_type} "
            f"(raw: {raw.hex()})"
        )
        raise RuntimeError(
            "Reward probe currently encodes legacy OS/OT + OW overrides; "
            "refusing modern firmware until that path is mapped"
        )
    print(f"Legacy firmware build: {firmware} (1-byte 'F' reply; raw: {raw.hex()})")
    if firmware != 6:
        raise RuntimeError(
            f"Unexpected legacy build {firmware}; reward override map not confirmed"
        )


def send_uart_arm(
    bpod: serial.Serial,
    channel: int,
    device_id: int,
    amount: int,
    gap_s: float,
) -> bytes:
    payload = bytes([device_id & 0xFF, amount & 0xFF])
    prefix = b"OS" if channel == 1 else b"OT"
    for i, byte in enumerate(payload):
        bpod.write(prefix + bytes([byte]))
        if gap_s > 0 and i + 1 < len(payload):
            time.sleep(gap_s)
    bpod.flush()
    return payload


def pulse_terminal2(bpod: serial.Serial, pulse_s: float) -> None:
    try:
        bpod.write(b"OW\x01")
        bpod.flush()
        time.sleep(pulse_s)
    finally:
        bpod.write(b"OW\x00")
        bpod.flush()


def end_session(bpod: serial.Serial) -> None:
    bpod.write(b"\x00Z")
    bpod.flush()
    prev_timeout = bpod.timeout
    bpod.timeout = 0.5
    ack = bpod.read(8)
    bpod.timeout = prev_timeout
    if b"1" in ack:
        print("Disconnect OK")
    else:
        print(
            f"Disconnect sent; unexpected ack {ack!r}. "
            "If the LED stays green, run: python3 bpod_serial_probe.py PORT --disconnect",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Arm reward over UART ([device_id, amount]), then fire GPIO terminal 2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("port", help="Bpod Native USB serial device")
    parser.add_argument(
        "--device-id",
        type=int,
        default=1,
        help="First UART byte (default: 1)",
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=1,
        help="Second UART byte, reward_amt (default: 1)",
    )
    parser.add_argument(
        "--channel",
        type=int,
        choices=(1, 2),
        default=1,
        help="Module UART: 1=SERIAL1, 2=SERIAL2 (default: 1)",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=0.002,
        help="Delay between legacy per-byte UART USB writes (default: 0.002 s)",
    )
    parser.add_argument(
        "--pre-trigger-delay",
        type=float,
        default=0.01,
        help="Seconds to wait after UART before GPIO pulse (default: 0.01)",
    )
    parser.add_argument(
        "--pulse-ms",
        type=float,
        default=50.0,
        help="GPIO terminal-2 high time in milliseconds (default: 50)",
    )
    parser.add_argument(
        "--serial-only",
        action="store_true",
        help="Send UART arm bytes only; skip GPIO pulse",
    )
    parser.add_argument(
        "--gpio-only",
        action="store_true",
        help="Pulse terminal 2 only; skip UART arm",
    )
    parser.add_argument(
        "--listen",
        metavar="PORT",
        help="Optional host UART to confirm [device_id, amount] reception",
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
        help="Seconds to wait for listened bytes (default: 1.0)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.5,
        help="Seconds to wait after opening Bpod USB (default: 0.5)",
    )
    args = parser.parse_args()

    if args.serial_only and args.gpio_only:
        raise SystemExit("Use only one of --serial-only / --gpio-only")
    for name, value in (("device-id", args.device_id), ("amount", args.amount)):
        if not 0 <= value <= 255:
            raise SystemExit(f"--{name} must be 0..255, got {value}")
    if args.pulse_ms < 0:
        raise SystemExit("--pulse-ms must be >= 0")

    reject_programming_port(args.port)
    pulse_s = args.pulse_ms / 1000.0
    do_uart = not args.gpio_only
    do_gpio = not args.serial_only

    listener = None
    if args.listen:
        if not do_uart:
            raise SystemExit("--listen requires UART arm (omit --gpio-only)")
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

    exit_code = 0
    try:
        with serial.Serial(args.port, 115200, timeout=2, write_timeout=2) as bpod:
            handshake(bpod, args.settle)
            kind, firmware, machine_type, raw = read_firmware_identity(bpod)
            require_legacy_build6(kind, firmware, machine_type, raw)

            payload = b""
            if do_uart:
                payload = send_uart_arm(
                    bpod,
                    args.channel,
                    args.device_id,
                    args.amount,
                    args.gap,
                )
                uart_name = "SERIAL1/OS" if args.channel == 1 else "SERIAL2/OT"
                print(
                    f"UART arm via {uart_name}: "
                    f"[device_id={args.device_id}, reward_amt={args.amount}] "
                    f"hex={payload.hex()}"
                )

                if listener is not None:
                    received = b""
                    deadline = time.time() + args.listen_timeout
                    while time.time() < deadline and len(received) < len(payload):
                        chunk = listener.read(len(payload) - len(received))
                        if chunk:
                            received += chunk
                        else:
                            time.sleep(0.01)
                    print(
                        f"Heard {len(received)} byte(s): "
                        f"{received!r} hex={received.hex()}"
                    )
                    if received != payload:
                        print("Listen mismatch or incomplete", file=sys.stderr)
                        exit_code = 1

            if do_gpio:
                if do_uart and args.pre_trigger_delay > 0:
                    time.sleep(args.pre_trigger_delay)
                pulse_terminal2(bpod, pulse_s)
                print(
                    f"GPIO fire: terminal 2 pulsed high for {args.pulse_ms:g} ms "
                    "(measure vs terminal 1 GND)"
                )
            else:
                print("GPIO fire skipped (--serial-only)")

            end_session(bpod)
    finally:
        if listener is not None:
            listener.close()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
