# Bpod r0.5 — USB Control and UART Integration

Developer notes for controlling a **Sanworks Bpod state machine, hardware r0.5 (Arduino Due)** without requiring MATLAB for basic diagnostics. This document summarizes the hardware/firmware investigation and provides a minimal Python USB-serial test.

## Goal

1. Establish reliable USB communication between a computer and the Bpod r0.5.
2. Query the installed firmware and record its identity (modern builds report **machine type 1** for r0.5; legacy builds may only report a single-byte build number).
3. Optionally pulse a known 3.3 V digital output for bench verification.
4. Drive an external reward controller over a Bpod hardware UART (`SERIAL1` or `SERIAL2`), then release reward with a GPIO edge on spring **terminal 2**.
5. Keep changes to the Arduino Due firmware unnecessary unless the existing command interface proves insufficient.

## Lab findings (macOS, this unit)

Verified 2026-11-09 with `bpod_probe.py` against the physical r0.5 board:

| Check | Result |
|---|---|
| USB connector | Must use the Due **Native USB** port (`SerialUSB`). The **Programming** port (`Arduino Due Prog. Port`, VID:PID `2A03:003D`) opens as a serial device but never answers Bpod commands. |
| Working port example | Native USB appeared as `/dev/cu.usbmodem83201` with product **Arduino Due**, VID:PID `2341:003E`. |
| Handshake `b'6'` → `b'5'` | OK |
| Firmware `b'F'` | Returned **one byte** `0x06` (legacy build **6**), not the modern 4-byte `(firmware, machine_type)` packet. No machine-type field on this firmware. |
| Output pulse | Confirmed: **3.3 V** on spring **terminal 2** (Due D43) vs **terminal 1 (GND)** using legacy `OW` wire override. |
| Module UART TX | Confirmed on **SERIAL1** via legacy `OS` + data byte (not top-level `'S'`, which is soft-code). Always end with `'Z'` or the status LED stays solid green. |

Implications:

- This board is still on the old r0.5 main-module sketch (`FirmwareBuildVersion = 6`), not StateMachine Firmware v17+/v23. Modern MATLAB Gen2 / PyBpod assumptions may not apply until firmware is updated.
- Do **not** use the v17/v23 channel-index form `O\x05…` on this unit; that override map is for newer firmware. Legacy wire control is `O` + `'W'` + a 4-bit mask. Legacy UART TX is `O` + `'S'`/`'T'` + data byte.
- Baud rate on Native USB CDC is largely irrelevant; `115200` is fine. Module UART baud (also 115200 in firmware) is a separate physical interface.

Identify the port before probing:

```bash
python3 -m serial.tools.list_ports -v
```

Reject any listing whose product string contains **Prog. Port** / **Programming**.

## Architecture

- **Arduino Due:** runs persistent Bpod state-machine firmware. It handles event detection, timed state transitions, and local outputs. It is **not reprogrammed for each experiment**.
- **Computer (usually MATLAB):** defines and uploads state machines and retrieves results over the Due's **Native USB** serial port (`SerialUSB`). The byte protocol can also be implemented in Python. The Due's separate Programming USB port is for sketch upload via the 16U2 and is **not** the Bpod host interface.
- **Module serial ports:** the r0.5 has two single-ended 3.3 V UART ports; **they are not RS-485**. The firmware specifies **115200 baud** for these module ports. Do not confuse this setting with the USB serial protocol.
- **PyBpod:** do not assume plug-and-play compatibility with r0.5; PyBpod targets later firmware/hardware conventions. Basic direct USB commands are a smaller first step.

### Firmware locations

