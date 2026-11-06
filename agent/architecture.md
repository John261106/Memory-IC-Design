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
- **Scalable Rules Basis:** $\lambda = 90\text{ nm}, 180\text{ nm} = 2\lambda$. All lengths $L = 2\lambda = 0.18\ \mu\text{m}$.
- **Transistor Sizing:**
  - **Pull-Up PMOS ($M_{\text{PU\_BIT}}, M_{\text{PU\_BITB}}$):** $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (charges $C_{\text{BL}} \approx 35\text{ fF}$ to $98\% V_{\text{DD}}$ in $< 0.8\text{ ns}$).
  - **Equalization PMOS ($M_{\text{EQ}}$):** $W = 3\lambda = 0.27\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (equalizes residual $\Delta V < 2\text{ mV}$).
- **Topology:** Three PMOS transistors active low (`PCB = 0`):
  - Two PMOS pull-ups charging `BIT` and `BITB` to $V_{\text{DD}}$.
  - One PMOS equalizer connected between `BIT` and `BITB` to eliminate offset before sensing.

### 2.3 Write Driver Unit
- **Scalable Rules Basis:** $\lambda = 90\text{ nm}, 180\text{ nm} = 2\lambda$. All lengths $L = 2\lambda = 0.18\ \mu\text{m}$.
- **Transistor Sizing:**
  - **Series Pull-Down NMOS (`Mnmos@0, 4, 5, 6`):** $W = 6\lambda = 0.54\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (low series resistance $< 1.5\ \text{k}\Omega$).
  - **Data Inverter:** NMOS (`Mnmos@7`) $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS (`Mpmos@2`) $W = 4\lambda = 0.36\ \mu\text{m}$ (balanced threshold, model `CMOSP`).
- **Topology:** Tri-state differential pull-down logic gated by `WRITE_EN` and input data `DATA`:
  - When `WRITE_EN = 1` and `DATA = 1`: pulls `BITB` to GND, leaves `BIT` high.
  - When `WRITE_EN = 1` and `DATA = 0`: pulls `BIT` to GND, leaves `BITB` high.
  - When `WRITE_EN = 0`: high impedance (Hi-Z) so read operations are not perturbed.
- **Performance:** Bitline discharge time $t_{\text{pulldown}} < 250\text{ ps}$ into $50\text{ fF}$; $V_{\text{OL}} < 0.05\text{ V}$.

### 2.4 Sense Amplifier Unit
- **Scalable Rules Basis:** $\lambda = 90\text{ nm}, 180\text{ nm} = 2\lambda$. All lengths $L = 2\lambda = 0.18\ \mu\text{m}$.
- **Transistor Sizing:**
  - **Tail Strobe NMOS (`Mnmos@5`):** $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (biases diff pair).
  - **Differential Input NMOS Pair (`Mnmos@3`, `Mnmos@4`):** $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (high $g_m$, zero DC bitline load).
  - **Active PMOS Current Mirror (`Mpmos@4`, `Mpmos@5`):** $W = 4\lambda = 0.36\ \mu\text{m}, L = 2\lambda = 0.18\ \mu\text{m}$ (high output impedance active load).
  - **Output Inverter Stage:** NMOS (`Mnmos@6`) $W = 2\lambda = 0.18\ \mu\text{m}$, PMOS (`Mpmos@6`) $W = 4\lambda = 0.36\ \mu\text{m}$ (full-rail digital output).
- **Topology:** 2-Stage Current-Mirror Operational Transconductance Amplifier (OTA) with inverter output buffer.
- **Performance:** Senses down to $\Delta V_{\text{min}} \le 50\text{--}100\text{ mV}$ with high CMRR, sensing delay $t_{\text{sense}} < 300\text{ ps}$, and zero DC bitline loading.

### 2.5 4-to-16 Row & Column Decoders
- **Row Decoder:** 4 address bits ($A[7:4]$) $\to$ 16 Wordline drivers (`WL[0:15]`). Static CMOS NAND/NOR structure with driving inverters/buffers sized to charge the parasitic gate capacitance of 16 bitcell access transistors.
- **Column Decoder / Multiplexer:** 4 address bits ($A[3:0]$) $\to$ 16 column transmission gates or NMOS pass-transistor pairs connecting the selected `BIT[k]` / `BITB[k]` to the global data lines.

### 2.6 Serial Address Generation Engine
Because only **1 external address pin (`ADDR_IN`)** is provided:
- **Option A (Serial Shift Register):** An 8-bit Serial-In Parallel-Out (SIPO) shift register clocked by `CLK`. Takes 8 clock cycles to shift in an 8-bit target address before issuing Read/Write.
- **Option B (Sequential Counter with Reset):** An 8-bit synchronous binary counter incrementing each clock cycle, with `ADDR_IN` serving as address reset / sync pulse or serial address increment strobe.
- **Output:** 8 parallel lines ($A[7:0]$) split into Row Address ($A[7:4]$) and Column Address ($A[3:0]$).

