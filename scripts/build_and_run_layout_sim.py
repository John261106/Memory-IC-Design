import os
import subprocess
import re

# 1. Read clean Top_layout.spi
with open(r"D:\Projects\Memory-IC-Design\spice\Top_layout.spi", "r") as f:
    text = f.read()

# Replace all '@' with '_' for SPICE instance & net compatibility
text_clean = text.replace("@", "_")

# Expose counter flip-flop outputs C0, C1, C2 in 3Bit_counter subcircuit
text_clean = text_clean.replace(
    ".SUBCKT Memory-IC-Design__3Bit_counter CLK COUNT_7 gnd vdd",
    ".SUBCKT Memory-IC-Design__3Bit_counter CLK COUNT_7 gnd vdd C0 C1 C2"
)
sub_start = text_clean.find(".SUBCKT Memory-IC-Design__3Bit_counter")
sub_end = text_clean.find(".ENDS Memory-IC-Design__3Bit_counter", sub_start)
counter_sub = text_clean[sub_start:sub_end]
counter_sub_mod = counter_sub.replace("net_112", "C0").replace("net_58", "C1").replace("net_66", "C2")
text_clean = text_clean[:sub_start] + counter_sub_mod + text_clean[sub_end:]

# Update X_3Bit_cou_0 instantiation in Top
text_clean = text_clean.replace(
    "X_3Bit_cou_0 CLK net_19561 gnd vdd Memory-IC-Design__3Bit_counter",
    "X_3Bit_cou_0 CLK net_19561 gnd vdd C0 C1 C2 Memory-IC-Design__3Bit_counter"
)

# Add 6T_cell_mon subcircuit
cell_mon_def = """
*** MONITORED 6T SRAM BITCELL SUBCIRCUIT (Layout-extracted sizes & diff parasitics)
.SUBCKT Memory-IC-Design__6T_cell_mon BIT BITB gnd vdd WL Q QB
Mnmos_0 gnd QB Q gnd CMOSN L=0.18U W=0.63U AS=0.184P AD=0.456P PS=1.5U PD=2.655U
Mnmos_1 QB Q gnd gnd CMOSN L=0.18U W=0.63U AS=0.456P AD=0.184P PS=2.655U PD=1.5U
Mnmos_2 Q WL BIT gnd CMOSN L=0.18U W=0.36U AS=0.235P AD=0.184P PS=1.98U PD=1.5U
Mnmos_3 BITB WL QB gnd CMOSN L=0.18U W=0.36U AS=0.184P AD=0.235P PS=1.5U PD=1.98U
Mpmos_0 vdd QB Q vdd CMOSP L=0.18U W=0.27U AS=0.184P AD=0.275P PS=1.5U PD=2.34U
Mpmos_1 QB Q vdd vdd CMOSP L=0.18U W=0.27U AS=0.275P AD=0.275P PS=2.34U PD=1.5U
.ENDS Memory-IC-Design__6T_cell_mon
"""
text_clean = text_clean.replace(".ENDS Memory-IC-Design__6T_cell", ".ENDS Memory-IC-Design__6T_cell\n" + cell_mon_def)

# Update 256bit_array subcircuit header to export 8 monitor pins
arr_sub_start = text_clean.find(".SUBCKT Memory-IC-Design__256bit_array")
arr_sub_end = text_clean.find("\n", arr_sub_start)
old_arr_header = text_clean[arr_sub_start:arr_sub_end]
new_arr_header = old_arr_header + " Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5"
text_clean = text_clean[:arr_sub_start] + new_arr_header + text_clean[arr_sub_end:]

# Replace cells 165, 60, 164, 149 with 6T_cell_mon
text_clean = re.sub(
    r'X_6T_cell_165\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_165 \1 \2 \3 \4 \5 Q_r10_c5 QB_r10_c5 Memory-IC-Design__6T_cell_mon',
    text_clean
)
text_clean = re.sub(
    r'X_6T_cell_60\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_60 \1 \2 \3 \4 \5 Q_r3_c12 QB_r3_c12 Memory-IC-Design__6T_cell_mon',
    text_clean
)
text_clean = re.sub(
    r'X_6T_cell_164\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_164 \1 \2 \3 \4 \5 Q_r10_c4 QB_r10_c4 Memory-IC-Design__6T_cell_mon',
    text_clean
)
text_clean = re.sub(
    r'X_6T_cell_149\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+Memory-IC-Design__6T_cell',
    r'X_6T_cell_149 \1 \2 \3 \4 \5 Q_r9_c5 QB_r9_c5 Memory-IC-Design__6T_cell_mon',
    text_clean
)

# Update X_256bit_a_0 call in Top
text_clean = text_clean.replace(
    "+Memory-IC-Design__256bit_array",
    "+Q_r10_c5 QB_r10_c5 Q_r3_c12 QB_r3_c12 Q_r10_c4 QB_r10_c4 Q_r9_c5 QB_r9_c5 Memory-IC-Design__256bit_array"
)

# Strip any existing .END lines
lines = [l for l in text_clean.splitlines() if not l.strip().upper() == ".END"]
netlist = "\n".join(lines) + "\n"

