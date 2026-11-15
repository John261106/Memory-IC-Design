# scripts/test_counter_ncc.py
import java.lang.Double
from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

sch = lib.findNodeProto("3Bit_counter{sch}")
dff_lay = lib.findNodeProto("D_flipflop{lay}")

# Create test layout
lay = Cell.makeInstance(lib, "3Bit_counter{lay}")
lay.setTechnology(mocmos)

n_proto = mocmos.findNodeProto("N-Transistor")
p_proto = mocmos.findNodeProto("P-Transistor")
m1_pin = mocmos.findNodeProto("Metal-1-Pin")
m1_wire = mocmos.findArcProto("Metal-1")

# Instantiate 3 DFFs
dff0 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, 100.0), 287.0, 56.0, lay, Orientation.IDENT, "D_flipfl@3")
dff1 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, 200.0), 287.0, 56.0, lay, Orientation.IDENT, "D_flipfl@4")
dff2 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, 300.0), 287.0, 56.0, lay, Orientation.IDENT, "D_flipfl@5")

# Power & GND pins
pin_vdd = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(0.0, 500.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_vdd")
pin_gnd = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(0.0, -100.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_gnd")
pin_clk = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-50.0, 200.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_clk")
pin_count7 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(500.0, 200.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_count7")

Export.newInst(lay, pin_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
Export.newInst(lay, pin_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)
Export.newInst(lay, pin_clk.getOnlyPortInst(), "CLK", PortCharacteristic.IN)
Export.newInst(lay, pin_count7.getOnlyPortInst(), "COUNT_7", PortCharacteristic.OUT)

# Connect DFF power & clk
for dff in [dff0, dff1, dff2]:
    ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), dff.findPortInst("VDD"))
    ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), dff.findPortInst("GND"))
    ArcInst.makeInstance(m1_wire, ep, pin_clk.getOnlyPortInst(), dff.findPortInst("CLK"))

# Create 14 PMOS and 14 NMOS
p_widths = [8.0, 8.0, 8.0, 4.0, 4.0, 8.0, 4.0, 4.0, 4.0, 12.0, 8.0, 8.0, 8.0, 8.0]
n_widths = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 6.0, 6.0, 6.0, 6.0, 4.0, 4.0, 4.0, 4.0]

p_nodes = {}
n_nodes = {}
for i in range(14):
    p_nodes[i] = NodeInst.makeInstance(p_proto, ep, Point2D.Double(i * 30.0, 400.0), 2.0, p_widths[i], lay, Orientation.IDENT, "pmos@%d" % i)
    n_nodes[i] = NodeInst.makeInstance(n_proto, ep, Point2D.Double(i * 30.0, 450.0), 2.0, n_widths[i], lay, Orientation.IDENT, "nmos@%d" % i)

# Helper pins for internal nets
def make_net_pin(name, x, y):
    return NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, y), 3.0, 3.0, lay, Orientation.IDENT, name)

# Signal nets:
# C0 = dff0[Q]
# C1 = dff1[Q]
# C2 = dff2[Q]
p_c0 = dff0.findPortInst("Q")
p_c1 = dff1.findPortInst("Q")
p_c2 = dff2.findPortInst("Q")

# C0B = Inverter 0 output -> connects to dff0[D]
pin_c0b = make_net_pin("c0b", 50.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_c0b.getOnlyPortInst(), dff0.findPortInst("D"))
ArcInst.makeInstance(m1_wire, ep, pin_c0b.getOnlyPortInst(), p_nodes[0].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c0b.getOnlyPortInst(), n_nodes[0].findPortInst("diff-top"))

# Inverter 0 input: C0
ArcInst.makeInstance(m1_wire, ep, p_c0, p_nodes[0].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c0, n_nodes[0].findPortInst("poly-left"))
# Inverter 0 power:
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[0].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[0].findPortInst("diff-bottom"))

# Inverter 1: C1 -> C1B
pin_c1b = make_net_pin("c1b", 80.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_c1b.getOnlyPortInst(), p_nodes[1].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c1b.getOnlyPortInst(), n_nodes[1].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, p_c1, p_nodes[1].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c1, n_nodes[1].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[1].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[1].findPortInst("diff-bottom"))

# Inverter 2: C2 -> C2B
pin_c2b = make_net_pin("c2b", 110.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_c2b.getOnlyPortInst(), p_nodes[2].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c2b.getOnlyPortInst(), n_nodes[2].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, p_c2, p_nodes[2].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c2, n_nodes[2].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[2].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[2].findPortInst("diff-bottom"))

# AND2: NAND2 (pmos@3,4, nmos@3,4) + Inverter (pmos@5, nmos@5)
# NAND2 output: C01B
pin_c01b = make_net_pin("c01b", 140.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), p_nodes[3].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), p_nodes[4].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), n_nodes[3].findPortInst("diff-top"))

# pmos@3,4 to VDD
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[3].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[4].findPortInst("diff-bottom"))

# NAND2 inputs: C0 to p3,n3; C1 to p4,n4
ArcInst.makeInstance(m1_wire, ep, p_c0, p_nodes[3].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c0, n_nodes[3].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c1, p_nodes[4].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c1, n_nodes[4].findPortInst("poly-left"))

