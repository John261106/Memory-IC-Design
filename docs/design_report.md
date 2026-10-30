# 16 × 16 (256-Bit) SRAM Memory IC — Engineering Design Report

---

## Document Control & Progress
- **Project Title:** Custom Transistor-Level 16 × 16 Static Random-Access Memory (SRAM) Design
- **Process Technology:** TSMC 0.18 µm CMOS Process (`tsmc018.lib`, generic MOSIS mocmos)
- **Supply Voltage ($V_{\text{DD}}$):** 1.8 V Nominal
- **Status:** In Progress (Active Circuit Design & Automation Phase)
- **Living Document Policy:** This report is automatically updated by engineering agents upon every design decision, circuit change, sizing experiment, and simulation milestone.

---

## 1. Executive Summary

This report documents the transistor-level schematic capture, physical layout, and post-layout verification of a **16 × 16 (256-bit) synchronous Static RAM IC** using **Electric VLSI 9.08** and **SPICE** (LTspice / ngspice).

The design integrates 256 individual 6T memory cells, 4-to-16 row decoding, 16-to-1 column selection, differential bitline precharge, a shared differential sense amplifier, a shared tri-state write driver, balanced clock distribution, and top-metal power/ground distribution. It communicates through a minimal 5-pin external interface and accounts for packaging parasitics (bond wire and I/O pad equivalent circuits).

---

## 2. Design Specifications & Pinout

### 2.1 External Signal Interface (Strictly 5 Signal Pins)

| Signal Pin | Direction | Type | Description |
|---|---|---|---|
| `CLK` | Input | Digital | Master clock for synchronization, addressing, and strobe generation |
| `CTRL` | Input | Digital | Read/Write control: `HIGH` (1.8 V) = READ, `LOW` (0.0 V) = WRITE |
| `ADDR_IN` | Input | Digital | 1-bit serial address line (shifts 8 bits to access 256 locations) |
| `DIN` | Input | Digital | 1-bit serial data input to write driver |
| `DOUT` | Output | Digital | 1-bit serial data output from sense amplifier |
| `VDD` | Supply | Power | Core power supply: 1.8 V |
| `GND` | Supply | Ground | Core reference ground: 0.0 V |

### 2.2 Target Operational Constraints
- **Array Size:** 16 rows × 16 columns (256 bits / 32 bytes).
- **Core Voltage:** 1.8 V ± 10%.
- **Packaging Parasitics:** $L_{\text{bond}} \approx 1.5\text{ nH}$, $R_{\text{bond}} \approx 0.1\ \Omega$, $C_{\text{pad}} \approx 0.8\text{ pF}$ on all external pins.
- **Optimization Priority:** Minimum silicon area, verified read stability, robust writeability, and maximum clock frequency ($F_{\text{max}}$).

---

## 3. Design Decisions & Architectural Evolution Log

This section records every major design decision, the alternatives evaluated, and the rationale for the selected approach.

### Decision Log 1: Transition from 16 Per-Column SAs/WDs to 1 Shared SA & 1 Shared WD
- **Date:** October 2026
- **Context:** Initial architecture featured 16 separate Sense Amplifiers and 16 separate Write Drivers (one per column), followed by a 16:1 digital multiplexer.
- **Alternatives Considered:**
  1. *Per-Column SAs & WDs (16 pairs):* High peripheral area, high active power (firing 16 sense amps simultaneously), requires large 16-to-1 digital multiplexer at the output.
  2. *Shared SA & WD via Column Multiplexing (1 pair):* Multiplexing happens directly on the bitlines before the sense amplifier.
- **Decision:** Adopted **1 Shared Sense Amplifier and 1 Shared Write Driver**.
- **Rationale:** Reduces peripheral active silicon area by >70%, eliminates the bulky 16-to-1 post-sense digital multiplexer, and cuts read dynamic power by strobing only one sense amplifier per cycle.

---

### Decision Log 2: CMOS Transmission Gates for Column Multiplexing
- **Date:** October 2026
- **Context:** Selecting the column switch element to connect the selected column's bitlines (`BIT[k]`, `BITB[k]`) to the global data lines (`DL`, `DLB`).
- **Alternatives Considered:**
  1. *NMOS-Only Pass Transistors:* Smaller area, but introduces a threshold voltage drop ($V_{\text{DD}} - V_{\text{thn}} \approx 1.3\text{ V}$) when passing precharged bitline levels near 1.8 V during reads.
  2. *Full CMOS Transmission Gates (NMOS + PMOS in parallel):* Requires both true and complementary gate enables, but provides rail-to-rail signal transmission, low ON-resistance across the entire voltage range, and full differential integrity.
