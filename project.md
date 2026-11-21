# 16 × 16 (256-Bit) Transistor-Level Memory IC Design

## 1. Project Overview

This project encompasses the end-to-end design, implementation, and verification of a **2D array 16 × 16 (256-bit) Static Random-Access Memory (SRAM) IC**, spanning from transistor-level schematics to full custom physical layout.

The design incorporates individual 6T bit cells, row/column address decoding, read/write circuitry, sense amplifiers, precharge circuits, and output readout logic to ensure reliable memory operation under realistic operating conditions.

### External Interface Constraints
The memory core interfaces with the outside world through strictly **five external signals**:
1. **Control Signal (1-bit `CTRL` / `R_W`):** Controls operation mode (Read vs. Write).
2. **Address Input (1-bit `ADDR_IN`):** Single-bit serial or sequential address input used to address all 256 memory locations ($16 \times 16$).
3. **Clock Input (1-bit `CLK`):** Synchronizes addressing, precharge, write operations, and output latching.
4. **Data Input (1-bit `DIN`):** Serial input data to write into the selected bit cell.
5. **Data Output (1-bit `DOUT`):** Output data retrieved from the selected bit cell.

*(In addition to dedicated power `VDD` and ground `GND` lines).*

---

## 2. Project Objectives & Key Requirements

- **Transistor-Level Design:** Full custom implementation at the transistor level (TSMC 0.18 µm CMOS process, 1.8 V nominal supply).
- **Area Optimization:** Minimize layout area through optimized cell sizing, compact symmetric 6T bitcell layout, shared diffusion contacts, and dense routing.
- **Power Characterization:** Measure average and peak power / energy consumed during bit read and write cycles.
- **Maximum Clock Frequency ($F_{\text{max}}$):** Identify the critical timing path and determine the maximum achievable operating frequency across process corners.
- **I/O Pad & Bond Wire Circuitry:** All 5 external signals (plus power supplies) must incorporate equivalent RLC bond wire and I/O pad circuits to model real-world chip packaging parasitics and loading.
- **Clock Tree Distribution:** Implement a balanced clock distribution tree network to eliminate clock skew across row decoders, column multiplexers, address registers, and sense amps.
- **Top-Metal Power & Ground Routing:** Route power (`VDD`) and ground (`GND`) distribution grids exclusively on the topmost available metal layers (e.g., Metal 5/6) to reduce IR drop, electromigration, and parasitic RC degradation.
- **Dual-Level Verification:** Validate functional correctness and timing both at the schematic level and post-layout level (including parasitic extraction).

---

## 3. Specifications Summary

| Parameter | Specification | Measured / Implementation Value | Notes / Description |
|---|---|:---:|---|
| **Array Architecture** | 16 rows × 16 columns | **16 × 16** | 2D rectangular array |
| **Total Storage** | 256 bits (32 bytes) | **256 bits** | Individually addressable bits |
| **External Signal Count** | 5 signal pins | **5 pins** | `CLK`, `CTRL` (R/W), `ADDR_IN`, `DIN`, `DOUT` (+ `VDD`, `GND`) |
| **Supply Voltage** | 1.8 V nominal | **1.80 V** | TSMC 0.18 µm standard CMOS ($L_{\text{min}} = 0.18\,\mu\text{m}$, $\lambda = 90\text{ nm}$) |
| **Operating Frequency** | 100 MHz target | **100 MHz** ($T = 10\text{ ns}$) | Maximum tested $> 125\text{ MHz}$ packaged ($> 400\text{ MHz}$ core limit) |
| **Bit Cell Type** | 6T SRAM Cell | **Continuous Shared-Diffusion** | Sized for Read SNM $> 160\text{ mV}$, $CR = 1.75$, $PR = 1.33$ |
| **Addressing Mechanism** | 8-bit Serial / Sequential | **8-Bit SIPO Shift Register** | Maps 1-bit input over 8 clock cycles ($A_7..A_4$ Row, $A_3..A_0$ Col) |
| **Row Decoder** | 4-to-16 Decoder | **Static CMOS NAND4 + INV** | Active-high Word Line gating via `WL_driver` ($t_{\text{rise}} = 289\text{ ps}$) |
| **Column Selection** | 16-to-1 MUX / Pass Gates | **16 CMOS Transmission Gates** | Mobility-matched $W_P=8\lambda, W_N=4\lambda$ with local inverters |
| **Read Path** | Precharge + Sense Amp | **Current-Mirror OTA + DFF Latch** | Resolves $\Delta V \le 50 - 100\text{ mV}$ to rail-to-rail $1.8\text{ V}$ |
| **Write Path** | Tri-state Write Driver | **Series NMOS Pull-Down Stacks** | Discharges 50 fF bitline in $< 450\text{ ps}$ down to $< 1\,\mu\text{V}$ |
| **I/O Buffering** | Multi-stage in/out buffers | **Input Buffers + Size-32 Output Buffer** | Restores input slew; drives external $C_{\text{dout}} = 20\text{ fF}$ load |
| **Packaging Model** | 2-Stage Bond Wire RLC | $L = 4.5\text{ nH}, R = 0.25\,\Omega, C_{\text{pad}} = 1.9\text{ pF}$ | 2-stage ladder on all 7 chip pins with $50\,\Omega$ PCB source termination |
| **Silicon Area (`Top{lay}`)** | Minimum rectangular die | **$0.03746\text{ mm}^2$** | $163.08\,\mu\text{m} \times 229.73\,\mu\text{m}$ ($1812\lambda \times 2552.5\lambda$) |
| **DRC / LVS Status** | Zero errors / 100% Match | **0 DRC Errors / 100% LVS Match** | 100% Manhattan geometry (0 diagonal arcs); full sizing match |

