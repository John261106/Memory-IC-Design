# Status, Milestones & Task Checklist

## 1. Current Project Status
- **Core 6T Bitcell:** Complete (`6T_cell{sch}`, verified in SPICE).
- **Precharge Circuit:** Complete (`Precharge_ckt{sch}`, verified in SPICE).
- **Sense Amplifier:** Complete (`Sense_amp{sch}`, verified in SPICE).
- **Write Driver:** Complete (`Write_driver{sch}`, verified in SPICE).
- **D Flip-Flop:** Complete (`D_flipflop{sch}` sized and verified; testbench in `D_flipflop_test.spi` confirms 2-stage shift register cascading with sub-230ps delay).
- **8-Bit Shift Register:** Complete (`8Bit_shiftreg{sch}` & `{ic}` in `.jelib` exporting parallel outputs `Q0..Q7` directly to `CA0..CA3` and `RA0..RA3`; shadow register `8Bit_reg` eliminated per 8-cycle inverted-phase architecture).
- **3-Bit Synchronous Counter:** Complete (`3Bit_counter{sch}` built in `.jelib` with custom transistor-level logic and net-name routing; verified in `3Bit_counter_test.spi`).
- **Control Logic Unit:** Complete (`Control_logic{sch}` & `{ic}` updated in `.jelib` for 8-cycle inverted-phase operation: $\text{PCB}=\overline{\text{CLK}}$, $\text{WL\_EN}=\text{COUNT\_7}\cdot\overline{\text{CLK}}$, $\text{WRITE\_EN}=\overline{\text{CTRL}}\cdot\text{WL\_EN}$, $\text{READ\_EN}=\text{CTRL}\cdot\text{WL\_EN}$ with an 8-stage CMOS inverter delay line to eliminate Read '0' $0.7\text{ V}$ sense amp glitch; verified in `Top_test.spi` at $18.6\text{ mV}$ peak).
- **Wordline Driver (`WL_driver`):** Complete (`WL_driver{sch}` & `{ic}` built in `.jelib`; verified in SPICE with $t_{\text{rise}} = 288.9\text{ ps}$ into full 50 fF wordline load and $V_{\text{OL}} \le 45\text{ nV}$).
- **Top-Level 256-Bit SRAM Chip (`Top`):** Complete (`Top{sch}` & `Top{ic}` updated in `.jelib` without `8Bit_reg` or `Precharg@16`; verified end-to-end in `spice/Top.spi` and `spice/Top_test.spi` at $P_{\text{chip,avg}} = 165.9\ \mu\text{W}$).
- **1-Bit SRAM Slice:** Complete & verified (`1Bit_SRAM.spi`).
- **16x16 Bitcell Matrix:** Schematic created (`256bit_array{sch}` / `256bit_SRAM.spi`).
- **4-to-16 Decoder:** Complete (`Decoder{sch}` & `{ic}` verified and integrated for both Row and Column decoding).
- **Living Design Report:** Updated (`docs/design_report.md` tracking Decision Logs 1–15 and full-chip characterization metrics).

---

## 2. Active Roadmap & Prioritized Checklist

### Phase 1: Address Decoding & Multiplexing
- [x] Create automated connection script for 4-to-16 static CMOS Address Decoder (`scripts/05_connect_decoder.py`).
- [x] Run decoder connection script inside Electric VLSI on `Decoder{sch}`.
- [x] Connect Row Decoder outputs to Wordlines `WL[0:15]` via gated `WL_driver` array.
- [x] Design Column Multiplexer with 16 CMOS transmission gates + local inverters connected to shared SA & WD.

### Phase 2: Serial Addressing & Clock Tree Network
- [x] Design, size, and verify Master-Slave Transmission-Gate D Flip-Flop (`D_flipflop.spi`, `D_flipflop_test.spi`).
- [x] Implement 8-bit Serial-In Parallel-Out (SIPO) shift register (`8Bit_shiftreg`), 8-bit shadow register (`8Bit_reg`), and 3-bit Modulo-8 counter (`3Bit_counter`) for single-pin `ADDR_IN`.
- [ ] Design balanced Clock Tree Network distributing `CLK` to decoders, registers, and sense amp strobes (deferred per user preference: no intermediate clock buffers for now).
- [x] Synthesize/integrate Control (`CTRL` R/W) logic timing generator (`Control_logic`).

### Phase 3: Packaging & I/O Pad Integration
- [ ] Create SPICE subcircuit / schematic block for Bond Wire + I/O Pad equivalent RLC network ($L_{\text{bond}} = 1.5\text{ nH}, R_{\text{bond}} = 0.1\,\Omega, C_{\text{pad}} = 0.8\text{ pF}$).
- [ ] Wrap all 5 external signals (`CLK`, `CTRL`, `ADDR_IN`, `DIN`, `DOUT`) and power supplies with the pad equivalent model.

### Phase 4: Physical Layout & Power Grid Routing
- [ ] Layout 6T bitcell with DRC / LVS cleanliness, minimizing cell area.
- [ ] Array layout: $16 \times 16$ symmetric pitch-matched placement.
- [ ] Layout peripheral blocks (decoders, precharge, sense amp, write driver, address register).
- [ ] Route `VDD` and `GND` power grid on Top Metal (Metal 5/6).
- [ ] Full-chip DRC and LVS signoff.

### Phase 5: Power & Frequency Characterization
- [x] Schematic-level full-chip transient verification (`spice/Top_test.spi`).
- [ ] Post-layout parasitic extraction (PEX) and simulation.
- [x] Measure read energy/power per bit ($E_{\text{read}} = 3.138\text{ pJ/bit}, P_{\text{read}} = 313.79\ \mu\text{W}$).
- [x] Measure write energy/power per bit ($E_{\text{write}} = 2.738\text{ pJ/bit}, P_{\text{write}} = 273.83\ \mu\text{W}$).
- [x] Measure critical path delay and calculate maximum clock frequency ($t_{\text{CQ}} = 370.3\text{ ps}$, $F_{\text{max}} > 500\text{ MHz}$).
