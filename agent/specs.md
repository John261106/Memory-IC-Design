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

## 4. Packaging Parasitics Model (Bond Wire + Pad)
- **Bond wire inductance:** $L_{\text{bond}} = 1.5\text{ nH}$ (typical 1.0–2.5 nH).
- **Bond wire resistance:** $R_{\text{bond}} = 0.1\ \Omega$.
- **Pad capacitance:** $C_{\text{pad}} = 0.8\text{ pF}$ (typical 0.5–1.2 pF).
- Circuit per pin: `Pad_in -> [R_bond in series with L_bond] -> [C_pad to GND] -> Internal_Core_Pin`.

## 5. Performance Targets & Characterization
- **Area:** Optimized minimum rectangular bounding box layout.
- **Power:** Measure dynamic + leakage power for:
  - Bit read operation ($E_{\text{read}}$ in fJ/bit).
  - Bit write operation ($E_{\text{write}}$ in fJ/bit).
- **Frequency ($F_{\text{max}}$):** Maximum clock frequency limited by:
  $$T_{\text{clk,min}} \ge t_{\text{setup}} + t_{\text{decode}} + t_{\text{WL}} + t_{\text{discharge}} + t_{\text{sense}} + t_{\text{hold}}$$