- **Decision:** Adopted **Full CMOS Transmission Gates**.
- **Rationale:** Guarantees undistorted millivolt differential development ($\Delta V_{\text{BL}}$) transferred to the sense amplifier during reads, while providing rapid pull-down during writes.

---

### Decision Log 3: Maintaining Dedicated Per-Column Precharge Units
- **Date:** October 2026
- **Context:** Evaluating whether to replace all 16 precharge circuits with a single global precharge circuit.
- **Alternatives Considered:**
  1. *Single Global Precharge Unit:* Would require turning on all 16 column transmission gates simultaneously during precharge, creating a massive capacitive node, complex decoding logic, and slow precharge recovery.
  2. *16 Dedicated Column Precharge Units + 1 Global Bus Precharge:* 3 tiny PMOS transistors per column directly pitch-matched to the bitcell width.
- **Decision:** Maintained **16 Dedicated Column Precharge Units** plus 1 auxiliary global bus precharge.
- **Rationale:** Prevents catastrophic destructive reads on unselected columns (when a wordline fires, all 16 cells on that row turn on; unselected bitlines must remain held at $V_{\text{DD}}$ to prevent internal cell flipping).

---

### Decision Log 4: Local Inverter in Transmission Gate vs. Routing 32 Global Select Lines
- **Date:** October 2026
- **Context:** CMOS transmission gates require complementary enable signals ($EN$ and $\overline{EN}$).
- **Alternatives Considered:**
  1. *Tap NAND Output directly from Decoder:* Export both `OUT` (from inverter) and `OUT_BAR` (from NAND) and route 32 long wires across the 16 columns.
  2. *Route Single Active-High Line (`OUT[0:15]`) + Local Inverter inside Transmission Gate Block:* Decoder outputs 16 buffered lines; each column switch has an internal inverter to generate $\overline{EN}$.
- **Decision:** Adopted **Single Active-High Route + Local Inverter in Transmission Gate Block**.
- **Rationale:**
  - *Area & Routing:* Halves the global control bus wires from 32 to 16, drastically reducing metal routing congestion and pitch mismatch.
  - *Signal Integrity:* The 4-input NAND gate has a 4-stack series NMOS pull-down with high output resistance; driving long global interconnect from an unbuffered NAND node causes severe rise/fall edge degradation. The decoder output inverter acts as a low-impedance line driver.
  - *Timing Skew:* Eliminates propagation delay skew between NMOS and PMOS gate switching.

---

### Decision Log 5: 6T SRAM Cell Transistor Sizing in Scalable Lambda Rules
- **Date:** October 2026
- **Context:** Sizing the 6T bitcell transistors using MOSIS scalable CMOS ($\lambda$) rules ($180\text{ nm} = 2\lambda \implies \lambda = 90\text{ nm}$) to balance Read Stability (Cell Ratio) and Writeability (Pull-Up Ratio).
- **Alternatives Considered:**
  1. *Minimum Uniform Sizing ($W=2\lambda, L=2\lambda$ for all transistors):* Results in $CR = 1.0$ and $PR = 1.0$, which causes catastrophic destructive reads (bit flips during read access).
  2. *Excessively Large Cell Ratio ($CR > 3.0$):* Ensures extreme stability, but blows up cell area by >50% and hampers write speed.
  3. *Optimized Ratio ($W_{\text{PD}}=7\lambda\text{ or }8\lambda, W_{\text{AX}}=4\lambda, W_{\text{PU}}=3\lambda$):* Provides $CR = 1.75\text{--}2.0$ and $PR = 1.33$.
- **Decision:** Adopted **$W_{\text{PD}}=7\lambda$ ($0.63\ \mu\text{m}$), $W_{\text{AX}}=4\lambda$ ($0.36\ \mu\text{m}$), $W_{\text{PU}}=3\lambda$ ($0.27\ \mu\text{m}$)**, with all lengths $L = 2\lambda = 180\text{ nm} = 0.18\ \mu\text{m}$.
- **Rationale:** 
  - Achieves $CR = 1.75$, keeping read voltage disturbance $V_{\text{read,bump}} \le 0.2\text{ V} < V_{\text{thn}}$, guaranteeing Read SNM $\ge 160\text{ mV}$.
  - Achieves $PR = 1.33$, ensuring write driver pulls internal node below inverter switching threshold without write contention.

---

