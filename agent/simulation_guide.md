# Simulation, Characterization & SPICE Guide

## 1. Simulation Setup & Models
- **SPICE Engine:** LTspice XVII/24 or ngspice.
- **Transistor Models:** TSMC 0.18 µm (`lib/tsmc018.lib`), Level 49 (BSIM3v3):
  - NMOS model: `CMOSN`
  - PMOS model: `CMOSP`
- **Supply Voltage:** $V_{\text{DD}} = 1.8\text{ V}$, $\text{GND} = 0.0\text{ V}$.
- **Temperature:** Nominal 27 °C ($300\text{ K}$).

---

## 2. Characterization Procedures

### 2.1 Read & Write Power Consumption Calculation
Average power and energy consumption must be evaluated for reading and writing each bit:

1. **Instantaneous Power:**
   $$P(t) = V_{\text{DD}} \times I_{\text{VDD}}(t)$$
2. **Energy per Bit Operation:**
   $$E_{\text{operation}} = \int_{t_{\text{start}}}^{t_{\text{stop}}} V_{\text{DD}} \times I_{\text{VDD}}(t) \, dt$$
   In SPICE testbenches, compute using `.MEAS`:
   ```spice
   .MEAS TRAN E_read INTEG V(VDD)*I(VDDsrc) FROM=t_read_start TO=t_read_stop
   .MEAS TRAN P_read_avg AVG V(VDD)*I(VDDsrc) FROM=t_read_start TO=t_read_stop
   .MEAS TRAN E_write INTEG V(VDD)*I(VDDsrc) FROM=t_write_start TO=t_write_stop
   .MEAS TRAN P_write_avg AVG V(VDD)*I(VDDsrc) FROM=t_write_start TO=t_write_stop
   ```

---

### 2.2 Maximum Clock Frequency ($F_{\text{max}}$) Determination
Determine the maximum frequency by identifying the longest delay path (critical path):
1. **Critical Path in Read Cycle:**
   $$t_{\text{read\_path}} = t_{\text{setup\_addr}} + t_{\text{row\_decoder}} + t_{\text{WL\_charge}} + t_{\text{BL\_discharge}} + t_{\text{sense\_amp}} + t_{\text{output\_pad}}$$
2. **Precharge Constraint:**
   $$t_{\text{precharge}} \text{ must restore } V(\text{BIT}) \text{ and } V(\text{BITB}) \ge 0.98 \times V_{\text{DD}}$$
3. **Calculation:**
   $$T_{\text{clk,min}} \ge t_{\text{precharge}} + t_{\text{read\_path}}$$
   $$F_{\text{max}} = \frac{1}{T_{\text{clk,min}}}$$

---

### 2.3 Packaging Parasitic (Bond Wire + Pad) Subcircuit
To model the bond wire and I/O pad circuit on each external pin, include this SPICE subcircuit:

```spice
* ========================================================
* Bond Wire + Pad Equivalent Circuit Subcircuit
* ========================================================
.SUBCKT IO_PAD_BOND PIN_EXT PIN_CORE GND
L_bond PIN_EXT N_mid 1.5n
R_bond N_mid   PIN_CORE 0.1
C_pad  PIN_CORE GND 0.8p
.ENDS IO_PAD_BOND
```
All 5 external signals (`CLK`, `CTRL`, `ADDR_IN`, `DIN`, `DOUT`) and power supplies connect through instances of `IO_PAD_BOND`.

---

## 3. SPICE Simulation Deck Conventions
- Always declare ground node as `0` or `GND`.
- Set transient maximum timestep: `.TRAN 10p 100n` to ensure numerical convergence during fast sense amplifier latching.
- Use explicit initial conditions `.IC V(Q)=1.8 V(QB)=0` when testing cell stability.