testbench = """
*** Power Supplies & Output Load
VDDsrc vdd 0 DC 1.8
VGND   gnd 0 DC 0
C_dout DOUT gnd 20f

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

*** External Stimuli
VCLK CLK 0 PULSE(0 1.8 5n 50p 50p 4.95n 10n)
VADDR ADDR_IN 0 PWL(0n 1.8 9.9n 1.8 10.1n 0.0 19.9n 0.0 20.1n 1.8 29.9n 1.8 30.1n 0.0 39.9n 0.0 40.1n 0.0 49.9n 0.0 50.1n 1.8 59.9n 1.8 60.1n 0.0 69.9n 0.0 70.1n 1.8 79.9n 1.8 80.1n 0.0 89.9n 0.0 90.1n 0.0 99.9n 0.0 100.1n 1.8 109.9n 1.8 110.1n 1.8 119.9n 1.8 120.1n 1.8 129.9n 1.8 130.1n 1.8 139.9n 1.8 140.1n 0.0 149.9n 0.0 150.1n 0.0 159.9n 0.0 160.1n 1.8 169.9n 1.8 170.1n 0.0 179.9n 0.0 180.1n 1.8 189.9n 1.8 190.1n 0.0 199.9n 0.0 200.1n 0.0 209.9n 0.0 210.1n 1.8 219.9n 1.8 220.1n 0.0 229.9n 0.0 230.1n 1.8 239.9n 1.8 240.1n 0.0 249.9n 0.0 250.1n 0.0 259.9n 0.0 260.1n 1.8 269.9n 1.8 270.1n 1.8 279.9n 1.8 280.1n 1.8 289.9n 1.8 290.1n 1.8 299.9n 1.8 300.1n 0.0 309.9n 0.0 310.1n 0.0 319.9n 0.0 320.1n 0.0 340n 0.0)
VCTRL CTRL 0 PWL(0n 0  165.9n 0  166.0n 1.8  340n 1.8)
VDIN DIN 0 PWL(0n 1.8  85.9n 1.8  86.0n 0  340n 0)

.TRAN 20p 340n

*** Measurements
* Frame 1 Address Check (at t = 79ns)
.MEAS TRAN V_ra3_f1 FIND V(net_19526) AT=79n
.MEAS TRAN V_ra2_f1 FIND V(net_19518) AT=79n
.MEAS TRAN V_ra1_f1 FIND V(net_19510) AT=79n
.MEAS TRAN V_ra0_f1 FIND V(net_19503) AT=79n
.MEAS TRAN V_ca3_f1 FIND V(net_19554) AT=79n
.MEAS TRAN V_ca2_f1 FIND V(net_19547) AT=79n
.MEAS TRAN V_ca1_f1 FIND V(net_19540) AT=79n
.MEAS TRAN V_ca0_f1 FIND V(net_19533) AT=79n

* Frame 1 Write '1' to (10, 5) (Cycle 8: 80-85ns)
.MEAS TRAN V_wl10_w1           FIND V(net_18747) AT=82.5n
.MEAS TRAN V_col5_w1           FIND V(net_19448) AT=82.5n
.MEAS TRAN V_r10c5_Q_after_w1  FIND V(Q_r10_c5)  AT=84.5n
.MEAS TRAN V_r10c5_QB_after_w1 FIND V(QB_r10_c5) AT=84.5n
.MEAS TRAN t_write1_flip TRIG V(CLK) VAL=0.9 FALL=8 TARG V(QB_r10_c5) VAL=1.62 RISE=1

* Frame 2 Write '0' to (3, 12) (Cycle 16: 160-165ns)
.MEAS TRAN V_wl3_w0            FIND V(net_18667) AT=162.5n
.MEAS TRAN V_col12_w0          FIND V(net_19483) AT=162.5n
.MEAS TRAN V_r3c12_Q_after_w0  FIND V(Q_r3_c12)  AT=164.5n
.MEAS TRAN V_r3c12_QB_after_w0 FIND V(QB_r3_c12) AT=164.5n
.MEAS TRAN t_write0_flip TRIG V(CLK) VAL=0.9 FALL=16 TARG V(Q_r3_c12) VAL=1.62 RISE=1

* Frame 3 Read from (10, 5) (Cycle 24: 240-245ns)
.MEAS TRAN V_sense_f3        FIND V(net_19600) AT=244n
.MEAS TRAN V_dl_read1        FIND V(net_19187) AT=244n
.MEAS TRAN V_dlb_read1       FIND V(net_19190) AT=244n
.MEAS TRAN V_dout_latched_f3 FIND V(DOUT)      AT=250n
.MEAS TRAN t_cq_read1        TRIG V(CLK) VAL=0.9 FALL=24 TARG V(net_19600) VAL=0.9 RISE=1 TD=239n

* Frame 4 Read from (3, 12) (Cycle 32: 320-325ns)
.MEAS TRAN V_sense_f4        FIND V(net_19600) AT=324n
.MEAS TRAN V_dl_read0        FIND V(net_19187) AT=324n
.MEAS TRAN V_dlb_read0       FIND V(net_19190) AT=324n
.MEAS TRAN V_dout_latched_f4 FIND V(DOUT)      AT=330n
.MEAS TRAN t_cq_read0        TRIG V(CLK) VAL=0.9 FALL=32 TARG V(net_19600) VAL=0.9 FALL=1 TD=319n

* Disturb & Power
.MEAS TRAN V_unselected_r10c4_Q FIND V(Q_r10_c4) AT=325n
.MEAS TRAN V_unselected_r9c5_QB FIND V(QB_r9_c5) AT=325n
.MEAS TRAN P_chip_avg AVG (-V(vdd)*I(VDDsrc)) FROM=5n TO=325n

.END
"""

out_deck = r"D:\Projects\Memory-IC-Design\spice\Top_layout_test.spi"
with open(out_deck, "w") as f:
    f.write(netlist)
    f.write(testbench)

print("Created clean Top_layout_test.spi successfully!")