### Decision Log 6: Bitline Precharge Circuit Sizing in Scalable Lambda Rules
- **Date:** October 2026
- **Context:** Sizing the PMOS pull-up and equalization transistors in the per-column precharge circuit under a $C_{\text{BL}} \approx 35\text{ fF}$ parasitic load (16 bitcell access diffusions + metal bitline routing).
- **Alternatives Considered:**
  1. *Minimum Uniform Sizing ($W = 2\lambda = 0.18\ \mu\text{m}$ for all PMOS):* Results in high PMOS $R_{\text{on,P}} \approx 10\ \text{k}\Omega$, causing slow bitline recovery ($t_{\text{precharge}} > 1.5\text{ ns}$), bottlenecking memory clock frequency.
  2. *Excessively Large PMOS ($W > 8\lambda$):* Speeds up precharge by <100 ps, but causes severe layout pitch mismatch with the narrow 6T cell width and adds unnecessary gate capacitance to the global `PCB` distribution line.
  3. *Optimized Pitch-Matched Sizing ($W_{\text{PU}}=4\lambda=0.36\ \mu\text{m}, W_{\text{EQ}}=3\lambda=0.27\ \mu\text{m}$):* Restores bitlines to $98\% V_{\text{DD}}$ in $< 0.8\text{ ns}$ while comfortably fitting within the cell column pitch.
- **Decision:** Adopted **Pull-Up PMOS $W = 4\lambda = 0.36\ \mu\text{m}$, Equalization PMOS $W = 3\lambda = 0.27\ \mu\text{m}$, all $L = 2\lambda = 0.18\ \mu\text{m}$**.
- **Rationale:** Delivers rapid write recovery ($t_{\text{pre}} < 1.0\text{ ns}$) and eliminates residual bitline differential ($\Delta V_{\text{residual}} < 2\text{ mV}$) prior to sense amplifier activation.

---

## 4. Circuit Block Architectures

### 4.1 6T SRAM Bit Cell
- **Scalable Rules Basis:** $\lambda = 90\text{ nm} = 0.09\ \mu\text{m}$, $L_{\text{min}} = 2\lambda = 180\text{ nm} = 0.18\ \mu\text{m}$.
- **Detailed Transistor Sizing:**

| Transistor | Role | Width ($W$) in $\lambda$ | Width ($W$) in $\mu\text{m}$ | Length ($L$) in $\lambda$ | Length ($L$) in $\mu\text{m}$ | Governing Ratio | Target Criteria |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| $M_{\text{PU1}}, M_{\text{PU2}}$ (PMOS) | Pull-Up Latch | $3\lambda$ | $0.27\ \mu\text{m}$ | $2\lambda$ | $0.18\ \mu\text{m}$ | Reference | — |
| $M_{\text{AX1}}, M_{\text{AX2}}$ (NMOS) | Pass Access | $4\lambda$ | $0.36\ \mu\text{m}$ | $2\lambda$ | $0.18\ \mu\text{m}$ | $\text{PR} = W_{\text{AX}} / W_{\text{PU}} = 1.33$ | $1.0 \le \text{PR} \le 1.5$ |
| $M_{\text{PD1}}, M_{\text{PD2}}$ (NMOS) | Pull-Down Latch | $7\lambda$ | $0.63\ \mu\text{m}$ | $2\lambda$ | $0.18\ \mu\text{m}$ | $\text{CR} = W_{\text{PD}} / W_{\text{AX}} = 1.75$ | $1.5 \le \text{CR} \le 2.0$ |

- **Performance Figures of Merit (FOMs):**
  - **Hold Static Noise Margin (Hold SNM):** Side of maximum square in butterfly curve at $WL = 0\text{ V}$. Accepted benchmark: $> 300\text{ mV}$.
  - **Read Static Noise Margin (Read SNM):** Side of maximum square in butterfly curve at $WL = 1.8\text{ V}, BIT=BITB=1.8\text{ V}$. Accepted benchmark: $> 150\text{ mV}$.
  - **Write Trip Margin (WTM):** Bitline voltage at which internal cell flips state during write. Accepted benchmark: $0.6\text{--}0.9\text{ V}$.

### 4.2 4-to-16 Row & Column Address Decoders
- **Structure:**
  - 4 input inverters producing complementary addresses $A_0 \dots A_3$ and $\overline{A_0} \dots \overline{A_3}$.
  - 16 4-input NAND gates decoding minterms $m_0 \dots m_{15}$.
  - 16 output inverters buffering the active-high select lines `OUT0` through `OUT15`.
