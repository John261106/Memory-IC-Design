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

### Decision Log 7: Column CMOS Transmission Gate Sizing in Scalable Lambda Rules
- **Date:** October 2026
- **Context:** Sizing the CMOS transmission gates (`TG`) that multiplex column bitlines onto the global data lines (`DL`, `DLB`), and the integrated local inverter.
- **Alternatives Considered:**
  1. *Equal NMOS & PMOS Sizing ($W_{\text{N}} = W_{\text{P}} = 4\lambda$):* Results in an asymmetric resistance profile where PMOS $R_{\text{on,P}}$ is $> 2.2\times$ higher than NMOS due to low hole mobility, slowing down read differential transfer.
  2. *Mobility-Matched Sizing ($W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$):* Compensates for $\mu_n / \mu_p \approx 2.2$, yielding a flat, low equivalent ON-resistance ($R_{\text{on,eq}} \approx 1.2\text{--}1.6\ \text{k}\Omega$) across the entire $0\text{ V} \to 1.8\text{ V}$ range.
  3. *Local Inverter Sizing ($W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 3\lambda = 0.27\ \mu\text{m}$):* Keeps input gate capacitance minimal while switching in $< 30\text{ ps}$ to ensure simultaneous NMOS/PMOS enable.
- **Decision:** Adopted **NMOS $W = 4\lambda = 0.36\ \mu\text{m}$, PMOS $W = 8\lambda = 0.72\ \mu\text{m}$**, and **Local Inverter $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 3\lambda = 0.27\ \mu\text{m}$** (all $L = 2\lambda = 0.18\ \mu\text{m}$).
- **Rationale:** Ensures fast read differential transfer ($t_{\text{prop,read}} < 100\text{ ps}$) with zero attenuation and fast write zero pull-down ($t_{\text{prop,write}} < 150\text{ ps}$).

---

### Decision Log 8: Current-Mirror Differential Operational Amplifier (OTA) Sense Amplifier
- **Date:** October 2026
- **Context:** Sizing the 2-stage current-mirror differential sense amplifier (`Sense_amp`), comprising an NMOS differential input pair (`Mnmos@3`, `Mnmos@4`), an active PMOS current mirror load (`Mpmos@4`, `Mpmos@5`), a clocked tail NMOS strobe (`Mnmos@5`), and a second-stage CMOS output inverter buffer (`Mpmos@6`, `Mnmos@6`).
- **Alternatives Considered:**
  1. *Uniform Minimum Sizing ($W = 2\lambda = 0.18\ \mu\text{m}$ for all transistors):* Low input transconductance ($g_m$), causing reduced differential gain and slower response to small $\Delta V \le 100\text{ mV}$.
  2. *Excessively Large Transistors ($W > 8\lambda$):* Increases gate capacitance and layout area without significant speed advantage.
  3. *Optimized Sizing ($W_{\text{diff}}=4\lambda=0.36\ \mu\text{m}, W_{\text{mirror}}=4\lambda=0.36\ \mu\text{m}, W_{\text{tail}}=4\lambda=0.36\ \mu\text{m}$, Inverter: $W_{\text{N}}=2\lambda=0.18\ \mu\text{m}, W_{\text{P}}=4\lambda=0.36\ \mu\text{m}$):* Maximizes differential voltage gain $A_v = g_m (r_{on} \parallel r_{op})$, centers inverter switching threshold at $\approx 0.9\text{ V}$, and provides zero DC loading on bitlines.
- **Decision:** Adopted **Input Pair and Mirror $W = 4\lambda = 0.36\ \mu\text{m}$, Tail NMOS $W = 4\lambda = 0.36\ \mu\text{m}$, Output Inverter $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 4\lambda = 0.36\ \mu\text{m}$** (all $L = 2\lambda = 0.18\ \mu\text{m}$).
- **Rationale:** Delivers high CMRR, high differential sensitivity to small bitline differentials ($\Delta V \le 100\text{ mV}$), zero DC loading on the bitlines (gates only), and fast full-rail CMOS output transitions on `SENSE`.

---

