# Specifications Reference (Token-Dense)

## 1. High-Level Summary
- **Function:** 256-Bit Static RAM ($16 \times 16$ 2D memory array, 1-bit word width).
- **Process Technology:** TSMC 0.18 µm CMOS (`tsmc018.lib`, generic MOSIS mocmos).
- **Supply Voltage ($V_{\text{DD}}$):** 1.8 V nominal (GND = 0.0 V).
- **Design Tools:** Electric VLSI 9.08 + SPICE (LTspice / ngspice / UC SPICE).

## 2. External Interface (Strictly 5 External Signal Pins)

| Pin Name | Type | Direction | Description |
|---|---|---|---|
| `CTRL` / `R_W` | Digital | Input | High = Read operation, Low = Write operation (or active-low write enable). |
| `ADDR_IN` | Digital | Input | 1-bit serial address input to access 256 memory locations via sequential/shift mechanism. |
| `CLK` | Digital | Input | Synchronizes memory cycles, address loading, precharge, and data latching. |
| `DIN` | Digital | Input | 1-bit write data input. |
| `DOUT` | Digital | Output | 1-bit read data output from selected bit cell. |
| `VDD` | Power | Supply | 1.8 V core supply. |
| `GND` | Power | Ground | 0.0 V ground reference. |

## 3. Structural Constraints & Blocks
1. **Array:** 16 rows × 16 columns (256 6T SRAM cells).
2. **Row Decoder:** 4-to-16 static decoder driving Word Lines `WL[0:15]`.
3. **Column Decoder / MUX:** 4-to-16 column multiplexer selecting 1 of 16 bitline pairs (`BIT[0:15]`, `BITB[0:15]`).
4. **Addressing Engine:** 8-bit Serial-In Parallel-Out (SIPO) shift register or synchronous 8-bit counter ($2^8 = 256$ addresses: 4 bits Row + 4 bits Column).
5. **Read Circuit:** Precharge circuitry (pulls `BIT`/`BITB` to $V_{\text{DD}}$) + differential latch sense amplifier + output buffer.
6. **Write Circuit:** Differential tri-state write driver pulling selected `BIT` or `BITB` to GND.
7. **Clock Tree:** Balanced distribution network ensuring minimal clock skew across peripheral blocks and registers.
8. **Power Grid:** Top metal layer (Metal 5/6) for low-resistance $V_{\text{DD}}$ and GND distribution.
9. **I/O Packaging Model:** Bond wire + I/O pad equivalent circuit on every external pin.

## 4. Packaging Parasitics Model (Bond Wire + Pad + Board)
- **Model Topology:** 2-stage lumped RLC ladder per pin (`Top_package`).
- **Bond wire inductance:** $L_{\text{tot}} = 4.5\text{ nH}$ ($L_1 = 2.5\text{ nH}, L_0 = 2.0\text{ nH}$).
- **Bond wire resistance:** $R_{\text{tot}} = 0.25\ \Omega$ ($R_1 = 0.10\,\Omega, R_0 = 0.15\,\Omega$).
- **Pad capacitance:** $C_{\text{pad}} = 1.9\text{ pF}$ ($C_1 = 0.7\text{ pF}, C_0 = 1.2\text{ pF}$).
- **Series source termination:** $R_{\text{ser}} = 50\ \Omega$ on all 4 external input sources (`VCLK`, `VADDR`, `VCTRL`, `VDIN`).
- **Output load:** $C_{\text{dout}} = 20\text{ fF}$ on `DOUT_PCB`.
- **I/O Buffering:** Multi-stage `input_buffer` on inputs; size-32 fingered `output_buffer` on `DOUT`.

## 5. Measured Performance & Characterization Results (Packaged IC)
Extracted from end-to-end simulation in LTspice XVII (`spice/Top_package_test.spi` @ 100 MHz, $V_{\text{DD}} = 1.8\text{ V}$):
- **Core Layout Footprint:** $1812.0\lambda \times 2552.5\lambda = 163.08\ \mu\text{m} \times 229.73\ \mu\text{m} = \mathbf{0.03746\text{ mm}^2}$ (`Top{lay}`).
- **Layout Cleanliness:** 100% Manhattan (0 diagonal arcs), **0 DRC errors/warnings**, **100% LVS match**.
- **Standby / Leakage Power:** **$23.86\ \mu\text{W}$** ($0 - 4.9\text{ ns}$ pre-clock).
- **Active Write Power / Energy (5 ns window):**
  - Write '1' ($80 - 85\text{ ns}$): $P = 187.43\ \mu\text{W}, E = 0.937\text{ pJ}$ (Cell 10, 5).
  - Write '0' ($160 - 165\text{ ns}$): $P = 176.09\ \mu\text{W}, E = 0.880\text{ pJ}$ (Cell 3, 12).
  - Average Active Write: **$181.76\ \mu\text{W}$** ($0.909\text{ pJ}$, $P_{\text{peak}} = 3.69\text{ mW}$).
- **Active Read Power / Energy (5 ns window):**
  - Read '1' ($240 - 245\text{ ns}$): $P = 201.59\ \mu\text{W}, E = 1.008\text{ pJ}$ (Cell 10, 5).
  - Read '0' ($320 - 325\text{ ns}$): $P = 294.56\ \mu\text{W}, E = 1.473\text{ pJ}$ (Cell 3, 12).
  - Average Active Read: **$248.08\ \mu\text{W}$** ($1.241\text{ pJ}$, $P_{\text{peak}} = 3.69\text{ mW}$).
- **Continuous Full-Chip Average Power:** **$203.85\ \mu\text{W}$** ($0.204\text{ mW}$ over 32 clock cycles, $5 - 325\text{ ns}$).
- **Total Energy (32 Cycles):** **$65.23\text{ pJ}$**.
- **Read Output Voltages:** $V_{\text{OH}} = \mathbf{1.802\text{ V}}$ (Frame 3 Read '1'); $V_{\text{OL}} = \mathbf{-0.005\text{ V}}$ (Frame 4 Read '0').
- **Write Switching Delays:** $t_{\text{write1}} = \mathbf{1.02\text{ ns}}$ ($t_{\text{abs}} = 61.02\text{ ns}$); $t_{\text{write0}} = \mathbf{1.02\text{ ns}}$ ($t_{\text{abs}} = 121.02\text{ ns}$).
- **Disturb Immunity:** Unselected half-selected cells maintained $\mathbf{1.7988\text{ V}}$ ($< 2\text{ mV}$ disturb).
- **Maximum Clock Frequency ($F_{\text{max}}$):** **$> 125\text{ MHz}$** (packaged IC) / **$> 400\text{ MHz}$** (core limit).