- [Sanworks Bpod product](https://sanworks.io/shop/viewproduct?productID=1001)
- [Legacy r0.5 main-module sketch (matches installed build 6)](https://github.com/sanworks/Bpod/blob/master/Firmware/Bpod_MainModule_0_5/Bpod_MainModule_0_5.ino)
- [Bpod StateMachine Firmware repository, v23](https://github.com/sanworks/Bpod_StateMachine_Firmware/tree/v23)
- [Dedicated r0.5 preconfigured firmware, v23](https://github.com/sanworks/Bpod_StateMachine_Firmware/tree/v23/Preconfigured/v23/StateMachine-Bpod0_5)
- [Shared development firmware (`StateMachineFirmware.ino`), v23](https://github.com/sanworks/Bpod_StateMachine_Firmware/blob/v23/Dev/StateMachineFirmware/StateMachineFirmware.ino)
- [Bpod Gen2 MATLAB software](https://github.com/sanworks/Bpod_Gen2)
- [PyBpod API](https://github.com/pybpod/pybpod-api)
- [Sanworks legacy finite-state-machine USB serial protocol, v17](https://sanworks.github.io/Bpod_Wiki/serial-interfaces/fsm-serial-interface-v17/) — useful for newer firmware; verify against the installed build (this unit is older than v17).

The v23 shared sketch has hardware-dependent configuration. For an r0.5 build:

```cpp
#define MACHINE_TYPE 1
#define MACHINE_BUILD 0
#define SM_FEATURE_PROFILE 0
```

The v23 source defines `MACHINE_TYPE == 1` as **FSM r0.5**, with these relevant mappings:

```cpp
byte OutputHW[] = {'U','U','X','B','B','W','W','W','W','P','P','P','P','P','P','P','P','V','V','V','V','V','V','V','V'};
byte OutputCh[] = {  0,  0,  0, 25, 24, 43, 41, 39, 37,  9,  8,  7,  6,  5,  4,  3,  2, 22, 22, 22, 22, 22, 22, 22, 22};
const int SerialBaudRate = 115200;
```

Accordingly, on **v23**, **USB override output index 5 corresponds to wire-terminal output 1 (Arduino Due D43; terminal 2)**. Output indices refer to `OutputHW` entries, **not** Arduino pin numbers.

On the **legacy build-6** sketch actually installed here, wire outputs are overridden as a group: command `'O'`, type `'W'`, then a bitmask (`bit0` = wire 1 / D43 / terminal 2, `bit1` = wire 2 / D41, …).

## Hardware connections (r0.5 schematic)

The original board schematic is `BpodMainBoard_r0_5.sch`. For the full Arduino Due pin ↔ Bpod net map (terminals, SERIAL1/2, PORT1–8, BNCs, valves), see **[Bpod_r0_5_PinMap.md](Bpod_r0_5_PinMap.md)**. That document is electrical/schematic truth; firmware still has to expose a given line before host software can drive it.

### Ten-position spring terminal block

| Terminal(s) | Purpose |
|---|---|
| 1, 10 | GND |
| 2–5 | Digital outputs (Due D43, D41, D39, D37) |
| 6–9 | Digital inputs through CD4050 buffers |

Outputs are nominally **3.3 V logic**. Check the connected circuit before applying loads or external voltages.

### `SERIAL1` and `SERIAL2` RJ45 pinout

| RJ45 contact | r0.5 schematic connection |
|---|---|
| 1 | +5 V power |
| 2 | GND |
| 3 | Bpod UART TX |
| 4 | Bpod UART RX (buffered through CD4050) |
| 5 | Additional MCU GPIO connection; not part of basic UART |
| 6–8 | Not connected in the supplied schematic |

For a SAMD21 / reward controller: **RJ45 3 → device RX; RJ45 2 ↔ device GND**. If bidirectional communication is needed, also **device TX → RJ45 4**. Keep the devices at compatible logic levels; **do not connect RJ45 +5 V to a 3.3 V rail**. A 1 m cable at 115200 baud is normally reasonable with common ground and suitable cable routing, but must be validated around solenoids/motors.

The behavioral `PORT1`–`PORT8` RJ45 connectors are **not** UART ports; they carry individual photogate/LED/valve and power lines.

## Reward delivery strategy

Chosen split: **parameterize over UART, fire over GPIO**.

| Step | Path | Payload / signal | Why |
|---|---|---|---|
| 1. Arm | Module UART (`SERIAL1` or `SERIAL2`), 115200 8N1 | Two bytes: `[device_id, reward_amt]` | Selects which dispenser and how much; ~174 µs on the wire for two bytes (plus host/firmware overhead). |
| 2. Fire | Spring **terminal 2** (Due D43) vs **terminal 1 (GND)** | Rising edge / pulse to 3.3 V logic | Immediate release trigger; avoids queuing the fire moment behind another UART frame. |

Sequence on this firmware (legacy build 6):

1. USB handshake (`6` → `5`), confirm identity (`F` → `0x06`).
2. Send `OS` + `device_id`, then `OS` + `reward_amt` (use `OT` if the controller is on SERIAL2).
3. Brief settle so the far end can parse the two bytes.
4. Pulse wire terminal 2: `OW\x01`, hold, then `OW\x00`.
5. Disconnect with `Z` (expect `1`) so the status LED leaves solid green.

Far-end contract (reward controller): interpret the two-byte UART frame as arming parameters; treat terminal-2 GPIO as the release strobe. Do not require a serial “trigger” byte for the fire moment.

Bench test script: `bpod_reward_probe.py`.

## USB command quick reference

The USB protocol is **binary byte-oriented**, not a newline-delimited ASCII terminal protocol. Commands shown below use ASCII command bytes followed by binary arguments.

| Bytes sent to Bpod | Function | Response / notes |
|---|---|---|
| `b'6'` | Handshake | `b'5'` (**verified**) |
| `b'F'` | Firmware identity | **Legacy (this unit):** 1 byte build number (`0x06`). **Modern v17+:** 4 bytes little-endian `uint16` firmware + `uint16` machine type |
| `b'OW\x01'` / `b'OW\x00'` | Legacy: set wire outputs high/low | No ACK. Bitmask of four wire terminals; `0x01` = terminal 2 / D43 (**verified**) |
| `b'OS' + byte` / `b'OT' + byte` | Legacy: TX one byte on SERIAL1 / SERIAL2 | No ACK. Top-level `'S'` is soft-code — do not use it for UART (**verified** `OS`) |
| `b'O\x05\x01'` / `b'O\x05\x00'` | Modern v17+/v23: wire output 1 high/low | No ACK. Channel index into `OutputHW[]`; **not** used by build 6 |
| `b'Z'` | End session | Legacy replies `b'1'` and clears the green “connected” LED (**verified**) |

**Safety:** Choose the override form that matches the `F` reply. **Verify identity first; disconnect valves and external loads before pulsing an output.**

## Minimal Python probe

Requires Python and [`pyserial`](https://pyserial.readthedocs.io/). The repo script `bpod_probe.py` refuses the Due programming port, accepts both legacy and modern `F` replies, and selects the matching wire-override bytes for `--pulse`.

```bash
python3 -m pip install pyserial
python3 -m serial.tools.list_ports -v
python3 bpod_probe.py /dev/cu.usbmodemXXXX
python3 bpod_probe.py /dev/cu.usbmodemXXXX --pulse
```

Use the Native USB device name (for example, `COM5` on Windows). On this unit, expected output without `--pulse`:

```text
Port: /dev/cu.usbmodemXXXX (Arduino Due, VID:PID=2341:003E, ...)
Handshake OK
Legacy firmware build: 6 (1-byte 'F' reply; raw: 06)
```

With `--pulse`, also expect a roughly 1-second **3.3 V pulse between spring terminals 2 and 1 (GND)**. The `O` command does **not** provide an acknowledgment; confirm with a meter or scope. Both handshake and pulse have been hardware-verified on this board.

### Reward routine test

`bpod_reward_probe.py` sends `[device_id, reward_amt]` on the module UART, then pulses terminal 2:

```bash
python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --device-id 1 --amount 5
python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --device-id 1 --amount 5 --channel 2
python3 bpod_reward_probe.py /dev/cu.usbmodemXXXX --device-id 1 --amount 5 --listen /dev/cu.usbserialXXXX
```

Defaults: SERIAL1, 10 ms post-UART settle, 50 ms GPIO pulse. Use `--serial-only` or `--gpio-only` to exercise each half of the path.

## Engineering concerns from the schematic discussion

These are **hypotheses to test**, not diagnosed causes of colleagues' intermittent triggers:

- Buffered behavioral and spring-terminal inputs may lack adequate biasing on the **external side** of the CD4050, depending on connected peripherals. Verify idle levels and external pull-ups rather than relying on the Due's internal pull-ups across the buffer.
- Long cables and solenoid switching may inject noise; scope both external inputs and the board's 3.3 V supply during an event.
- The r0.5 external module UARTs are single-ended, not differential RS-485. Provide a common ground and consider induced noise when wiring around inductive loads.
- Do not infer that a problem is caused by static electricity without correlating observed input glitches or supply disturbances.

## Implementation guidance for the agent

1. **Do not flash or replace the firmware initially.** Start with Native USB handshake and `F` query; record firmware bytes, OS, and port product/VID:PID. On this unit that is legacy build 6.
2. Keep the read-only probe as the default. Require an explicit option for any physical output override.
3. Handle binary framing, timeouts, serial-port ownership, and cleanup explicitly. MATLAB or another app cannot hold the USB serial port at the same time. Reject the Due **programming** port.
4. Branch override encoding on the `F` reply shape (1-byte legacy vs 4-byte modern). Avoid hardcoded v23 channel indices on legacy firmware.
5. Reward path on this unit: UART arm with `[device_id, reward_amt]` via legacy `OS`/`OT`, GPIO fire on terminal 2 via `OW`. Always `'Z'` on exit. Confirm far-end framing before connecting a live dispenser.
6. Validate wire-terminal I/O, serial direction, voltage levels, and pin numbering with a meter/scope before connecting experimental hardware.