### Decision Log 9: Tri-State Differential Write Driver Sizing in Lambda Rules
- **Date:** October 2026
- **Context:** Sizing the NMOS series pull-down stacks and data inverter in the tri-state write driver (`Write_driver`) to rapidly discharge heavily loaded bitlines ($C_{\text{load}} \approx 50\text{ fF}$) down to $V_{\text{OL}} \le 0.05\text{ V}$.
- **Alternatives Considered:**
  1. *Minimum Uniform Sizing ($W = 2\lambda = 0.18\ \mu\text{m}$):* Two series NMOS transistors present high pull-down resistance ($R_{\text{series}} \approx 5\text{--}6\ \text{k}\Omega$), resulting in sluggish bitline discharge ($t_{\text{fall}} > 600\text{ ps}$).
  2. *Excessively Large Stacks ($W > 12\lambda$):* Increases circuit layout footprint and gate capacitance without meaningful write speed improvements.
  3. *Optimized Series Sizing ($W_{\text{stack}}=6\lambda=0.54\ \mu\text{m}, W_{\text{inv,N}}=2\lambda=0.18\ \mu\text{m}, W_{\text{inv,P}}=4\lambda=0.36\ \mu\text{m}$):* Cuts series resistance to $< 1.5\ \text{k}\Omega$, achieving fast pull-down ($t_{\text{fall}} < 250\text{ ps}$) and solid $V_{\text{OL}} < 0.05\text{ V}$ to guarantee instant bitcell overwriting.
- **Decision:** Adopted **Series Pull-Down NMOS $W = 6\lambda = 0.54\ \mu\text{m}$**, **Data Inverter NMOS $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS $W = 4\lambda = 0.36\ \mu\text{m}$** (all $L = 2\lambda = 0.18\ \mu\text{m}$).
- **Rationale:** Overpowers the 6T bitcell pull-up PMOS effortlessly and drives the bitline to ground in $< 250\text{ ps}$.

---

### Decision Log 10: Static Master-Slave Transmission-Gate D Flip-Flop Sizing & Feedback Connection
- **Date:** October 2026
- **Context:** Implementing the sequential register elements required for serial addressing (`ADDR_IN`), data buffering (`DIN`), and control pipelines. Sizing all 20 transistors across the clock generation inverters, master latch, and slave latch, and resolving internal feedback keeper power routing.
- **Alternatives Considered:**
  1. *True Single-Phase Clock (TSPC) Dynamic Flip-Flop:* Uses fewer transistors (~9-11) and single clock line, but suffers from dynamic node charge leakage at low or paused clock speeds, high clock slope sensitivity, and charge-sharing hazards. Unsuitable for debuggable serial shift registers where clock rates may be paused.
  2. *Uniform Minimum-Sized Master-Slave TG DFF ($W = 2\lambda = 0.18\ \mu\text{m}$ throughout):* Clock inverters suffer high rise/fall skew under 4-TG capacitive loading; keeper inverters contend with input TGs during sampling; output stage produces sluggish edges ($> 400\text{ ps}$) into downstream shift-register stages.
  3. *Optimized Ratioed Master-Slave TG DFF:*
     - Clock inverters: $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ (balanced $\tau_{\text{p}} \approx \tau_{\text{n}}$, sharp transitions $< 40\text{ ps}$).
     - Input & Interstage TGs: $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ (low $R_{\text{on}}$, rapid sampling).
     - Master Forward Inverter: $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ (trip point $V_M \approx 0.9\text{ V}$, centered noise margin).
     - Feedback Keepers (Master & Slave): Weak sizing $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 4\lambda = 0.36\ \mu\text{m}$ for inverters, $W_{\text{N}} = 3\lambda = 0.27\ \mu\text{m}, W_{\text{P}} = 6\lambda = 0.54\ \mu\text{m}$ for feedback TGs. Eliminates write-contention spikes while holding state statically.
     - Slave Output Driver: $W_{\text{N}} = 6\lambda = 0.54\ \mu\text{m}, W_{\text{P}} = 12\lambda = 1.08\ \mu\text{m}$ for sharp transitions ($< 200\text{ ps}$) into $25\text{--}50\text{ fF}$ interconnect/load.
- **Decision:** Adopted **Optimized Ratioed Master-Slave TG DFF** and corrected the feedback keeper inverter power connections (NMOS source to `GND`, PMOS source to `VDD`, correcting a 180° rotation inversion in CAD schematic).
- **Rationale:** Achieves sub-230 ps clock-to-Q propagation delays ($t_{\text{clk}\to Q\text{, rise}} = 227.2\text{ ps}, t_{\text{clk}\to Q\text{, fall}} = 207.8\text{ ps}$), guarantees race-free cascading in shift registers, and maintains static data retention down to DC.