---

## 4. Architectural Block Breakdown

```
                         +-----------------------+
                         |      1-Bit CLK        |
                         +-----------+-----------+
                                     |
                             [ Clock Tree Network ]
                                     |
               +---------------------+---------------------+
               |                     |                     |
+--------------v-------+    +--------v----------+    +-----v---------------+
| 1-Bit Serial ADDR_IN |    | 1-Bit CTRL (R/W)  |    | 1-Bit DIN           |
+--------------+-------+    +--------+----------+    +-----+---------------+
               |                     |                     |
     [ 8-Bit Address Engine ]        |                     |
      (Serial-in / Counter)          |                     |
        |               |            |                     |
    [Row Addr]     [Col Addr]        |                     |
      (4-bit)        (4-bit)         |                     |
        |               |            |                     |
+-------v-------+  +----v-------+    |                     |
| 4-to-16 Row   |  | 4-to-16    |    |                     |
| Decoder       |  | Col MUX/Dec|    |                     |
+-------+-------+  +----+-------+    |                     |
        |               |            |                     |
     16 WLs          16 BL/BLB pairs |                     |
        |               |            |                     |
+-------v---------------v----+       |                     |
|                            |       |                     |
|    16 x 16 6T SRAM Array   |       |                     |
|        (256 Bits)          |       |                     |
|                            |       |                     |
+---------------+------------+       |                     |
                |                    |                     |
        +-------v-------+    +-------v-------+             |
        | Precharge Ckt |    | Write Drivers <-------------+
        +-------+-------+    +---------------+
                |
        +-------v-------+
        | Sense Amplif. |
        +-------+-------+
                |
        +-------v-------+
        | 1-Bit DOUT    |
        +---------------+
```

### 4.1 6T SRAM Bit Cell
- Dual cross-coupled CMOS inverters ($M_1, M_2, M_3, M_4$) storing complementary state nodes $Q$ and $\bar{Q}$.
- Two NMOS pass-gate access transistors ($M_5, M_6$) controlled by Word Line (`WL`), coupling the cell to complementary bit lines (`BIT`, `BITB`).
- Sizing optimized for Static Noise Margin (SNM), read stability (cell ratio $\beta_{\text{driver}} / \beta_{\text{access}} \ge 1.5 - 2.0$), and writeability (pull-up ratio $\beta_{\text{access}} / \beta_{\text{pullup}} \ge 1.0 - 1.2$).

### 4.2 8-Bit Addressing Mechanism
Because only a **single external address pin (`ADDR_IN`)** is available, an on-chip address generation engine bridges the external interface to the 256 memory locations:
- **Serial Address Shift Register / Sequential Counter:** An 8-bit register clocked by `CLK` loads or steps through the 8 address bits:
  - Higher 4 bits (`A[7:4]`): 4-to-16 Row Address Decoder selecting `WL[0:15]`.
  - Lower 4 bits (`A[3:0]`): 4-to-16 Column Address Decoder selecting `COL[0:15]`.

