# Bpod r0.5 — Arduino Due pin map

**Source of truth:** `BpodMainBoard_r0_5.sch` (uploaded EAGLE schematic). This maps physical electrical connections, **not** a promise that any particular firmware or MATLAB protocol exposes a channel for arbitrary control. Arduino Due pin labels were cross-referenced against [Arduino Due documentation](https://docs.arduino.cc/hardware/due).

## Complete Due digital and analog map

**NC** means that the Due pin does not connect to another net **on the Bpod r0.5 mainboard schematic**; it does *not* mean the Due pin is unavailable on the Arduino board itself. Input paths through CD4050 are non-isolated; the two BNC input channels pass through an optocoupler. All direct Due GPIO and analog inputs are **3.3 V only**.

| Due pin | Bpod function | Bpod location | Electrical path |
|---|---|---|---|
| D0 | Not connected on r0.5 mainboard | — | — |
| D1 | Not connected on r0.5 mainboard | — | — |
| D2 | Port 8 LED / PWM output | PORT8 RJ45 pin 3 | Direct 3.3 V Due output |
| D3 | Port 7 LED / PWM output | PORT7 RJ45 pin 3 | Direct 3.3 V Due output |
| D4 | Port 6 LED / PWM output | PORT6 RJ45 pin 3 | Direct 3.3 V Due output |
| D5 | Port 5 LED / PWM output | PORT5 RJ45 pin 3 | Direct 3.3 V Due output |
| D6 | Port 4 LED / PWM output | PORT4 RJ45 pin 3 | Direct 3.3 V Due output |
| D7 | Port 3 LED / PWM output | PORT3 RJ45 pin 3 | Direct 3.3 V Due output |
| D8 | Port 2 LED / PWM output | PORT2 RJ45 pin 3 | Direct 3.3 V Due output |
| D9 | Port 1 LED / PWM output | PORT1 RJ45 pin 3 | Direct 3.3 V Due output |
| D10 | BNC digital input net BNCIN1 | BNC input jack U$4 | Optocoupler OPTOCOUPLE channel 1 -> Due input |
| D11 | BNC digital input net BNCIN2 | BNC input jack U$3 | Optocoupler OPTOCOUPLE channel 2 -> Due input |
| D12 | On-board status LED line LED1 | Tricolor LED U$8 (pin 3) | Direct LED signal |
| D13 | On-board status LED line LED2 | Tricolor LED U$8 (pin 4) | Direct LED signal |
| D14 | On-board status LED line LED3 | Tricolor LED U$8 (pin 1) | Direct LED signal |
| D15 | SERIAL2 auxiliary line (not TX/RX) | SERIAL2 RJ45 pin 5 | Direct GPIO; protocol/function not defined by schematic |
| D16 | Serial2 TX (Due Serial2 TXD1) | SERIAL2 RJ45 pin 3 | Direct 3.3 V UART TX |
| D17 | Serial2 RX (Due Serial2 RXD1) | SERIAL2 RJ45 pin 4 | CD4050 buffer 5V_3V3_1 input pin 5 -> output pin 4 -> Due |
| D18 | Serial1 TX (Due Serial1 TXD0) | SERIAL1 RJ45 pin 3 | Direct 3.3 V UART TX |
| D19 | Serial1 RX (Due Serial1 RXD0) | SERIAL1 RJ45 pin 4 | CD4050 buffer 5V_3V3_1 input pin 3 -> output pin 2 -> Due |
| D20 | SERIAL1 auxiliary line (Due SDA; not UART TX/RX) | SERIAL1 RJ45 pin 5 | Direct GPIO; protocol/function not defined by schematic |
| D21 | Not connected on r0.5 mainboard | — | — |
| D22 | Valve shift-register latch / control | VALVE_REGISTER pin 7 (on mainboard) | Internal register control; valves on PORT1–8 RJ45 pin 7 |
| D23 | Sync shift-register latch / control | SYNC_REGISTER pin 12 (on mainboard) | Internal register control; sync outputs on SYNC RJ45 pins 2–8 |
| D24 | BNC output driver, jack U$1 | BNC output jack U$1 (schematic identifier) | Q3 transistor driver + R4 pull-up to 5V; not direct 3.3 V push-pull |
| D25 | BNC output driver, jack U$2 | BNC output jack U$2 (schematic identifier) | Q4 transistor driver + R5 pull-up to 5V; not direct 3.3 V push-pull |
| D26 | Not connected on r0.5 mainboard | — | — |
| D27 | Not connected on r0.5 mainboard | — | — |
| D28 | Port 1 digital input | PORT1 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D29 | Wire input 1 (DSUB_BUS1) | U$6 10-pin terminal, terminal 9 | Via CD4050 non-inverting buffer to Due input |
| D30 | Port 2 digital input | PORT2 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D31 | Wire input 2 (DSUB_BUS2) | U$6 10-pin terminal, terminal 8 | Via CD4050 non-inverting buffer to Due input |
| D32 | Port 3 digital input | PORT3 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D33 | Wire input 3 (DSUB_BUS3) | U$6 10-pin terminal, terminal 7 | Via CD4050 non-inverting buffer to Due input |
| D34 | Port 4 digital input | PORT4 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D35 | Wire input 4 (DSUB_BUS4) | U$6 10-pin terminal, terminal 6 | Via CD4050 non-inverting buffer to Due input |
| D36 | Port 5 digital input | PORT5 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D37 | Wire output 1 (DSUB_BUS5) | U$6 10-pin terminal, terminal 5 | Direct Due 3.3 V GPIO output |
| D38 | Port 6 digital input | PORT6 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D39 | Wire output 2 (DSUB_BUS6) | U$6 10-pin terminal, terminal 4 | Direct Due 3.3 V GPIO output |
| D40 | Port 7 digital input | PORT7 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D41 | Wire output 3 (DSUB_BUS7) | U$6 10-pin terminal, terminal 3 | Direct Due 3.3 V GPIO output |
| D42 | Port 8 digital input | PORT8 RJ45 pin 1 | Via CD4050 non-inverting buffer to Due input |
| D43 | Wire output 4 (DSUB_BUS8) | U$6 10-pin terminal, terminal 2 | Direct Due 3.3 V GPIO output |
| D44 | Not connected on r0.5 mainboard | — | — |
| D45 | Not connected on r0.5 mainboard | — | — |
| D46 | Not connected on r0.5 mainboard | — | — |
| D47 | Not connected on r0.5 mainboard | — | — |
| D48 | Not connected on r0.5 mainboard | — | — |
| D49 | Not connected on r0.5 mainboard | — | — |
| D50 | Not connected on r0.5 mainboard | — | — |
| D51 | Not connected on r0.5 mainboard | — | — |
| D52 | Not connected on r0.5 mainboard | — | — |
| D53 | Not connected on r0.5 mainboard | — | — |
| A0 | Port 1 analog input (wired; firmware use varies) | PORT1 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A1 | Port 2 analog input (wired; firmware use varies) | PORT2 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A2 | Port 3 analog input (wired; firmware use varies) | PORT3 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A3 | Port 4 analog input (wired; firmware use varies) | PORT4 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A4 | Port 5 analog input (wired; firmware use varies) | PORT5 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A5 | Port 6 analog input (wired; firmware use varies) | PORT6 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A6 | Port 7 analog input (wired; firmware use varies) | PORT7 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A7 | Port 8 analog input (wired; firmware use varies) | PORT8 RJ45 pin 8 | Direct to Due analog input (3.3 V maximum) |
| A8 | Not connected on r0.5 mainboard | — | — |
| A9 | Not connected on r0.5 mainboard | — | — |
| A10 | Not connected on r0.5 mainboard | — | — |
| A11 | Not connected on r0.5 mainboard | — | — |

## Connector pinouts (physical nets)

### `SERIAL1` / `SERIAL2` (RJ45; **not Ethernet or RS-485**)

| RJ45 pin | SERIAL1 | SERIAL2 |
|---|---|---|
| 1 | +5 V | +5 V |
| 2 | GND | GND |
| 3 | TX (Due D18) | TX (Due D16) |
| 4 | RX via CD4050 (Due D19) | RX via CD4050 (Due D17) |
| 5 | Auxiliary GPIO (Due D20 / SDA) | Auxiliary GPIO (Due D15) |
| 6–8 | NC | NC |

### `PORT1`–`PORT8` (RJ45)

| RJ45 pin | Function | Due pin relationship |
|---|---|---|
| 1 | Digital input | PORT1–8 -> D28, D30, D32, D34, D36, D38, D40, D42, via CD4050 |
| 2 | +3.3 V | Due 3.3 V rail |
| 3 | LED/PWM output | PORT1–8 <- D9, D8, D7, D6, D5, D4, D3, D2 |
| 4 | +5 V | Due 5 V rail |
| 5 | GND | Common ground |
| 6 | +12 V | On-board 5 V-to-12 V converter |
| 7 | Valve drive output | Via VALVE_REGISTER; not a direct Due GPIO |
| 8 | Analog input | PORT1–8 -> A0–A7 |

### `U$6` 10-position spring terminal

| Terminal | Net | Due pin |
|---|---|---|
| 1 | GND | — |
| 2 | DSUB_BUS8 (output) | D43 |
| 3 | DSUB_BUS7 (output) | D41 |
| 4 | DSUB_BUS6 (output) | D39 |
| 5 | DSUB_BUS5 (output) | D37 |
| 6 | DSUB_BUS4 (input, buffered) | D35 |
| 7 | DSUB_BUS3 (input, buffered) | D33 |
| 8 | DSUB_BUS2 (input, buffered) | D31 |
| 9 | DSUB_BUS1 (input, buffered) | D29 |
| 10 | GND | — |

### `SYNC` RJ45

| RJ45 pin | Signal |
|---|---|
| 1 | GND |
| 2–8 | Outputs from `SYNC_REGISTER` (74HC595 family), driven over SPI; latch controlled by Due D23 |

### BNC sockets

| BNC schematic component | Function | Due |
|---|---|---|
| U$1 | Output jack (schematic ID) | D24 via Q3 / 5 V pull-up |
| U$2 | Output jack (schematic ID) | D25 via Q4 / 5 V pull-up |
| U$3 | Input jack (schematic net `BNCIN2`) | D11 via R3 + optocoupler |
| U$4 | Input jack (schematic net `BNCIN1`) | D10 via R2 + optocoupler |

**Firmware/panel numbering caution:** The previously inspected v23 r0.5 `OutputCh[]` array lists the two BNC outputs in order **D25, D24**. Thus the first firmware BNC output may refer to schematic jack `U$2`, and the second to `U$1`. Use the Due pin/jack identity from this document for electrical tracing, and confirm software ordering against the installed firmware.

## Other Arduino Due connections

- **SPI:** the Due's dedicated 2×3 `ICSP` header feeds `SPI_CLK` (ICSP pin 3) and `SPI_DATA` (ICSP pin 4) to both the `VALVE_REGISTER` and `SYNC_REGISTER`. D22 and D23 select/latch the respective registers. These SPI wires are **not** `D11`/`D13` as on an AVR Uno.
- **Power:** Due 3.3 V supplies `VCC` (CD4050 buffers, photogate rail, etc.); Due 5 V supplies the register logic, UART connector pin 1, etc. The 12 V valve supply comes from converter `U$5`. `GND` is shared across ports.
- **Status LED:** D12, D13 and D14 feed `U$8` (three distinct channels); exact color-to-pin mapping depends on the installed LED and firmware.
- **Unused on the Bpod PCB:** D0, D1, D21, D26, D27, D44–D53, A8–A11, and the AREF header pin do not have mainboard net connections in this schematic. Do not interpret this as proof they are freely usable without firmware checks.

## Notes and limitations

- Source is **r0.5 schematic** only; do not assume the same map applies to later Bpod hardware.
- Bpod firmware can assign output-index ordering independent of Due pin numbers. Verify firmware and `H` command hardware descriptions before issuing USB `O` overrides; the **Due D43 pin** is not synonymous with **USB output index 43**.
- Connector orientation matters: RJ45 pin numbers are **contact numbers**, not wire colors. Verify with a continuity tester before connecting devices.
- The UART connectors are **single-ended 3.3 V UART**, not RS-485 or standard Ethernet interfaces. Share GND with external equipment.
- The CD4050 buffer is *not* optoisolation and does not inherently guarantee immunity to floating inputs, transients or cable noise.

## References

- Uploaded source: `BpodMainBoard_r0_5.sch` (EAGLE XML).
- [Arduino Due pinout](https://docs.arduino.cc/hardware/due)
- [Sanworks State Machine firmware (all versions)](https://github.com/sanworks/Bpod_StateMachine_Firmware)
- [Firmware v23 r0.5 configuration](https://github.com/sanworks/Bpod_StateMachine_Firmware/tree/v23/Preconfigured/v23/StateMachine-Bpod0_5)
- [Bpod State Machine Serial Interface](https://sanworks.github.io/Bpod_Wiki/serial-interfaces/fsm-serial-interface-v17/)