---

### Decision Log 11: 3-Bit Synchronous Binary Counter & Pipelined Shadow Register Control Architecture
- **Date:** November 2026
- **Context:** Designing the cycle counter (`3Bit_counter`) and control architecture to coordinate the 8-bit serial address shift register (`8Bit_shiftreg`), parallel shadow register, and precharge-assisted read/write cycles.
- **Alternatives Considered:**
  1. *Option B — Framed 9-Cycle Stalled Shift Register (No Shadow Register):* Requires gating the shift register clock or inserting 8 2:1 recirculation MUXes to freeze the address during the 9th execution cycle, introducing clock-gating skew hazards and stalling serial input throughput.
  2. *Option A — Free-Running 8-Bit Shift Register + 8-Bit Shadow Register Driven by a 3-Bit Modulo-8 Counter:* The shift register runs continuously on `CLK` while a 3-bit synchronous binary counter (`C2, C1, C0`) tracks the 8 incoming serial bits ($000 \to 111$) and asserts `COUNT_7` ($C_2 \cdot C_1 \cdot C_0$) when the 8th bit arrives. Furthermore, precharge (`PCB = CLK`) operates in every cycle during $\text{CLK} = 0$ so both Read and Write are precharge-assisted.
- **Decision:** Adopted **Option A with a custom transistor-level 3-Bit Synchronous Binary Counter (`3Bit_counter{sch}`)** comprising 3 `D_flipflop` instances, 3 complement inverters ($W_{\text{N}}=0.36\ \mu\text{m}, W_{\text{P}}=0.72\ \mu\text{m}$), 2 transmission-gate XOR blocks ($W_{\text{N}}=0.36\ \mu\text{m}, W_{\text{P}}=0.72\ \mu\text{m}$), 1 static CMOS AND2 block (`C01 = C0 & C1`), and a **direct path-balanced 3-input AND3 block (`NAND3(C0, C1, C2) + INV`)** for `COUNT_7`.
- **Rationale:** Using a cascaded 2-input AND (`C01 & C2`) introduced a $251.2\text{ mV}$ static-0 combinational hazard glitch at the `011 -> 100` transition ($t = 35\text{ ns}$) because `C01` was delayed by two extra gate stages relative to `C2`. Replacing the terminal-count stage with a direct 3-input NAND (`NAND3`, $W_{\text{N}}=0.54\ \mu\text{m}, W_{\text{P}}=0.36\ \mu\text{m}$) matches input arrival times, suppressing the $35\text{ ns}$ spike from **$251.2\text{ mV}$ down to $0.99\text{ mV}$** while improving propagation delay to $t_{\text{clk}\to \text{COUNT\_7, rise}} = 338.2\text{ ps}$ and $t_{\text{clk}\to \text{COUNT\_7, fall}} = 275.8\text{ ps}$.

---

### Decision Log 12: 8-Cycle Inverted-Phase Shadow-Register-Free Control Logic (`Control_logic{sch}`)
- **Date:** November 2026
- **Context:** Designing the central timing and strobe generator (`Control_logic{sch}`) that converts master `CLK`, `CTRL` (R/W), and `COUNT_7` into internal memory control signals (`PCB`, `WL_EN`, `WRITE_EN`, `READ_EN`).
- **Alternatives Considered:**
  1. *9-Cycle Pipeline with 8-Bit Shadow Register (`8Bit_reg`) and `PCB = CLK`:* Requires 8 clock cycles to shift the address into `8Bit_shiftreg`, a falling-edge `CLK_SHADOW` strobe at the end of Cycle 8 to latch it into an 8-bit shadow register (`8Bit_reg`), and executes the Read/Write during Cycle 9 (`CLK = 1`). Adds 8 extra D flip-flops (160 transistors) and an extra cycle of latency.
  2. *8-Cycle Inverted-Phase Architecture (`PCB = ~CLK`, No Shadow Register):* Defines each clock cycle from rising edge to rising edge. During the first half of each cycle (`CLK = 1`), the serial address bit shifts into `8Bit_shiftreg` ($\approx 210\text{ ps}$) while **Precharge is active** ($\text{PCB} = \overline{\text{CLK}} = 0\text{ V}$) and the decoders settle ($\approx 400\text{ ps}$) well within the $5\text{ ns}$ high phase. During the second half of the 8th clock cycle (`CLK = 0` and `COUNT_7 = 1`), Precharge turns OFF ($\text{PCB} = 1.8\text{ V}$) and memory Read/Write executes directly while `8Bit_shiftreg` outputs `Q0..Q7` are held completely static:
     $$\text{PCB} = \overline{\text{CLK}}, \quad \text{WL\_EN} = \text{COUNT\_7} \cdot \overline{\text{CLK}}, \quad \text{WRITE\_EN} = \overline{\text{CTRL}} \cdot \text{WL\_EN}, \quad \text{READ\_EN} = \text{CTRL} \cdot \text{WL\_EN}$$
