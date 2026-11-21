import re
import subprocess
import os

# 1. Read Top_package_scale90.spi
with open(r"D:\Projects\Memory-IC-Design\spice\Top_package_scale90.spi", "r") as f:
    text = f.read()

# Replace all '@' with '_' for SPICE netlist compatibility
text_clean = text.replace("@", "_")

# Add title comment on line 1, then include for tsmc018.lib
header = """* Testbench for Top_package with Rser=50 and Package Parasitics
.include D:\\Projects\\Memory-IC-Design\\lib\\tsmc018.lib

"""

# 2. Update 3Bit_counter subcircuit to expose C0, C1, C2
text_clean = text_clean.replace(
    ".SUBCKT Memory-IC-Design__3Bit_counter CLK COUNT_7 gnd vdd",
    ".SUBCKT Memory-IC-Design__3Bit_counter CLK COUNT_7 gnd vdd C0 C1 C2"
)

# 3. Add 6T_cell_mon subcircuit
cell_mon_def = """
*** MONITORED 6T SRAM BITCELL SUBCIRCUIT
.SUBCKT Memory-IC-Design__6T_cell_mon BIT BITB gnd vdd WL Q QB
Mnmos_0 Q   QB  gnd gnd CMOSN L=0.18U W=0.63U
Mnmos_1 QB  Q   gnd gnd CMOSN L=0.18U W=0.63U
Mnmos_2 Q   WL  BIT gnd CMOSN L=0.18U W=0.36U
Mnmos_3 BITB WL QB  gnd CMOSN L=0.18U W=0.36U
Mpmos_0 vdd QB  Q   vdd CMOSP L=0.18U W=0.27U
Mpmos_1 vdd Q   QB  vdd CMOSP L=0.18U W=0.27U
.ENDS Memory-IC-Design__6T_cell_mon
"""
text_clean = text_clean.replace(".ENDS Memory-IC-Design__6T_cell", ".ENDS Memory-IC-Design__6T_cell\n" + cell_mon_def)

# 4. Update 256bit_array subcircuit header to export 8 monitor pins
arr_sub_start = text_clean.find(".SUBCKT Memory-IC-Design__256bit_array")
arr_sub_end = text_clean.find("\n", arr_sub_start)
old_arr_header = text_clean[arr_sub_start:arr_sub_end]
new_arr_header = old_arr_header + " Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5"
text_clean = text_clean[:arr_sub_start] + new_arr_header + text_clean[arr_sub_end:]

# Replace the 4 monitored cells in 256bit_array
# Row 10, Col 5: X_6T_cell_602
text_clean = re.sub(
    r'X_6T_cell_602\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_602 \1 \2 \3 \4 \5 Q_r10_c5 QB_r10_c5 Memory-IC-Design__6T_cell_mon',
    text_clean
)
# Row 3, Col 12: X_6T_cell_721
text_clean = re.sub(
    r'X_6T_cell_721\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_721 \1 \2 \3 \4 \5 Q_r3_c12 QB_r3_c12 Memory-IC-Design__6T_cell_mon',
    text_clean
)
# Row 10, Col 4: X_6T_cell_601
text_clean = re.sub(
    r'X_6T_cell_601\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_601 \1 \2 \3 \4 \5 Q_r10_c4 QB_r10_c4 Memory-IC-Design__6T_cell_mon',
    text_clean
)
# Row 9, Col 5: X_6T_cell_618
text_clean = re.sub(
    r'X_6T_cell_618\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_618 \1 \2 \3 \4 \5 Q_r9_c5 QB_r9_c5 Memory-IC-Design__6T_cell_mon',
    text_clean
)

# 5. In Memory-IC-Design__Top:
# Update X_3Bit_cou_0 instantiation:
text_clean = text_clean.replace(
    "X_3Bit_cou_0 CLK_int COUNT_7 gnd vdd Memory-IC-Design__3Bit_counter",
    "X_3Bit_cou_0 CLK_int COUNT_7 gnd vdd C0 C1 C2 Memory-IC-Design__3Bit_counter"
)

# Update X_256bit_a_0 call in Top:
text_clean = re.sub(
    r'(X_256bit_a_0\s+.*?WL9)\s+Memory-IC-Design__256bit_array',
    r'\1 Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5 Memory-IC-Design__256bit_array',
    text_clean
)

# Update Memory-IC-Design__Top subcircuit header:
top_sub_start = text_clean.find(".SUBCKT Memory-IC-Design__Top")
top_sub_end = text_clean.find("\n", top_sub_start)
old_top_header = text_clean[top_sub_start:top_sub_end]
new_top_header = old_top_header + " C0 C1 C2 Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5"
text_clean = text_clean[:top_sub_start] + new_top_header + text_clean[top_sub_end:]

# 6. In Top_package:
# Update XTop_0 call in Top_package:
text_clean = re.sub(
    r'(XTop_0\s+.*?net_21)\s+Memory-IC-Design__Top',
    r'\1 C0 C1 C2 Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5 Memory-IC-Design__Top',
    text_clean
)

