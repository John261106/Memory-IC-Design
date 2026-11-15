# Status, Milestones & Task Checklist

## 1. Current Project Status
- **Core 6T Bitcell:** Complete (`6T_cell{sch}` verified in SPICE; `6T_cell{lay}` layout created with traditional 6T floorplan, 100% perpendicular/Manhattan lines, zero DRC collisions/violations, and verified 100% clean in NCC/LVS for topology, exports, and sizing).
- **Precharge Circuit:** Complete (`Precharge_ckt{sch}`, verified in SPICE).
- **Sense Amplifier:** Complete (`Sense_amp{sch}`, verified in SPICE).
- **Write Driver:** Complete (`Write_driver{sch}`, verified in SPICE).
- **D Flip-Flop:** Complete (`D_flipflop{sch}` sized and verified; testbench in `D_flipflop_test.spi` confirms 2-stage shift register cascading with sub-230ps delay).
- **8-Bit Parallel Register:** Complete (`8Bit_reg{sch}` & `8Bit_reg{lay}` in `.jelib`, 100% Manhattan, 0 DRC, 100% LVS match).
- **8-Bit Shift Register:** Complete (`8Bit_shiftreg{sch}`, `{ic}` & `8Bit_shiftreg{lay}` in `.jelib` exporting parallel outputs `Q0..Q7` directly to `CA0..CA3` and `RA0..RA3`, 100% Manhattan, 0 DRC, 100% LVS match).
- **3-Bit Synchronous Counter:** Complete (`3Bit_counter{sch}` & `3Bit_counter{lay}` in `.jelib`, 100% Manhattan, 0 DRC, 100% LVS match; verified in `3Bit_counter_test.spi`).
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
- [x] Layout fundamental standard cells:
  - [x] Ultra-Compact Shared-Diffusion 6T SRAM Bitcell (`6T_cell{lay}`) — Ultra-compact dimensions ($45.0\lambda \times 72.0\lambda = 3,240\ \lambda^2$ / $4.05\ \mu\text{m} \times 6.48\ \mu\text{m}$, 50.0% area reduction vs previous $72\lambda \times 90\lambda$ layout and 89.88% reduction vs original $200\lambda \times 160\lambda = 32,000\ \lambda^2$), continuous shared active diffusion architecture (all 4 NMOS share a single horizontal N-active row sharing Q, GND, and QB diffusions; both PMOS share a single horizontal P-active row sharing VDD diffusion), minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$ for all transistors), 100% Manhattan perpendicular routing (41 arcs), 0 DRC violations/warnings via Electric's built-in Quick DRC engine (`ALGO_SWEEP`), 100% LVS / NCC match (topology, exports, transistor sizing: Drivers $W=7, L=2$, Access $W=4, L=2$, Loads $W=3, L=2$). Generated by `scripts/09_layout_compact_6t_cell.py`.
  - [x] Ultra-Compact Inverter (`Not{lay}`) — Ultra-compact dimensions ($32\lambda \times 52\lambda = 1664\ \lambda^2$ / $2.88\ \mu\text{m} \times 4.68\ \mu\text{m}$, 48.0% area reduction vs original $56\lambda \times 76\lambda$), minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$ for all source/drain contacts `con_p_vdd`, `con_p_out`, `con_n_gnd`, `con_n_out`), 100% Manhattan perpendicular routing (17 arcs), 0 DRC violations/warnings verified via Electric's built-in Quick DRC engine (`ALGO_SWEEP`), 100% LVS / NCC match (topology, exports, transistor sizes $W=8,4, L=2$). Generated by `scripts/07_layout_not_and_nand.py`.
  - [x] Ultra-Compact 4-Input NAND Gate (`Nand{lay}`) — Ultra-compact standard cell ($72\lambda \times 52\lambda = 3744\ \lambda^2$ / $6.48\ \mu\text{m} \times 4.68\ \mu\text{m}$, 66.7% area reduction vs original $148\lambda \times 76\lambda = 11,248\ \lambda^2$ and 38% reduction vs previous $116\lambda \times 52\lambda$), minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$ across all 4 PMOS and 4 NMOS transistors and shared active contacts), perfectly pitch-matched standard cell height with `Not{lay}` ($Y_{\text{VDD}} = +26.0\lambda, Y_{\text{GND}} = -26.0\lambda$), 100% Manhattan perpendicular routing (43 arcs), 0 DRC violations/warnings via Electric's built-in Quick DRC engine (`ALGO_SWEEP`), 100% NCC/LVS match (topology, exports, transistor sizing $W=4, L=2$). Generated by `scripts/07_layout_not_and_nand.py`.
  - [x] 4-to-16 Address Decoder (`Decoder{lay}`) — Hierarchical physical layout ($192\lambda \times 1520\lambda = 17.28\ \mu\text{m} \times 136.8\ \mu\text{m}$), instantiating 16 `Nand{lay}` and 20 `Not{lay}` subcells, structured 8-track vertical Metal-2 address bus with clean channel dogs, vertical Metal-2 power straps, 100% Manhattan perpendicular routing (322 arcs), 0 DRC violations/warnings via Electric's built-in Quick DRC engine (`ALGO_SWEEP`), 100% hierarchical NCC/LVS match (topology, exports, transistor sizing).
  - [x] Ultra-Compact Precharge Circuit (`Precharge_ckt{lay}`) — Ultra-compact single continuous shared diffusion row ($44\lambda \times 22\lambda = 968\ \lambda^2$ / $3.96\ \mu\text{m} \times 1.98\ \mu\text{m}$). Minimum contact-to-MOSFET spacing ($dx = 4.5\lambda = 0.405\ \mu\text{m}$ across all transistors and active contacts), integrated VDD well tap (`Metal-1-N-Well-Con`), 100% Manhattan perpendicular routing (15 arcs), 0 DRC errors/warnings via Electric Quick DRC engine (`ALGO_SWEEP`), 100% LVS / NCC match (topology, exports, transistor sizing: Pull-ups $W=4\lambda, L=2\lambda$, Equalizer $W=3\lambda, L=2\lambda$). Generated by `scripts/10_layout_precharge.py`.
  - [x] Master-Slave Transmission-Gate D Flip-Flop (`D_flipflop{lay}`) — Standard cell ($287\lambda \times 56\lambda = 16,072\ \lambda^2$ / $25.83\ \mu\text{m} \times 5.04\ \mu\text{m}$) containing 20 transistors (6 CMOS inverters + 4 CMOS transmission gates). Minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all 20 transistors on both source and drain sides. Dedicated horizontal Metal-2 routing tracks for clock busses (`CLK2` @ $Y=+21.0\lambda$, `CLKB` @ $Y=-21.0\lambda$) and internal signal interconnects (`net@6`, `net@45`, `net@14`, `net@48`, `net@22`, `Q`). 100% Manhattan perpendicular routing (168 arcs), 0 DRC errors/warnings via Electric Quick DRC engine (`ALGO_SWEEP`), 100% LVS / NCC match with `checkSizes = True` (5 exports: `CLK`, `D`, `GND`, `Q`, `VDD`, topology, and transistor sizing). Generated by `scripts/11_layout_d_flipflop.py`.
  - [x] Ultra-Compact Shared-Diffusion Sense Amplifier (`Sense_amp{lay}`) — Ultra-compact standard cell ($62\lambda \times 56\lambda = 3,472\ \lambda^2$ / $5.58\ \mu\text{m} \times 5.04\ \mu\text{m}$, 48.3% area reduction vs previous non-shared layout) containing 7 transistors. Features continuous shared active diffusions:
    - PMOS current mirror (`pmos@4` & `pmos@5`) shares continuous P-active VDD diffusion contact at $X = 16.5\lambda$.
    - NMOS differential pair (`nmos@3` & `nmos@4`) shares continuous N-active TAIL (`net@38`) diffusion contact at $X = 16.5\lambda$.
    - Tail enable NMOS (`nmos@5`) and inverter NMOS (`nmos@6`) share continuous N-active GND diffusion contact at $X = 46.5\lambda$.
    - Minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all 7 transistors.
    - Low-resistance Metal-1 / Metal-2 routing with dedicated Manhattan tracks, 100% Manhattan perpendicular routing (48 arcs), 0 DRC errors/warnings via Electric Quick DRC engine (`ALGO_SWEEP`), 100% LVS / NCC match with `checkSizes = True` (5 exports: `BIT`, `BITB`, `READ_EN`, `SENSE_OUT`, `VDD`, `GND`). Generated by `scripts/12_layout_sense_amp.py`.
  - [x] Ultra-Compact Shared-Diffusion Write Driver (`Write_driver{lay}`) — Ultra-compact standard cell ($78\lambda \times 56\lambda = 4,368\ \lambda^2$ / $7.02\ \mu\text{m} \times 5.04\ \mu\text{m}$) containing 6 transistors (1 PMOS, 5 NMOS). Features:
    - Continuous shared active diffusions for series pull-down NMOS pairs: `nmos@0` and `nmos@4` share `net@6` diffusion contact at $X = 15.5\lambda$; `nmos@6` and `nmos@5` share `net@12` diffusion contact at $X = 60.5\lambda$.
    - Minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all transistors on both source and drain sides.
    - Low-resistance Metal-2 bus at $Y = -21.0\lambda$ for `WRITE_EN` distribution.
    - Low-resistance Metal-1 interconnect from inverter output directly to `nmos@6` gate.
    - 100% Manhattan perpendicular routing (39 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `Write_driver{sch}` (6 exports: `BIT`, `BITB`, `DATA`, `GND`, `VDD`, `WRITE_EN`, topologies, and transistor sizes). Generated by `scripts/13_layout_write_driver.py`.
  - [x] Ultra-Compact Transmission Gate Bitline Multiplexer (`TG_bitline{lay}`) — Ultra-compact standard cell ($56\lambda \times 56\lambda = 3,136\ \lambda^2$ / $5.04\ \mu\text{m} \times 5.04\ \mu\text{m}$) containing 6 transistors (3 PMOS: `pmos@0` $W=8$, `pmos@1` $W=8$, `pmos@3` $W=3$; 3 NMOS: `nmos@0` $W=4$, `nmos@1` $W=4$, `nmos@2` $W=3$). Features:
    - Minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all transistors on both source and drain sides.
    - Straight, low-resistance vertical Metal-1 lines for `BIT_U`, `BIT_D`, `BITB_U`, `BITB_D`.
    - Low-resistance horizontal Metal-2 buses for complementary enable distribution: `ENB` @ $Y = +21.0\lambda$, `EN` @ $Y = -21.0\lambda$.
    - Standard cell pitch matching VDD @ $Y = +28.0\lambda$ and GND @ $Y = -28.0\lambda$.
    - 100% Manhattan perpendicular routing (47 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `TG_bitline{sch}` (7 exports: `BIT_U`, `BIT_D`, `BITB_U`, `BITB_D`, `EN`, `VDD`, `GND`, topologies, and transistor sizes). Generated by `scripts/14_layout_tg_bitline.py`.
  - [x] Ultra-Compact Shared-Diffusion Wordline Driver (`WL_driver{lay}`) — Ultra-compact standard cell ($52\lambda \times 56\lambda = 2,912\ \lambda^2$ / $4.68\ \mu\text{m} \times 5.04\ \mu\text{m}$) containing 6 transistors (3 PMOS, 3 NMOS: 2-input NAND stage + Inverter buffer). Features:
    - Continuous shared active diffusions:
      - PMOS NAND pair (`pmos@0` & `pmos@1`) shares continuous P-active diffusion with shared center drain contact `pcm_01` (`NAND_OUT`).
      - NMOS NAND pair (`nmos@0` & `nmos@1`) shares continuous N-active diffusion with shared center series contact `ncm_01` (`net@9`).
    - Minimum contact-to-MOSFET active diffusion distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all transistors on both source and drain sides.
    - Standard cell pitch matching ($Y_{\text{VDD}} = +28.0\lambda, Y_{\text{GND}} = -28.0\lambda$, height $56.0\lambda$).
    - Low-resistance horizontal Metal-1 wire for `NAND_OUT` at $Y = 0.0$ connecting directly to inverter gate contact `con_ginv` ($X = 33.0$).
    - Low-resistance vertical Metal-1 line at $X = 44.5\lambda$ connecting inverter drains for `WL` output.
    - 100% Manhattan perpendicular routing (38 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `WL_driver{sch}` (5 exports: `EN`, `GND`, `IN`, `VDD`, `WL`, topologies, and transistor sizes). Generated by `scripts/15_layout_wl_driver.py`.
  - [x] Standard-Cell Control Logic Unit (`Control_logic{lay}`) — Standard cell ($469\lambda \times 56\lambda = 26,264\ \lambda^2$ / $42.21\ \mu\text{m} \times 5.04\ \mu\text{m}$) containing 42 transistors (21 PMOS, 21 NMOS across 21 columns) implementing the complete 8-cycle inverted-phase control subsystem:
    - CLK Inverter, CLKB Buffer, PCB Buffer ($W_P=12, W_N=6$), CTRL Inverter.
    - 3 Shared-diffusion NAND pairs: `WL_EN` NAND (`pmos@11,12` & `nmos@11,12`), `WRITE_EN` NAND (`pmos@5,6` & `nmos@5,6`), `READ_EN` NAND (`pmos@8,9` & `nmos@8,9`).
    - `WL_EN` Buffer ($W_P=12, W_N=6$) and `WRITE_EN` Buffer ($W_P=12, W_N=6$).
    - 8-stage CMOS inverter delay line (`p14..p21` / `n14..n21`) & `READ_EN` Buffer ($W_P=12, W_N=6$).
    - Continuous shared active diffusions for all 3 NAND pairs with minimum active contact distance ($dx = 4.5\lambda = 0.405\ \mu\text{m}$) across all 42 transistors on both source and drain sides.
    - Pitch-matched standard cell height ($56.0\lambda$, $Y_{\text{VDD}} = +28.0\lambda, Y_{\text{GND}} = -28.0\lambda$).
    - Dedicated horizontal routing tracks: Track $Y = +7.0\lambda$ (Metal-2 for `CTRL`), Track $Y = 0.0\lambda$ (Metal-1 for gate/inverter I/O), Track $Y = -7.0\lambda$ (Metal-2 for `CLKB` and `WL_EN`), Track $Y = -21.0\lambda$ (Metal-2 for `CTRLB`).
    - 100% Manhattan perpendicular routing (301 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `Control_logic{sch}` (9 exports: `CLK`, `COUNT_7`, `CTRL`, `GND`, `PCB`, `READ_EN`, `VDD`, `WL_EN`, `WRITE_EN`, topologies, and transistor sizes). Generated by `scripts/16_layout_control_logic.py`.
  - [x] Standard-Cell 3-Bit Synchronous Binary Counter (`3Bit_counter{lay}`) — Hierarchical standard-cell block ($287\lambda \times 228\lambda = 65,436\ \lambda^2$ / $25.83\ \mu\text{m} \times 20.52\ \mu\text{m}$) containing 74 transistors across 3 rows:
    - Row 0 ($Y = 0\lambda$): `D_flipfl@0` ($20$ tx), Inverter $I_0$ ($W=4/2$, $2$ tx).
    - Row 1 ($Y = 86\lambda$): `D_flipfl@1` ($20$ tx), XOR Gate $X_1$ ($6$ tx), Inverter $I_1$ ($W=4/2$, $2$ tx).
    - Row 2 ($Y = 172\lambda$): `D_flipfl@2` ($20$ tx), 3-input NAND $N_2$ ($6$ tx), XOR Gate $X_2$ ($6$ tx), Inverter $I_2$ ($W=4/2$, $2$ tx).
    - Structured vertical Metal-2 power grid straps (`VDD` @ $X = -38.0\lambda$, `GND` @ $X = -46.0\lambda$, `CLK` @ $X = -30.0\lambda$) with Metal-1 horizontal drops.
    - Low-resistance inter-row feedback and feed-forward Metal-1 & Metal-2 routing channels.
    - 100% Manhattan perpendicular routing (295 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `3Bit_counter{sch}` (6 exports: `CLK`, `COUNT_7`, `GND`, `Q0`, `Q1`, `Q2`, `VDD`, topologies, and transistor sizes). Generated by `scripts/17_layout_3bit_counter.py`.
  - [x] Standard-Cell 8-Bit Parallel Register (`8Bit_reg{lay}`) — Hierarchical standard-cell block ($287\lambda \times 658\lambda = 188,846\ \lambda^2$ / $25.83\ \mu\text{m} \times 59.22\ \mu\text{m}$) containing 160 transistors:
    - 8 D Flip-Flop standard cell instances (`D_flipfl@0` to `D_flipfl@7`) instantiating `D_flipflop{lay}` with row pitch $DY = 86.0\lambda$.
    - Structured vertical Metal-2 power grid straps (`VDD` @ $X = -38.0\lambda$, `GND` @ $X = -46.0\lambda$, `CLK` @ $X = -30.0\lambda$) with Metal-1 horizontal drops.
    - 19 exports: `CLK`, `VDD`, `GND`, `D0`..`D7`, `Q0`..`Q7`.
    - 100% Manhattan perpendicular routing (45 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `8Bit_reg{sch}` (19 exports, topologies, and transistor sizes). Generated by `scripts/18_layout_8bit_reg.py`.
  - [x] Standard-Cell 8-Bit Shift Register (`8Bit_shiftreg{lay}`) — Hierarchical standard-cell block ($287\lambda \times 658\lambda = 188,846\ \lambda^2$ / $25.83\ \mu\text{m} \times 59.22\ \mu\text{m}$) containing 160 transistors:
    - 8 D Flip-Flop standard cell instances (`D_flipfl@0` to `D_flipfl@7`) instantiating `D_flipflop{lay}` with row pitch $DY = 86.0\lambda$.
    - Structured vertical Metal-2 power grid straps (`VDD` @ $X = -38.0\lambda$, `GND` @ $X = -46.0\lambda$, `CLK` @ $X = -30.0\lambda$) with Metal-1 horizontal drops.
    - Clean inter-row cascading channels routing $Q[i] \to D[i+1]$ on Metal-1 with zero Metal-2 collisions inside DFF cells.
    - 11 exports: `CLK`, `VDD`, `GND`, `D`, `Q0`..`Q7`.
    - 100% Manhattan perpendicular routing (87 arcs, 0 non-perpendicular arcs).
    - 0 DRC errors and 0 warnings via Electric Quick DRC engine (`ALGO_SWEEP`).
    - 100% LVS / NCC match with `checkSizes = True` against `8Bit_shiftreg{sch}` (11 exports, topologies, and transistor sizes). Generated by `scripts/19_layout_8bit_shiftreg.py`.
- [ ] Array layout: $16 \times 16$ symmetric pitch-matched placement.
- [ ] Layout remaining peripheral blocks (precharge, sense amp, write driver, address register).
- [ ] Route `VDD` and `GND` power grid on Top Metal (Metal 5/6).
- [ ] Full-chip DRC and LVS signoff.

### Phase 5: Power & Frequency Characterization
- [x] Schematic-level full-chip transient verification (`spice/Top_test.spi`).
- [ ] Post-layout parasitic extraction (PEX) and simulation.
- [x] Measure read energy/power per bit ($E_{\text{read}} = 3.138\text{ pJ/bit}, P_{\text{read}} = 313.79\ \mu\text{W}$).
- [x] Measure write energy/power per bit ($E_{\text{write}} = 2.738\text{ pJ/bit}, P_{\text{write}} = 273.83\ \mu\text{W}$).
- [x] Measure critical path delay and calculate maximum clock frequency ($t_{\text{CQ}} = 370.3\text{ ps}$, $F_{\text{max}} > 500\text{ MHz}$).