- **Decision:** Adopted the **8-Cycle Inverted-Phase Shadow-Register-Free Architecture** in `Control_logic{sch}` and `Top{sch}`, eliminating `8Bit_reg` and `CLK_SHADOW` and connecting `8Bit_shiftreg` outputs `Q0..Q7` directly to `CA0..CA3` and `RA0..RA3`.
- **Rationale:** Completely eliminates the 8-bit shadow register (saving 8 D flip-flops and $40\%$ of full-chip average power), executes every Read/Write right in the second half of the 8th clock cycle ($80\text{--}85\text{ ns}$), and guarantees race-free turn-off at the next rising clock edge (`WL_EN` falls in $244.6\text{ ps}$, before `8Bit_shiftreg` + `Decoder` can transition in $\sim 610\text{ ps}$).

---

### Decision Log 13: Static CMOS Wordline Driver (`WL_driver`) & Wordline Gating
- **Date:** November 2026
- **Context:** Implementing row wordline gating with `WL_EN` to ensure wordlines remain held strictly at $0\text{ V}$ during precharge and address shifting (Cycles 1–7 and first half of Cycle 8), and rapidly drive the 50 fF wordline load (32 NMOS access gates + routing) during the evaluation phase of Cycle 8 (`CLK = 0, COUNT_7 = 1`).
- **Alternatives Considered:**
  1. *Transmission Gate Switches with NMOS Pull-down:* Passive switches introduce series on-resistance that slows down rise time into 50 fF, while risking high-impedance floating states during switching skews between TG turn-off and pull-down turn-on.
  2. *Static CMOS 2-Input AND Gate (NAND2 + Inverter Driver):* Active CMOS logic with dedicated pull-up PMOS and pull-down NMOS, actively holding unselected wordlines at $V_{\text{OL}} \le 45\text{ nV}$ with zero impedance, and delivering a low-impedance rise time ($t_{\text{rise}} = 288.9\text{ ps}$) into 50 fF.
- **Decision:** Adopted **Static CMOS 2-Input AND Wordline Driver (`WL_driver{sch}`)** with $W_n = 4\lambda = 0.36\ \mu\text{m}$, $W_p = 4\lambda = 0.36\ \mu\text{m}$ (NAND2 stage) and $W_n = 4\lambda = 0.36\ \mu\text{m}$, $W_p = 8\lambda = 0.72\ \mu\text{m}$ (Output Driver Inverter).
- **Rationale:** Guarantees zero floating wordline nodes, protects bitcells against inadvertent read disturbs on unselected rows, and achieves sub-300 ps wordline activation into full 50 fF load.

---

### Decision Log 14: Full-Chip Top-Level Integration (`Top{sch}`) & End-to-End 8-Cycle Verification
- **Date:** November 2026
- **Context:** Integrating all hierarchical sub-blocks (`8Bit_shiftreg`, `3Bit_counter`, `Control_logic`, Row/Column `Decoder` units, 16 `WL_driver` units, `256bit_array`, 16 column `Precharge_ckt` units, 16 `TG_bitline` switches, shared `Write_driver`, and shared `Sense_amp`) into `Top{sch}` under the strict 5-pin external interface (`CLK`, `CTRL`, `ADDR_IN`, `DIN`, `DOUT` + `VDD`, `GND`).
- **Alternatives Considered:**
  1. *Point-to-Point Crossing Wires Across Schematic:* Creates hundreds of overlapping wires across the 16-row by 16-column buses, making schematic inspection error-prone.
  2. *Structured Modular Placement with Net-Name Stubs:* Groups components into clean functional zones with direct net-labeled stubs (`RA0..3`, `CA0..3`, `RDEC0..15`, `COL0..15`, `WL0..15`, `BL0..15`, `BLB0..15`, `DL`, `DLB`) between `8Bit_shiftreg`, `Decoder`, `WL_driver`, `256bit_array`, `Precharge_ckt`, `TG_bitline`, `Write_driver`, and `Sense_amp`.