# In Top_package, replace net_24 with GND_PCB so package ground returns to PCB ground
top_pkg_start = text_clean.find(".SUBCKT Top_package")
top_pkg_end = text_clean.find(".ENDS Top_package", top_pkg_start)
top_pkg_body = text_clean[top_pkg_start:top_pkg_end]
top_pkg_body_mod = top_pkg_body.replace("net_24", "GND_PCB")

# Expose C0 C1 C2 and monitor pins on Top_package:
top_pkg_body_mod = top_pkg_body_mod.replace(
    ".SUBCKT Top_package ADDR_IN_PCB CLK_PCB CTRL_PCB DIN_PCB DOUT_PCB GND_PCB VDD_PCB",
    ".SUBCKT Top_package ADDR_IN_PCB CLK_PCB CTRL_PCB DIN_PCB DOUT_PCB GND_PCB VDD_PCB C0 C1 C2 Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5"
)
text_clean = text_clean[:top_pkg_start] + top_pkg_body_mod + text_clean[top_pkg_end:]

# Strip any existing .END lines
lines = [l for l in text_clean.splitlines() if not l.strip().upper() == ".END"]
netlist = header + "\n".join(lines) + "\n"

# 7. Add top-level testbench with comprehensive Power and Operation Measurements
testbench = """
*** Top-Level Instantiation of Packaged IC
XTop_pkg ADDR_IN_PCB CLK_PCB CTRL_PCB DIN_PCB DOUT_PCB GND_PCB VDD_PCB C0 C1 C2 Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5 Top_package

*** Power Supplies & Output Load
VDDsrc VDD_PCB 0 DC 1.8
VGND   GND_PCB 0 DC 0
C_dout DOUT_PCB GND_PCB 20f

*** Initial Conditions
* 3-Bit counter initialized to 111 so Edge #1 is Count 000
.ic V(C0)=1.8 V(C1)=1.8 V(C2)=1.8
* Cell (10, 5): initial DATA=0 (Q=1.8V, QB=0V) to verify Write '1' flips it
.ic V(Q_r10_c5)=1.8 V(QB_r10_c5)=0
* Cell (3, 12): initial DATA=1 (Q=0V, QB=1.8V) to verify Write '0' flips it
.ic V(Q_r3_c12)=0 V(QB_r3_c12)=1.8
* Unselected adjacent cells on Row 10 (Col 4) and Col 5 (Row 9) to verify zero disturb
.ic V(Q_r10_c4)=1.8 V(QB_r10_c4)=0
.ic V(Q_r9_c5)=0 V(QB_r9_c5)=1.8

*** External Stimuli with 50-Ohm Series Resistor (Rser=50) on PCB Signal Sources
VCLK CLK_PCB 0 PULSE(0 1.8 5n 50p 50p 4.95n 10n) Rser=50
VADDR ADDR_IN_PCB 0 PWL(0n 1.8 9.9n 1.8 10.1n 0.0 19.9n 0.0 20.1n 1.8 29.9n 1.8 30.1n 0.0 39.9n 0.0 40.1n 0.0 49.9n 0.0 50.1n 1.8 59.9n 1.8 60.1n 0.0 69.9n 0.0 70.1n 1.8 79.9n 1.8 80.1n 0.0 89.9n 0.0 90.1n 0.0 99.9n 0.0 100.1n 1.8 109.9n 1.8 110.1n 1.8 119.9n 1.8 120.1n 1.8 129.9n 1.8 130.1n 1.8 139.9n 1.8 140.1n 0.0 149.9n 0.0 150.1n 0.0 159.9n 0.0 160.1n 1.8 169.9n 1.8 170.1n 0.0 179.9n 0.0 180.1n 1.8 189.9n 1.8 190.1n 0.0 199.9n 0.0 200.1n 0.0 209.9n 0.0 210.1n 1.8 219.9n 1.8 220.1n 0.0 229.9n 0.0 230.1n 1.8 239.9n 1.8 240.1n 0.0 249.9n 0.0 250.1n 0.0 259.9n 0.0 260.1n 1.8 269.9n 1.8 270.1n 1.8 279.9n 1.8 280.1n 1.8 289.9n 1.8 290.1n 1.8 299.9n 1.8 300.1n 0.0 309.9n 0.0 310.1n 0.0 319.9n 0.0 320.1n 0.0 340n 0.0) Rser=50
VCTRL CTRL_PCB 0 PWL(0n 0  165.9n 0  166.0n 1.8  340n 1.8) Rser=50
VDIN DIN_PCB 0 PWL(0n 1.8  85.9n 1.8  86.0n 0  340n 0) Rser=50

.TRAN 20p 340n

*** Measurements: Cell Data & Latched Output Verification
* Write '1' into (10, 5)
.MEAS TRAN V_r10c5_Q_after_w1  FIND V(Q_r10_c5)  AT=84.5n
.MEAS TRAN V_r10c5_QB_after_w1 FIND V(QB_r10_c5) AT=84.5n
.MEAS TRAN t_write1_flip TRIG V(CLK_PCB) VAL=0.9 FALL=8 TARG V(QB_r10_c5) VAL=1.62 RISE=1

* Write '0' into (3, 12)
.MEAS TRAN V_r3c12_Q_after_w0  FIND V(Q_r3_c12)  AT=164.5n
.MEAS TRAN V_r3c12_QB_after_w0 FIND V(QB_r3_c12) AT=164.5n
.MEAS TRAN t_write0_flip TRIG V(CLK_PCB) VAL=0.9 FALL=16 TARG V(Q_r3_c12) VAL=1.62 RISE=1

* Read '1' & Read '0' Latched Output on DOUT_PCB
.MEAS TRAN V_dout_latched_f3 FIND V(DOUT_PCB) AT=250n
.MEAS TRAN V_dout_latched_f4 FIND V(DOUT_PCB) AT=330n

* Disturb Immunity Check on unselected neighbors
.MEAS TRAN V_unselected_r10c4_Q FIND V(Q_r10_c4) AT=325n
.MEAS TRAN V_unselected_r9c5_QB FIND V(QB_r9_c5) AT=325n

*** ========================================================
*** Accurate Power and Energy Calculations for Read & Write
*** ========================================================

* 1. Quiescent / Standby Power (before first clock pulse)
.MEAS TRAN P_standby        AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=0n TO=4.9n

* 2. Frame 1 (Write '1' Full 8-Cycle Frame: 5ns to 85ns)
.MEAS TRAN P_write1_frame   AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=5n TO=85n
.MEAS TRAN E_write1_frame   INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=5n TO=85n

* 3. Write '1' Active Pulse Cycle (Cycle 8: 80ns to 85ns, when WL10 is active and bitcell is written)
.MEAS TRAN P_write1_active  AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=80n TO=85n
.MEAS TRAN E_write1_active  INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=80n TO=85n
.MEAS TRAN P_write1_peak    MAX (-V(VDD_PCB)*I(VDDsrc)) FROM=80n TO=85n

* 4. Frame 2 (Write '0' Full 8-Cycle Frame: 85ns to 165ns)
.MEAS TRAN P_write0_frame   AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=85n TO=165n
.MEAS TRAN E_write0_frame   INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=85n TO=165n

* 5. Write '0' Active Pulse Cycle (Cycle 16: 160ns to 165ns, when WL3 is active and bitcell is written)
.MEAS TRAN P_write0_active  AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=160n TO=165n
.MEAS TRAN E_write0_active  INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=160n TO=165n
.MEAS TRAN P_write0_peak    MAX (-V(VDD_PCB)*I(VDDsrc)) FROM=160n TO=165n

* 6. Frame 3 (Read '1' Full 8-Cycle Frame: 165ns to 245ns)
.MEAS TRAN P_read1_frame    AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=165n TO=245n
.MEAS TRAN E_read1_frame    INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=165n TO=245n

* 7. Read '1' Active Pulse Cycle (Cycle 24: 240ns to 245ns, when WL10, column mux, sense amp & DFF latch)
.MEAS TRAN P_read1_active   AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=240n TO=245n
.MEAS TRAN E_read1_active   INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=240n TO=245n
.MEAS TRAN P_read1_peak     MAX (-V(VDD_PCB)*I(VDDsrc)) FROM=240n TO=245n

* 8. Frame 4 (Read '0' Full 8-Cycle Frame: 245ns to 325ns)
.MEAS TRAN P_read0_frame    AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=245n TO=325n
.MEAS TRAN E_read0_frame    INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=245n TO=325n

* 9. Read '0' Active Pulse Cycle (Cycle 32: 320ns to 325ns, when WL3, column mux, sense amp & DFF latch)
.MEAS TRAN P_read0_active   AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=320n TO=325n
.MEAS TRAN E_read0_active   INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=320n TO=325n
.MEAS TRAN P_read0_peak     MAX (-V(VDD_PCB)*I(VDDsrc)) FROM=320n TO=325n

* 10. Overall Full-Chip Average Across Entire Active Operation (5ns to 325ns)
.MEAS TRAN P_chip_avg       AVG (-V(VDD_PCB)*I(VDDsrc)) FROM=5n TO=325n
.MEAS TRAN E_chip_total     INTEG (-V(VDD_PCB)*I(VDDsrc)) FROM=5n TO=325n

.END
"""

final_deck = netlist + testbench
test_spi_path = r"D:\Projects\Memory-IC-Design\spice\Top_package_test.spi"
with open(test_spi_path, "w") as f:
    f.write(final_deck)

print("Generated:", test_spi_path, "Size:", len(final_deck))