# nmos@3,4 series: n3 bottom to n4 top; n4 bottom to GND
ArcInst.makeInstance(m1_wire, ep, n_nodes[3].findPortInst("diff-bottom"), n_nodes[4].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[4].findPortInst("diff-bottom"))

# Inverter (pmos@5, nmos@5): input C01B, output C01
pin_c01 = make_net_pin("c01", 170.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), p_nodes[5].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), n_nodes[5].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_c01.getOnlyPortInst(), p_nodes[5].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c01.getOnlyPortInst(), n_nodes[5].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[5].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[5].findPortInst("diff-bottom"))

# AND3: NAND3 (pmos@6,7,8, nmos@6,7,8) + Output Inverter (pmos@9, nmos@9)
pin_count7b = make_net_pin("count7b", 220.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), p_nodes[6].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), p_nodes[7].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), p_nodes[8].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), n_nodes[6].findPortInst("diff-top"))

# pmos@6,7,8 to VDD
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[6].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[7].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[8].findPortInst("diff-bottom"))

# NAND3 inputs: C0 to p6,n6; C1 to p7,n7; C2 to p8,n8
ArcInst.makeInstance(m1_wire, ep, p_c0, p_nodes[6].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c0, n_nodes[6].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c1, p_nodes[7].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c1, n_nodes[7].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c2, p_nodes[8].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c2, n_nodes[8].findPortInst("poly-left"))

# nmos@6,7,8 series: n6 bottom to n7 top, n7 bottom to n8 top, n8 bottom to GND
ArcInst.makeInstance(m1_wire, ep, n_nodes[6].findPortInst("diff-bottom"), n_nodes[7].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, n_nodes[7].findPortInst("diff-bottom"), n_nodes[8].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[8].findPortInst("diff-bottom"))

# Output Inverter (pmos@9, nmos@9): input COUNT_7B, output pin_count7
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), p_nodes[9].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_count7b.getOnlyPortInst(), n_nodes[9].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_count7.getOnlyPortInst(), p_nodes[9].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_count7.getOnlyPortInst(), n_nodes[9].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_vdd.getOnlyPortInst(), p_nodes[9].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_gnd.getOnlyPortInst(), n_nodes[9].findPortInst("diff-bottom"))

# XOR1: TG1 (pmos@10, nmos@10) + TG2 (pmos@11, nmos@11) -> output D1
# D1 connects to dff1[D]
pin_d1 = make_net_pin("d1", 260.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_d1.getOnlyPortInst(), dff1.findPortInst("D"))

# TG1: input C1, gates C0/C0B, output D1
ArcInst.makeInstance(m1_wire, ep, p_c1, p_nodes[10].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, p_c1, n_nodes[10].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_d1.getOnlyPortInst(), p_nodes[10].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_d1.getOnlyPortInst(), n_nodes[10].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, p_c0, p_nodes[10].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_c0b.getOnlyPortInst(), n_nodes[10].findPortInst("poly-left"))

# TG2: input C1B, gates C0B/C0, output D1
ArcInst.makeInstance(m1_wire, ep, pin_c1b.getOnlyPortInst(), p_nodes[11].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c1b.getOnlyPortInst(), n_nodes[11].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_d1.getOnlyPortInst(), p_nodes[11].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_d1.getOnlyPortInst(), n_nodes[11].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_c0b.getOnlyPortInst(), p_nodes[11].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, p_c0, n_nodes[11].findPortInst("poly-left"))

# XOR2: TG3 (pmos@12, nmos@12) + TG4 (pmos@13, nmos@13) -> output D2
# D2 connects to dff2[D]
pin_d2 = make_net_pin("d2", 300.0, 350.0)
ArcInst.makeInstance(m1_wire, ep, pin_d2.getOnlyPortInst(), dff2.findPortInst("D"))

# TG3: input C2, gates C01/C01B, output D2
ArcInst.makeInstance(m1_wire, ep, p_c2, p_nodes[12].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, p_c2, n_nodes[12].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_d2.getOnlyPortInst(), p_nodes[12].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_d2.getOnlyPortInst(), n_nodes[12].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_c01.getOnlyPortInst(), p_nodes[12].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), n_nodes[12].findPortInst("poly-left"))

# TG4: input C2B, gates C01B/C01, output D2
ArcInst.makeInstance(m1_wire, ep, pin_c2b.getOnlyPortInst(), p_nodes[13].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_c2b.getOnlyPortInst(), n_nodes[13].findPortInst("diff-top"))
ArcInst.makeInstance(m1_wire, ep, pin_d2.getOnlyPortInst(), p_nodes[13].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_d2.getOnlyPortInst(), n_nodes[13].findPortInst("diff-bottom"))
ArcInst.makeInstance(m1_wire, ep, pin_c01b.getOnlyPortInst(), p_nodes[13].findPortInst("poly-left"))
ArcInst.makeInstance(m1_wire, ep, pin_c01.getOnlyPortInst(), n_nodes[13].findPortInst("poly-left"))

# Run NCC!
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(sch, None, lay, None, opts)
print("NCC Comparison Result: match = %s" % res.match())

# Clean up test cell
lay.kill()
