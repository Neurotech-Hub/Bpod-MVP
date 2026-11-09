import argparse
import struct
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


def read_firmware_identity(bpod: serial.Serial):
    """Handle both legacy (1-byte) and modern (4-byte) 'F' replies."""
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

    firmware = first[0]
    return "legacy", firmware, None, first


parser = argparse.ArgumentParser(
    description="Handshake with a Bpod r0.5 over Native USB (SerialUSB)."
)
parser.add_argument("port")
parser.add_argument(
    "--pulse",
    action="store_true",
    help="Pulse wire terminal 2 (D43) for 1s after identity check",
)
parser.add_argument(
    "--settle",
    type=float,
    default=0.5,
    help="Seconds to wait after opening the port (default: 0.5)",
)
args = parser.parse_args()

identity = describe_port(args.port)
print(f"Port: {args.port} ({identity})")
if "Prog. Port" in identity or "Programming" in identity:
    raise SystemExit(
        "This is the Arduino Due programming port (16U2 UART), not Native USB.\n"
        "Bpod firmware uses SerialUSB on the Native USB connector.\n"
        "Unplug and connect the cable to the Due/Bpod Native USB port, then re-run."
    )

with serial.Serial(args.port, 115200, timeout=2, write_timeout=2) as bpod:
    time.sleep(args.settle)

    # v18+ may emit discovery byte 222 on connect; drain it.
    pending = bpod.in_waiting
    if pending:
        junk = bpod.read(pending)
        print(f"Drained {len(junk)} byte(s) on open: {junk!r}")
    else:
        bpod.reset_input_buffer()

    bpod.write(b"6")
    ack = bpod.read(1)
    if ack == b"\xde":  # leftover discovery byte 222
        ack = bpod.read(1)
    if ack != b"5":
        raise RuntimeError(f"Handshake failed: {ack!r}")
    print("Handshake OK")

    kind, firmware, machine_type, raw = read_firmware_identity(bpod)
    if kind == "modern":
        print(
            f"Firmware: {firmware}, machine type: {machine_type} "
            f"(raw: {raw.hex()})"
        )
        if machine_type != 1:
            raise RuntimeError(
                "Expected Bpod r0.5 (machine type 1); refusing output test"
            )
        # v17+/v23 channel-index override: output index 5 = wire 1 on r0.5
        pulse_on = b"O\x05\x01"
        pulse_off = b"O\x05\x00"
    else:
        print(
            f"Legacy firmware build: {firmware} "
            f"(1-byte 'F' reply; raw: {raw.hex()})"
        )
        if firmware != 6:
            raise RuntimeError(
                f"Unexpected legacy build {firmware}; "
                "refusing output test without a known override map"
            )
        # Legacy r0.5: O + 'W' + 4-bit wire mask; bit0 = wire1 (D43 / terminal 2)
        pulse_on = b"OW\x01"
        pulse_off = b"OW\x00"

    if args.pulse:
        try:
            bpod.write(pulse_on)
            time.sleep(1)
        finally:
            bpod.write(pulse_off)
        print("Output pulse sent; verify terminal 2 vs GND with meter or scope")

    # 'Z' clears connectionState; solid green LED means still "connected".
    bpod.write(b"Z")
    bpod.flush()
    prev_timeout = bpod.timeout
    bpod.timeout = 0.5
    ack = bpod.read(8)
    bpod.timeout = prev_timeout
    if b"1" in ack:
        print("Disconnect OK")
    elif ack:
        print(f"Disconnect reply: {ack!r}")