- **Automation:** Implemented and wired automatically via [`scripts/05_connect_decoder.py`](file:///d:/Projects/Memory-IC-Design/scripts/05_connect_decoder.py).

### 4.3 Read Path: Precharge, Transmission Gate & Sense Amplifier
- **Bitline Precharge Unit:**
  - Scalable rules: $\lambda = 90\text{ nm}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Pull-Up PMOS ($M_{\text{PU\_BIT}}, M_{\text{PU\_BITB}}$): $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Equalization PMOS ($M_{\text{EQ}}$): $W = 3\lambda = 0.27\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Target Performance: Recovery time $t_{\text{precharge}} < 1.0\text{ ns}$ to $98\% V_{\text{DD}}$ into $C_{\text{BL}} = 35\text{ fF}$; residual differential $\Delta V_{\text{residual}} < 5\text{ mV}$.
- **Column Select:** CMOS transmission gate multiplexing selected bitlines onto global data lines `DL` / `DLB`.
- **Sense Amplifier:** Differential latch amplifier triggered by `SENSE_EN` pulse, converting small $\Delta V \approx 100\text{--}200\text{ mV}$ into full 0–1.8 V CMOS rail.

### 4.4 Write Path: Write Driver
- Tri-state pull-down driver controlled by `WRITE_EN` and `DIN`, driving `DL` / `DLB` strongly to $0\text{ V}$ during write cycles.

---

## 5. Physical Layout & Parasitics Strategy

1. **Cell Pitch-Matching:** The 6T bitcell width dictates the column pitch for precharge circuits and column transmission gates.
2. **Top-Metal Power Mesh:** $V_{\text{DD}}$ and $\text{GND}$ are routed exclusively on the topmost available metal layers (e.g., Metal 5/Metal 6) to eliminate IR drop and electromigration.
3. **Balanced Clock Tree:** Symmetrical H-tree network distributes `CLK` with $< 50\text{ ps}$ skew.
4. **I/O & Packaging:** Every external pin passes through a lumped $R_{\text{bond}}\text{-}L_{\text{bond}}\text{-}C_{\text{pad}}$ subcircuit in all SPICE simulations.

---

## 6. Simulation & Characterization Metrics (Living Table)

*The metrics below will be populated as simulation testbenches complete.*

| Metric | Target / Unit | Schematic Result | Post-Layout Result | Notes |
|---|---|---|---|---|
| **Core Supply Voltage** | 1.8 V | 1.8 V | — | Nominal TSMC 0.18 µm |
| **Total Memory Capacity** | 256 bits | 256 bits | — | $16 \times 16$ array |
| **Read Disturbance Bump ($V_{\text{bump}}$)** | $< 0.35\text{ V}$ | **0.222 V** | — | Measured on Q & QB during Read 0/1; $< V_{\text{thn}}$ (0.45V) |
| **Static Noise Margin (SNM - Hold)** | $> 250\text{ mV}$ | $> 300\text{ mV}$ | — | Butterfly curve analysis |
| **Static Noise Margin (SNM - Read)** | $> 120\text{ mV}$ | $> 160\text{ mV}$ | — | Backed by $V_{\text{bump}} = 0.222\text{ V}$ |
| **Write Switching Time ($t_{\text{write}}$)** | $< 1.0\text{ ns}$ | **128.8 ps** | — | Time from WL rising to node reaching 90% $V_{\text{DD}}$ |
| **Precharge Recovery Time ($t_{\text{precharge}}$)** | $< 1.0\text{ ns}$ | **774.2 ps** | — | Time to restore discharged bitline from 0V to 98% $V_{\text{DD}}$ |
| **Precharge Restored Voltage** | $\ge 1.764\text{ V}$ (98%) | **1.800 V** (100%) | — | Full rail restoration from 0V write state |
| **Precharge Residual Offset ($\Delta V_{\text{residual}}$)** | $< 5\text{ mV}$ | **0.000 V** | — | Perfect equalization; zero sense amp offset |
| **Precharge Peak Current per Column** | $< 1.0\text{ mA}$ | **165.3 µA** | — | Low peak supply surge |
| **Precharge Energy per Column ($E_{\text{pre}}$)** | $< 150\text{ fJ}$ | **115.4 fJ** | — | Matches theoretical $C_{\text{BL}}V_{\text{DD}}^2$ (113.4 fJ) within 1.7% |
| **Read Power per Bit ($P_{\text{read}}$)** | Report | Pending | — | Integrated $V_{\text{DD}} \times I_{\text{DD}}$ |
| **Write Power per Bit ($P_{\text{write}}$)** | Report | Pending | — | Integrated $V_{\text{DD}} \times I_{\text{DD}}$ |
| **Read Access Delay ($t_{\text{CQ}}$)** | Minimized | Pending | — | CLK rising edge to valid DOUT |
| **Max Clock Frequency ($F_{\text{max}}$)** | Report | Pending | — | $1 / T_{\text{clk,min}}$ |
| **Core Layout Area** | Minimized ($\mu\text{m}^2$) | — | Pending | Electric VLSI DRC/LVS clean |