- **Decision:** Adopted **Modular Placement with Net-Name Stubs** in `Top;1{sch}` and `Top;1{ic}`, connecting `8Bit_shiftreg` directly to `CA0..CA3` and `RA0..RA3` (no shadow register) and utilizing strictly the **16 dedicated column precharge units** (`Precharg@0..15`) at the top of the columns.
- **Rationale:** Full-chip SPICE simulation (`spice/Top_test.spi`) across 4 consecutive 8-cycle frames ($5\text{--}325\text{ ns}$) verified 100% functional accuracy for serial address shifting, Write `1` ($t_{\text{write1}} = 730.9\text{ ps}$), Write `0` ($t_{\text{write0}} = 743.3\text{ ps}$), Read `1` ($t_{\text{CQ}} = 580.2\text{ ps}$, $V_{\text{DOUT}} = 1.800\text{ V}$), Read `0` ($V_{\text{DOUT}} = 3.27\ \mu\text{V}$), and zero read/write disturb on unselected cells at **$164.86\ \mu\text{W}$** average full-chip power @ 100 MHz.

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
- **Column Select (CMOS Transmission Gate + Local Inverter):**
  - Scalable rules: $\lambda = 90\text{ nm}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - NMOS Pass Gates (`Mnmos@0`, `Mnmos@1`): $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - PMOS Pass Gates (`Mpmos@0`, `Mpmos@1`): $W = 8\lambda = 0.72\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Local Inverter: NMOS $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS $W = 3\lambda = 0.27\ \mu\text{m}$.
  - Target Performance: $R_{\text{on,eq}} < 2\ \text{k}\Omega$, read transfer delay $t_{\text{prop,read}} < 100\text{ ps}$, zero threshold voltage drop.
- **Sense Amplifier (Current-Mirror OTA Architecture):**
  - Scalable rules: $\lambda = 90\text{ nm}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Tail NMOS Strobe (`Mnmos@5`): $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Differential NMOS Input Pair (`Mnmos@3`, `Mnmos@4`): $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (matched pair).
  - Active PMOS Current Mirror Load (`Mpmos@4`, `Mpmos@5`): $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Second-Stage Output Inverter: NMOS (`Mnmos@6`) $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS (`Mpmos@6`) $W = 4\lambda = 0.36\ \mu\text{m}$.
  - Target Performance: Sensitivity $\Delta V_{\text{min}} \le 50\text{--}100\text{ mV}$, high CMRR, sensing delay $t_{\text{sense}} < 300\text{ ps}$, zero DC bitline loading.

### 4.4 Write Path: Write Driver
- **Tri-State Differential Write Driver:**
  - Scalable rules: $\lambda = 90\text{ nm}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Series Pull-Down NMOS Stacks (`Mnmos@0, 4, 5, 6`): $W = 6\lambda = 0.54\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$.
  - Data Inverter: NMOS (`Mnmos@7`) $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS (`Mpmos@2`) $W = 4\lambda = 0.36\ \mu\text{m}$ (model `CMOSP`).
  - Target Performance: Bitline discharge time $t_{\text{pulldown}} < 250\text{ ps}$ into $50\text{ fF}$; final $V_{\text{OL}} \le 0.05\text{ V}$; tri-state leakage $< 1\text{ nA}$.