### 4.3 4-to-16 Address Decoders
- High-speed pseudo-NMOS or static CMOS NOR/NAND decoding logic.
- Buffers inserted on `WL` lines to drive the capacitance of 16 access transistor gates along each row.

### 4.4 Read & Write Peripheral Circuitry
- **Bitline Precharge & Equalization:** Active-low PMOS precharge circuit precharging `BIT` and `BITB` to $V_{\text{DD}}$ prior to read operations.
- **Sense Amplifiers:** Differential latch-type or current-mirror sense amplifiers to resolve millivolt bitline differentials to full CMOS logic levels ($0 \to 1.8\text{ V}$).
- **Write Drivers:** Tri-state pull-down drivers enabled by write signal that overpower the internal bit cell latch during write mode.

### 4.5 Package & I/O Pad Equivalent Model
To represent real-world chip integration, each external pin (`CTRL`, `ADDR_IN`, `CLK`, `DIN`, `DOUT`, `VDD`, `GND`) is modeled with:
- Bond wire inductance: $L_{\text{bond}} \approx 1.0\text{--}2.5\text{ nH}$
- Bond wire series resistance: $R_{\text{bond}} \approx 0.05\text{--}0.2\ \Omega$
- Pad capacitance to ground: $C_{\text{pad}} \approx 0.5\text{--}1.2\text{ pF}$
- Electrostatic Discharge (ESD) protection network representation.

### 4.6 Clock Distribution Tree Network
- Balanced H-tree / symmetric buffer tree distributing the high-speed clock across the 16x16 array periphery, address register, and sense amplifier strobes with matched delays and minimal clock skew.

### 4.7 Top-Metal Power & Ground Distribution
- Wide `VDD` and `GND` trunks and distribution rings implemented on the topmost metal layers (Metal 5 and Metal 6) to achieve low sheet resistance, eliminate IR drop, prevent ground bounce during simultaneous sense amp firing, and satisfy electromigration constraints.

---

## 5. Verification & Characterization Strategy

### 5.1 Functional Verification
- **Write 0 / Write 1:** Verify robust state switching across all 256 memory cells.
- **Read 0 / Read 1:** Verify bitline differential development, sense amplifier latching, and valid output on `DOUT`.
- **Sequential 256-Bit Sweep:** Automated serial address sweep across all 256 cells sequentially to verify non-destructive reads and zero cross-talk between adjacent cells.
- **Read-After-Write Cycle:** Verify dynamic write recovery and minimum precharge time.

### 5.2 Power Characterization
- Calculate dynamic and static energy per operation:
  $$E_{\text{read}} = \int_{0}^{T_{\text{read}}} V_{\text{DD}} \cdot I_{\text{DD}}(t)\,dt$$
  $$E_{\text{write}} = \int_{0}^{T_{\text{write}}} V_{\text{DD}} \cdot I_{\text{DD}}(t)\,dt$$
- Report energy per bit (fJ/bit) and total average power consumption at maximum clock frequency.

### 5.3 Timing & Maximum Frequency ($F_{\text{max}}$)
- Characterize setup/hold times ($t_{\text{setup}}, t_{\text{hold}}$), clock-to-output delay ($t_{\text{CQ}}$), address decode delay, bitline discharge delay, and sense amplifier activation window.
- Determine maximum clock frequency:
  $$F_{\text{max}} = \frac{1}{T_{\text{clk,min}}}$$

### 5.4 Physical Design & Post-Layout Simulation
- Design Rule Checking (DRC) and Layout Versus Schematic (LVS) cleanliness in Electric VLSI 9.08.
- Extract parasitic capacitances and resistances from layout.
- Compare pre-layout vs. post-layout SPICE waveforms.

---

## 6. Deliverables

1. Full transistor-level schematic database in Electric VLSI (`Memory-IC-Design.jelib`).
2. SPICE netlists for individual cells, 16x16 array, decoders, peripheral circuitry, and full top-level chip.
3. Physical layout with DRC and LVS reports (`Top{lay}`: 0 DRC errors, 0 warnings, 100% LVS match).
4. Packaged chip integration (`Top_package{sch}`, `Top_package{lay}`) with bond wire RLC and I/O buffers.
5. Comprehensive characterization reports:
   - Area breakdown ($0.03746\text{ mm}^2$)
   - Read & write power and energy consumption per bit
   - Maximum operating frequency ($> 125\text{ MHz}$)
   - Post-package waveforms with bond wire RLC parasitics and $50\,\Omega$ PCB source termination.