### 2.7 Master-Slave Transmission-Gate D Flip-Flop
- **Cell:** `D_flipflop`
- **Scalable Rules Basis:** $\lambda = 90\text{ nm}, L_{\text{min}} = 2\lambda = 0.18\ \mu\text{m}$.
- **Transistor Sizing:**
  - **Clock Inverters (`Mnmos@8/9, Mpmos@8/9`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ (balanced $\tau_p \approx \tau_n$, sharp transitions).
  - **Master Input & Interstage TGs (`Mnmos@0/7, Mpmos@0/7`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ (low $R_{\text{on}}$, rapid state transfer).
  - **Master Forward Inverter (`Mnmos@2, Mpmos@2`):** $W_{\text{N}} = 4\lambda = 0.36\ \mu\text{m}, W_{\text{P}} = 8\lambda = 0.72\ \mu\text{m}$ ($V_M \approx 0.9\text{ V}$, centered noise margin).
  - **Keeper Inverters (`Mnmos@3/6, Mpmos@3/6`):** $W_{\text{N}} = 2\lambda = 0.18\ \mu\text{m}, W_{\text{P}} = 4\lambda = 0.36\ \mu\text{m}$ (weak keeper, eliminates write contention).
  - **Keeper TGs (`Mnmos@1/4, Mpmos@1/4`):** $W_{\text{N}} = 3\lambda = 0.27\ \mu\text{m}, W_{\text{P}} = 6\lambda = 0.54\ \mu\text{m}$.
  - **Slave Output Driver (`Mnmos@5, Mpmos@5`):** $W_{\text{N}} = 6\lambda = 0.54\ \mu\text{m}, W_{\text{P}} = 12\lambda = 1.08\ \mu\text{m}$ (strong output drive into downstream shift-register loads).
- **Performance:** $t_{\text{clk}\to Q\text{, rise}} = 227.2\text{ ps}, t_{\text{clk}\to Q\text{, fall}} = 207.8\text{ ps}$; dynamic energy $E_{\text{cycle}} = 190.2\text{ fJ}$; robust static retention down to DC.

### 2.8 3-Bit Synchronous Binary Counter
- **Cell:** `3Bit_counter`
- **Topology:** Modulo-8 synchronous counter using 3 TG-MS D-flip-flops and transistor-level combinational gates.
- **Hazard-Free Terminal Count:** Direct path-balanced 3-input NAND + strong INV replaces cascaded gates to eliminate 011 -> 100 skew spikes (hazard glitch reduced from 251.2 mV to 0.99 mV).
- **Performance:** $t_{\text{clk}\to \text{COUNT\_7, rise}} = 338.2\text{ ps}, t_{\text{clk}\to \text{COUNT\_7, fall}} = 275.8\text{ ps}$; frame energy $1.962\text{ pJ}$ @ 100 MHz.

### 2.9 Central Multi-Strobe Timing Generator
- **Cell:** `Control_logic`
- **Inputs:** `CLK`, `CTRL` (1=Read, 0=Write), `COUNT_7`, `VDD`, `GND`.
- **Outputs:** `PCB` (precharge bar), `WL_EN` (wordline strobe), `WRITE_EN`, `READ_EN`.
- **Transistor Sizing:** Built with transistor-level CMOS gates ($W_n = 4\lambda, W_p = 8\lambda$ internal, $W_n = 6\lambda = 0.54\ \mu\text{m}, W_p = 12\lambda = 1.08\ \mu\text{m}$ output buffers).
- **Sense Amp Delay Line:** Incorporates an 8-stage CMOS inverter delay line on the `READ_EN` strobe path ($\sim 280\text{ ps}$ delay) to allow bitline differential voltage ($\Delta V > 500\text{ mV}$) to develop before sense amp activation, eliminating the $0.7\text{ V}$ Read '0' transient spike on `DOUT` ($0.699\text{ V} \rightarrow 0.0186\text{ V}$, 97.3% reduction).
- **Performance:** $t_{\text{prop,write\_en}} = 149.9\text{ ps}, t_{\text{prop,read\_en}} = 428.2\text{ ps}$; full-chip $t_{\text{CQ,read1}} = 723.2\text{ ps}$.

### 2.10 Serial-In Parallel-Out Address Register & Shadow Latch
- **Cells:** `8Bit_shiftreg`, `8Bit_reg`
- **Architecture:** 8-stage SIPO shift register clocked continuously by master `CLK` captures serial bits from `ADDR_IN`. At Cycle 7 low phase, `Control_logic.CLK_SHADOW` pulses to transfer $Q[7:0]$ into `8Bit_reg`.
- **Pin Pitch-Matching:** `8Bit_shiftreg;2{ic}` outputs $Q[0:7]$ at $X=7, Y=[7, 5, 3, 1, -1, -3, -5, -7]$ directly align horizontally with `8Bit_reg;1{ic}` inputs $D[0:7]$ at $X=-8, Y=[7, 5, 3, 1, -1, -3, -5, -7]$ with zero wire crossing.
- **Performance:** $56.09\ \mu\text{W}$ average power; solid DC retention during shift ($V_{\text{OL}} \le 23\ \mu\text{V}$, $V_{\text{OH}} = 1.800\text{ V}$).

### 2.11 Static CMOS Wordline Driver
- **Cell:** `WL_driver`
- **Topology:** Static CMOS 2-input AND gate (NAND2 stage + high-drive inverter driver).
- **Transistor Sizing:**
  - NAND2 Stage: PMOS $W = 4\lambda = 0.36\ \mu\text{m}$, NMOS $W = 4\lambda = 0.36\ \mu\text{m}$, $L = 0.18\ \mu\text{m}$.
  - Driver Inverter: PMOS $W = 8\lambda = 0.72\ \mu\text{m}$, NMOS $W = 4\lambda = 0.36\ \mu\text{m}$, $L = 0.18\ \mu\text{m}$.
- **Performance:** $t_{\text{rise}} = 288.9\text{ ps}, t_{\text{fall}} = 256.8\text{ ps}$ into full 50 fF wordline load; $V_{\text{OL}} \le 45\text{ nV}$ when unselected.

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
