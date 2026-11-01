# Status, Milestones & Task Checklist

## 1. Current Project Status
- **Core 6T Bitcell:** Complete (`6T_cell{sch}`, verified in SPICE).
- **Precharge Circuit:** Complete (`Precharge_ckt{sch}`, verified in SPICE).
- **Sense Amplifier:** Complete (`Sense_amp{sch}`, verified in SPICE).
- **Write Driver:** Complete (`Write_driver{sch}`, verified in SPICE).
- **D Flip-Flop:** Complete (`D_flipflop{sch}` sized and verified; testbench in `D_flipflop_test.spi` confirms 2-stage shift register cascading with sub-230ps delay).
- **8-Bit Shift Register:** Complete (`8Bit_shiftreg{sch}` & `{ic}` created in `.jelib`).
- **3-Bit Synchronous Counter:** Complete (`3Bit_counter{sch}` built in `.jelib` with custom transistor-level logic and net-name routing; verified in `3Bit_counter_test.spi`).
- **1-Bit SRAM Slice:** Complete & verified (`1Bit_SRAM.spi`).
- **16x16 Bitcell Matrix:** Schematic created (`256bit_SRAM.spi`, connected via Jython script `04_connect_sram_top.py`).
- **4-to-16 Decoder Script:** Complete (`scripts/05_connect_decoder.py`, automates 20 NOT + 16 NAND gates with active-high `OUT0..15`).
- **Living Design Report:** Initialized (`docs/design_report.md` tracking all architecture decisions and metrics).

---

## 2. Active Roadmap & Prioritized Checklist

### Phase 1: Address Decoding & Multiplexing
- [x] Create automated connection script for 4-to-16 static CMOS Address Decoder (`scripts/05_connect_decoder.py`).
- [ ] Run decoder connection script inside Electric VLSI on `Decoder{sch}`.
- [ ] Connect Row Decoder outputs to Wordlines `WL[0:15]`.
- [ ] Design Column Multiplexer with 16 CMOS transmission gates + local inverters connected to shared SA & WD.

### Phase 2: Serial Addressing & Clock Tree Network
- [x] Design, size, and verify Master-Slave Transmission-Gate D Flip-Flop (`D_flipflop.spi`, `D_flipflop_test.spi`).
- [ ] Implement 8-bit Serial-In Parallel-Out (SIPO) shift register / sequential counter for single-pin `ADDR_IN`.
- [ ] Design balanced Clock Tree Network distributing `CLK` to decoders, registers, and sense amp strobes.
- [ ] Synthesize/integrate Control (`CTRL` R/W) logic state machine.

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
- [ ] Schematic-level transient verification across all 256 memory locations.
- [ ] Post-layout parasitic extraction (PEX) and simulation.
- [ ] Measure read energy/power per bit ($E_{\text{read}}, P_{\text{read}}$).
- [ ] Measure write energy/power per bit ($E_{\text{write}}, P_{\text{write}}$).
- [ ] Measure critical path delay and calculate maximum clock frequency ($F_{\text{max}}$).