---

## 7. Final Measured Characterization Results (Packaged IC)

The final design was characterized via complete post-package transient simulation in LTspice XVII (`spice/Top_package_test.spi`) over 4 consecutive 8-cycle frames ($340\text{ ns}$ transient window):

| Metric | Symbol / Parameter | Value | Condition / Notes |
|:---|:---|:---:|:---|
| **Core Supply Voltage** | $V_{\text{DD}}$ | **1.80 V** | Nominal TSMC 0.18 µm CMOS |
| **Clock Frequency** | $F_{\text{clk}}$ | **100 MHz** | Clock period $T = 10\text{ ns}$ |
| **Standby / Leakage Power** | $P_{\text{leak}}$ | **23.86 µW** | Pre-clock static leakage ($0 - 4.9\text{ ns}$) |
| **Active Write '1' Power / Energy** | $P_{\text{w1}} / E_{\text{w1}}$ | **187.43 µW / 0.937 pJ** | Cycle 8 ($80 - 85\text{ ns}$) write pulse into Cell (10, 5) |
| **Active Write '0' Power / Energy** | $P_{\text{w0}} / E_{\text{w0}}$ | **176.09 µW / 0.880 pJ** | Cycle 16 ($160 - 165\text{ ns}$) write pulse into Cell (3, 12) |
| **Average Active Write Power / Energy** | $P_{\text{w,avg}} / E_{\text{w,avg}}$ | **181.76 µW / 0.909 pJ** | 5 ns active window ($P_{\text{peak}} = 3.69\text{ mW}$) |
| **Active Read '1' Power / Energy** | $P_{\text{r1}} / E_{\text{r1}}$ | **201.59 µW / 1.008 pJ** | Cycle 24 ($240 - 245\text{ ns}$) read & latch Cell (10, 5) |
| **Active Read '0' Power / Energy** | $P_{\text{r0}} / E_{\text{r0}}$ | **294.56 µW / 1.473 pJ** | Cycle 32 ($320 - 325\text{ ns}$) read & latch Cell (3, 12) |
| **Average Active Read Power / Energy** | $P_{\text{r,avg}} / E_{\text{r,avg}}$ | **248.08 µW / 1.241 pJ** | 5 ns active window ($P_{\text{peak}} = 3.69\text{ mW}$) |
| **Continuous Full-Chip Average Power** | $P_{\text{chip,avg}}$ | **203.85 µW** | Continuous operating average ($5 - 325\text{ ns}$, 32 cycles) |
| **Total Energy (32 Clock Cycles)** | $E_{\text{total}}$ | **65.23 pJ** | Cumulative $\int V_{\text{DD}} \cdot I_{\text{DD}} \, dt$ |
| **Read Output Voltage HIGH** | $V_{\text{OH}}$ | **1.802 V** | Full-rail logic '1' at `DOUT_PCB` terminal |
| **Read Output Voltage LOW** | $V_{\text{OL}}$ | **-0.005 V** ($\approx 0\text{ V}$) | Full-rail logic '0' at `DOUT_PCB` terminal |
| **Write '1' Cell Flip Time** | $t_{\text{write1}}$ | **1.02 ns** | From Cycle 8 clock fall to Cell (10, 5) state flip |
| **Write '0' Cell Flip Time** | $t_{\text{write0}}$ | **1.02 ns** | From Cycle 16 clock fall to Cell (3, 12) state flip |
| **Half-Select Disturb Retention** | $V_{\text{disturb}}$ | **1.7988 V** | Cell (10, 4) & Cell (9, 5) full state retention |
| **Physical Layout Area (`Top{lay}`)** | Silicon Footprint | **0.03746 mm²** | $163.08\,\mu\text{m} \times 229.73\,\mu\text{m}$ ($1812\lambda \times 2552.5\lambda$) |
| **Layout Cleanliness** | DRC & NCC/LVS | **0 Errors, 100% Match** | 100% Manhattan geometry; zero DRC errors/warnings |
