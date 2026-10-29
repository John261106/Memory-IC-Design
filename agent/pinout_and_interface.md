# Pinout, Interface & Timing Specification

## 1. External Signal Pinout

The memory chip uses strictly **five external signal pins** plus dedicated power and ground pins:

```
                  +---------------------------+
                  |    16x16 256-Bit SRAM     |
                  |                           |
  [PAD] CLK       |---> CLK              DOUT |---> DOUT [PAD]
  [PAD] CTRL      |---> CTRL (R/W)            |
  [PAD] ADDR_IN   |---> ADDR_IN               |
  [PAD] DIN       |---> DIN                   |
                  |                           |
  [PAD] VDD       |=== VDD (1.8V)             |
  [PAD] GND       |=== GND (0.0V)             |
                  +---------------------------+
```

### Signal Functional Table

| Pin | Direction | Description |
|---|---|---|
| `CLK` | Input | Master clock input. Synchronous operations trigger on rising/falling edges. |
| `CTRL` | Input | Control pin selecting operation mode: <br>• **HIGH (1.8 V)**: READ mode.<br>• **LOW (0.0 V)**: WRITE mode. |
| `ADDR_IN` | Input | 1-bit address line. Shifts in an 8-bit address over 8 clock pulses (or synchronizes a 256-step sequential address counter). |
| `DIN` | Input | 1-bit write data input presented to the write driver. |
| `DOUT` | Output | 1-bit read data output driven by the sense amplifier / output buffer. |
| `VDD` | Power | Core power supply: 1.8 V DC. |
| `GND` | Ground | Ground reference: 0.0 V DC. |

---

## 2. Operating Modes & Timing Protocols

### 2.1 Addressing Protocol (8-Bit SIPO Model)
Since there are 256 locations ($16 \times 16$), 8 address bits ($A_7 \dots A_0$) are required:
- **Phase 1: Address Shift (Cycles 1 to 8):**
  - Clock pulses shift 8 bits from `ADDR_IN` into an internal serial shift register.
  - Bits $A_7 \dots A_4$ latch to Row Address Decoder.
  - Bits $A_3 \dots A_0$ latch to Column Address Decoder.
- **Phase 2: Execution (Cycle 9):**
  - If `CTRL = 0` (Write): Data on `DIN` is written to address $A[7:0]$.
  - If `CTRL = 1` (Read): Stored data at address $A[7:0]$ is sensed and presented on `DOUT`.

*(Alternative Sequential Burst Protocol: If implemented as a sequential counter, each clock cycle advances the address by 1, and `ADDR_IN` serves as address frame sync / counter reset).*

---

### 2.2 Memory Operation Cycles

#### Write Cycle (`CTRL = 0` / LOW)
1. **Address Selection:** Row decoder asserts `WL[i] = 1.8 V`; column decoder opens column pass-gate for column `j`.
2. **Drive Bitlines:** Write driver pulls `BIT[j]` or `BITB[j]` to GND based on `DIN`.
3. **Cell Overwrite:** Access transistors force internal state nodes `Q`/`QB` to switch.
4. **De-assertion:** `WL[i]` returns to 0 V, latching the new bit in the cell.

#### Read Cycle (`CTRL = 1` / HIGH)
1. **Precharge Phase:** `PCB` pulses low, precharging all `BIT` and `BITB` lines to $V_{\text{DD}}$ (1.8 V). Equalizer balances both rails.
2. **Wordline Activation:** Row decoder asserts selected `WL[i] = 1.8 V`.
3. **Differential Discharge:** Cell discharges either `BIT` or `BITB` through the NMOS pull-down, developing $\Delta V_{\text{BL}} \ge 100\text{--}200\text{ mV}$.
4. **Sense Amp Strobe:** Sense amplifier is enabled (`SENSE_EN = 1.8 V`), amplifying $\Delta V_{\text{BL}}$ to full CMOS level.
5. **Output Presentation:** Latch/buffer places valid data on `DOUT`.

---

## 3. Timing Parameters & Constraints

| Parameter | Symbol | Target / Constraint | Description |
|---|---|---|---|
| Minimum Clock Period | $T_{\text{clk}}$ | Minimum cycle time for stable R/W | Limited by critical path delay |
| Max Clock Frequency | $F_{\text{max}}$ | $1 / T_{\text{clk}}$ | Maximum sustainable frequency |
| Address Setup Time | $t_{\text{setup,addr}}$ | $\ge 0.5\text{ ns}$ | `ADDR_IN` valid before `CLK` edge |
| Data Setup Time | $t_{\text{setup,din}}$ | $\ge 0.5\text{ ns}$ | `DIN` valid before write strobe |
| Clock-to-Output Delay | $t_{\text{CQ}}$ | Measured from `CLK` edge to valid `DOUT` | Total read latency |
| Bitline Precharge Time | $t_{\text{precharge}}$ | Minimum time for `BIT`/`BITB` to reach $0.98 \times V_{\text{DD}}$ | Required prior to wordline activation |
