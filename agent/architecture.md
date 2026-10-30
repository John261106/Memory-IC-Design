# Architecture & Circuit Implementation Reference

## 1. Top-Level Memory Organization
The 256-bit memory is organized into a $16 \times 16$ 2D matrix:
- **Rows:** 16 rows, each activated by a dedicated Wordline `WL[0:15]`.
- **Columns:** 16 columns, each connected to a complementary bitline pair `BIT[0:15]` and `BITB[0:15]`.
- **Addressing:** An 8-bit internal address ($A_7 \dots A_0$):
  - $A_7, A_6, A_5, A_4$: Row address decoded into 1 of 16 Wordlines.
  - $A_3, A_2, A_1, A_0$: Column address decoded into 1 of 16 Column multiplexer selects.

---

## 2. Transistor-Level Circuit Topologies

### 2.1 6T SRAM Cell
- **Scalable Rules Basis:** $\lambda = 90\text{ nm}$, $180\text{ nm} = 2\lambda$. All lengths $L = 2\lambda = 0.18\ \mu\text{m}$.
- **Sizing Ratios & Dimensions:**
  - **Pull-Up PMOS ($M_{\text{PU}}$):** $W = 3\lambda = 0.27\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (weakest, enables easy overwrite).
  - **Access NMOS ($M_{\text{AX}}$):** $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ ($\text{PR} = 4\lambda/3\lambda = 1.33$).
  - **Pull-Down NMOS ($M_{\text{PD}}$):** $W = 7\lambda = 0.63\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ ($\text{CR} = 7\lambda/4\lambda = 1.75$).
- **Performance Criteria:**
  - Hold SNM $> 300\text{ mV}$ (butterfly curve at $WL = 0\text{ V}$).
  - Read SNM $> 150\text{ mV}$ (butterfly curve at $WL = 1.8\text{ V}, BIT=BITB=1.8\text{ V}$).
  - Write Trip Margin $V_{\text{trip}} \approx 0.6\text{--}0.9\text{ V}$.

### 2.2 Precharge & Equalization Unit
- **Topology:** Three PMOS transistors active low (`PCB = 0`):
  - Two PMOS pull-ups charging `BIT` and `BITB` to $V_{\text{DD}}$.
  - One PMOS equalizer connected between `BIT` and `BITB` to guarantee zero initial differential voltage.

### 2.3 Write Driver Unit
- **Topology:** Tri-state NMOS/PMOS pull-down logic gated by `WRITE_EN` and input data `DATA`:
  - When `WRITE_EN = 1` and `DATA = 1`: pulls `BITB` to GND, leaves `BIT` high.
  - When `WRITE_EN = 1` and `DATA = 0`: pulls `BIT` to GND, leaves `BITB` high.
  - When `WRITE_EN = 0`: high impedance (Hi-Z) so read operations are not perturbed.

### 2.4 Sense Amplifier Unit
- **Topology:** Differential voltage latch-type sense amplifier or current-mirror amplifier enabled by `READ_EN` / `SENSE_EN`.
- Rapidly amplifies a small differential $\Delta V_{\text{BL}} \approx 100\text{--}200\text{ mV}$ between `BIT` and `BITB` to full-rail CMOS levels ($0 \to 1.8\text{ V}$), reducing active power and access delay.

### 2.5 4-to-16 Row & Column Decoders
- **Row Decoder:** 4 address bits ($A[7:4]$) $\to$ 16 Wordline drivers (`WL[0:15]`). Static CMOS NAND/NOR structure with driving inverters/buffers sized to charge the parasitic gate capacitance of 16 bitcell access transistors.
- **Column Decoder / Multiplexer:** 4 address bits ($A[3:0]$) $\to$ 16 column transmission gates or NMOS pass-transistor pairs connecting the selected `BIT[k]` / `BITB[k]` to the global data lines.

### 2.6 Serial Address Generation Engine
Because only **1 external address pin (`ADDR_IN`)** is provided:
- **Option A (Serial Shift Register):** An 8-bit Serial-In Parallel-Out (SIPO) shift register clocked by `CLK`. Takes 8 clock cycles to shift in an 8-bit target address before issuing Read/Write.
- **Option B (Sequential Counter with Reset):** An 8-bit synchronous binary counter incrementing each clock cycle, with `ADDR_IN` serving as address reset / sync pulse or serial address increment strobe.
- **Output:** 8 parallel lines ($A[7:0]$) split into Row Address ($A[7:4]$) and Column Address ($A[3:0]$).

---

## 3. Clock Distribution Network
- **Architecture:** Symmetric H-Tree or balanced inverter buffer tree.
- **Purpose:** Distributes the external `CLK` to:
  1. Address shift register / counter flip-flops.
  2. Precharge control pulse generator.
  3. Sense amplifier enable strobe generator.
  4. Output readout latch.
- **Goal:** Equalize delay to all clocked nodes, keeping clock skew $< 50\text{ ps}$.

---

## 4. Top-Metal Power & Ground Distribution
- **Routing Strategy:**
  - Lower metal layers (Metal 1, Metal 2, Metal 3) are reserved for bitcell local connections, wordlines, bitlines, and decoder interconnect.
  - Upper metal layers (Metal 4/5/6) form an orthogonal $V_{\text{DD}}$ / GND mesh.
  - Wide top-metal stripes maximize current-carrying capability, suppress IR drop across the 16x16 matrix, and prevent ground bounce.

---

## 5. Bond Wire & I/O Pad Equivalent Circuit
Every external pin (`CTRL`, `ADDR_IN`, `CLK`, `DIN`, `DOUT`, `VDD`, `GND`) connects through a packaging sub-circuit:

```
[ External Board Pin ]
         |
      [ L_bond = 1.5 nH ]
         |
      [ R_bond = 0.1 ohm ]
         |
         +-----------------+
         |                 |
    [ C_pad = 0.8 pF ]  [ Core Input / Output Buffer ]
         |
       (GND)
```
- Includes ESD diode loading where applicable.
- Verifies that external driving impedances and packaging rings do not degrade edge rates or induce ringing.
