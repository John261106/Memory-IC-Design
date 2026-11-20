import subprocess

# Let's inspect DOUT and SENSE_OUT (net_19600)
testbench_check = """
.MEAS TRAN V_sense_during_read1 FIND V(net_19600) AT=244n
.MEAS TRAN V_dout_after_read1  FIND V(DOUT)       AT=250n
.MEAS TRAN V_sense_during_read0 FIND V(net_19600) AT=324n
.MEAS TRAN V_dout_after_read0  FIND V(DOUT)       AT=326n
"""

with open(r"D:\Projects\Memory-IC-Design\spice\Top_layout_test.spi", "r") as f:
    text = f.read()

# Replace .END with testbench_check + .END
text = text.replace(".END", testbench_check + "\n.END")
with open(r"D:\Projects\Memory-IC-Design\spice\Top_layout_test.spi", "w") as f:
    f.write(text)

subprocess.run([r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe", "-b", r"D:\Projects\Memory-IC-Design\spice\Top_layout_test.spi"])

with open(r"D:\Projects\Memory-IC-Design\spice\Top_layout_test.log", "r") as f:
    log = f.read()

for l in log.splitlines():
    if "during" in l.lower() or "after" in l.lower() or "v_dout" in l.lower():
        print(l)