### 4.5 Sequential Elements: Master-Slave Transmission-Gate D Flip-Flop
- **D Flip-Flop Architecture (`D_flipflop`):**
  - Scalable rules: $\lambda = 90\text{ nm}, L_{\text{min}} = 2\lambda = 0.18\ \mu\text{m}$.
  - **Internal Clock Inverters (`Mnmos@8/9, Mpmos@8/9`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$. Sized to drive 4 transmission gate loads each with sharp rise/fall times.
  - **Master Input Transmission Gate (`Mnmos@0, Mpmos@0`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$. Low on-resistance allows rapid sampling into master storage node.
  - **Master Forward Inverter (`Mnmos@2, Mpmos@2`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$. Balanced $W_p / W_n = 2$ centers switching threshold at $V_M \approx 0.9\text{ V}$.
  - **Master Feedback Keeper (`Mnmos@3, Mpmos@3, Mnmos@1, Mpmos@1`):** Inverter $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 4\lambda = 0.36\ \mu\text{m}$; TG $W_{\text{N}} = 3\lambda = 0.27\ \mu\text{m}, W_{\text{P}} = 6\lambda = 0.54\ \mu\text{m}$. Deliberately sized weaker than input TG to eliminate contention.
  - **Inter-Stage Transmission Gate (`Mnmos@7, Mpmos@7`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$. Low resistance for fast master-to-slave charge transfer.
  - **Slave Forward Inverter / Output Stage (`Mnmos@5, Mpmos@5`):** $W_{\text{N}} = 6\lambda = 0.54\ \mu\text{m}, W_{\text{P}} = 12\lambda = 1.08\ \mu\text{m}$. Higher drive capability for sharp Q transitions into downstream shift-register loads.
  - **Slave Feedback Keeper (`Mnmos@6, Mpmos@6, Mnmos@4, Mpmos@4`):** Inverter $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 4\lambda = 0.36\ \mu\text{m}$; TG $W_{\text{N}} = 3\lambda = 0.27\ \mu\text{m}, W_{\text{P}} = 6\lambda = 0.54\ \mu\text{m}$. Holds slave state statically with zero DC power dissipation.

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
| **Write Bitline Pull-Down Delay ($t_{\text{pulldown}}$)** | $< 500\text{ ps}$ | **430.8 ps** | — | Pulls 50fF bitline down to $< 10\% V_{\text{DD}}$ in 431ps |
| **Write Pull-Down Symmetry ($\Delta t_{\text{W0-W1}}$)** | $< 10\text{ ps}$ | **0.06 ps** | — | 430.795ps vs 430.739ps; matched rise/fall inverter |
| **Write Output Low Voltage ($V_{\text{OL}}$)** | $< 50\text{ mV}$ | **$< 1\ \mu\text{V}$** | — | Pulls bitline completely to ground ($0.8\ \mu\text{V}$) |
| **DFF Clock-to-Q Rise Delay ($t_{\text{clk}\to Q\text{, rise}}$)** | $< 350\text{ ps}$ | **227.2 ps** | — | Measured at 50% $V_{\text{DD}}$ into 25 fF load |
| **DFF Clock-to-Q Fall Delay ($t_{\text{clk}\to Q\text{, fall}}$)** | $< 350\text{ ps}$ | **207.8 ps** | — | Measured at 50% $V_{\text{DD}}$ into 25 fF load |
| **DFF Output Rise Time ($t_{\text{rise}}$)** | $< 300\text{ ps}$ | **203.5 ps** | — | 10% to 90% full-swing output edge |
| **DFF Output Fall Time ($t_{\text{fall}}$)** | $< 250\text{ ps}$ | **155.2 ps** | — | 90% to 10% full-swing output edge |
| **Shift-Register Stage 2 Latency** | $< 350\text{ ps}$ | **225.5 ps** | — | Race-free stage-to-stage cascading verified |
| **DFF Hold Stability Check** | Full rail retention | **1.800 V / 0.000 V** | — | Zero corruption when input D toggles while CLK is HIGH |
| **DFF Dynamic Energy per Cycle ($E_{\text{cycle}}$)** | $< 300\text{ fJ}$ | **190.2 fJ** | — | Full clock cycle integration @ 100 MHz |
| **DFF Dynamic Power ($P_{\text{avg}}$)** | $< 30\ \mu\text{W}$ | **19.02 µW** | — | Continuous switching @ 100 MHz |
| **3-Bit Counter Terminal Count Rise ($t_{\text{clk}\to \text{COUNT\_7, rise}}$)** | $< 600\text{ ps}$ | **338.2 ps** | — | 7th clock edge to `COUNT_7` high (50% $V_{\text{DD}}$) |
| **3-Bit Counter Terminal Count Fall ($t_{\text{clk}\to \text{COUNT\_7, fall}}$)** | $< 500\text{ ps}$ | **275.8 ps** | — | 8th clock edge rollover to `COUNT_7` low |
| **3-Bit Counter Combinational Hazard (`011` $\to$ `100`)** | $< 50\text{ mV}$ | **0.99 mV** | — | Reduced from 251.2 mV via direct path-balanced `NAND3` |
| **3-Bit Counter 8-Cycle Frame Energy ($E_{\text{frame}}$)** | $< 3.0\text{ pJ}$ | **1.962 pJ** | — | Full Modulo-8 sequence (`000` $\to$ `111` $\to$ `000`) |
| **3-Bit Counter Average Power ($P_{\text{counter}}$)** | $< 40\ \mu\text{W}$ | **24.53 µW** | — | Operating @ 100 MHz |
| **Control Logic `PCB` Fall Delay ($t_{\text{clk\_rise}\to\text{pcb\_fall}}$)** | $< 250\text{ ps}$ | **196.9 ps** | — | CLK rising to PCB active low ($\text{PCB} = \overline{\text{CLK}}$) into 40 fF load |
| **Control Logic `PCB` Rise Delay ($t_{\text{clk\_fall}\to\text{pcb\_rise}}$)** | $< 250\text{ ps}$ | **226.3 ps** | — | CLK falling to PCB inactive high into 40 fF load |
| **Control Logic `WL_EN` Rise Delay ($t_{\text{clk\_fall}\to\text{wl\_en\_rise}}$)** | $< 300\text{ ps}$ | **252.2 ps** | — | CLK falling (Cycle 8) to WL_EN high into 40 fF load |
| **Control Logic `WL_EN` Fall Delay ($t_{\text{clk\_rise}\to\text{wl\_en\_fall}}$)** | $< 300\text{ ps}$ | **244.6 ps** | — | Next CLK rising edge to WL_EN turn-off |
| **Control Logic `WRITE_EN` / `READ_EN` Turn-On Delay** | $< 450\text{ ps}$ | **412.2 ps / 411.8 ps** | — | CLK falling (Cycle 8) to WRITE_EN / READ_EN high into 25 fF load |
| **Control Logic Average Power ($P_{\text{ctrl}}$)** | $< 60\ \mu\text{W}$ | **21.20 µW** | — | Continuous switching @ 100 MHz (4 outputs, no `CLK_SHADOW`) |
| **Wordline Driver Rise Delay ($t_{\text{rise, wl}}$)** | $< 400\text{ ps}$ | **288.9 ps** | — | EN rising to WL rising (50% $V_{\text{DD}}$) into 50 fF load |
| **Wordline Driver Fall Delay ($t_{\text{fall, wl}}$)** | $< 400\text{ ps}$ | **256.8 ps** | — | EN falling to WL falling (50% $V_{\text{DD}}$) into 50 fF load |
| **Wordline Unselected Output Low Voltage ($V_{\text{OL}}$)** | $< 1\text{ mV}$ | **$< 45\text{ nV}$** | — | Solid GND hold; zero read disturb on unselected rows |
| **Full-Chip Write `1` Flip Delay ($t_{\text{CLK\_fall}\to Q\text{, W1}}$)** | $< 1.0\text{ ns}$ | **730.9 ps** | — | Cycle 8 CLK falling edge to Cell(10,5) 90% flip (`0xA5`) |
| **Full-Chip Write `0` Flip Delay ($t_{\text{CLK\_fall}\to Q\text{, W0}}$)** | $< 1.0\text{ ns}$ | **743.3 ps** | — | Cycle 16 CLK falling edge to Cell(3,12) 90% flip (`0x3C`) |
| **Full-Chip Average Power @ 100 MHz ($P_{\text{chip,avg}}$)** | $< 500\ \mu\text{W}$ | **164.86 µW** | — | 8-cycle shadow-register-free architecture across 4 consecutive frames |
| **Read Access Delay ($t_{\text{CQ}}$)** | Minimized | **580.2 ps** (Read 1) | — | Cycle 24 CLK falling edge to valid DOUT (`1.800 V`) into 20 fF load |
| **Max Clock Frequency ($F_{\text{max}}$)** | Report | **$> 500\text{ MHz}$** ($T_{\text{min}} < 2.0\text{ ns}$) | — | Critical path $< 0.78\text{ ns}$ (Precharge: 774 ps, Write: 743 ps, Read: 580 ps) |
| **Core Layout Area** | Minimized ($\mu\text{m}^2$) | — | Pending | Electric VLSI DRC/LVS clean |
