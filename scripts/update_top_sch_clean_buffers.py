# -*- coding: utf-8 -*-
# scripts/update_top_sch_clean_buffers.py

from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from java.util import ArrayList

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
top_lay = lib.findNodeProto("Top{lay}")
sch_tech = Technology.findTechnology("schematic")
wire_arc = sch_tech.findArcProto("wire")
wire_pin = sch_tech.findNodeProto("Wire_Pin")

p_inbuf = lib.findNodeProto("input_buffer{ic}")

def make_wire(p1, p2, net_name=None):
    dx = abs(p1.getCenter().getX() - p2.getCenter().getX())
    dy = abs(p1.getCenter().getY() - p2.getCenter().getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-straight arc attempted: (%.1f, %.1f) to (%.1f, %.1f)" % (
            p1.getCenter().getX(), p1.getCenter().getY(), p2.getCenter().getX(), p2.getCenter().getY()))
    a = ArcInst.makeInstance(wire_arc, ep, p1, p2)
    if net_name:
        a.setName(net_name, ep)
    return a

def kill_node_and_arcs(node):
    if node is None: return
    arcs_to_kill = []
    ait = top_sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        if a.getHeadPortInst().getNodeInst() == node or a.getTailPortInst().getNodeInst() == node:
            arcs_to_kill.append(a)
    for a in arcs_to_kill:
        a.kill()
    node.kill()

print("=== Cleaning up Top{sch} West region (3Bit_counter, in_buf_clk, in_buf_ctrl, Control_logic) ===")

# Identify nodes to remove and rebuild
ib_clk = top_sch.findNode("in_buf_clk")
ib_ctrl = top_sch.findNode("in_buf_ctrl")
pin_clk_exp = top_sch.findNode("pin@18")
pin_ctrl_exp = top_sch.findNode("pin@19")

# Also find intermediate pins around clk and ctrl
# Let's inspect arcs connected to in_buf_clk and in_buf_ctrl
kill_node_and_arcs(ib_clk)
kill_node_and_arcs(ib_ctrl)
kill_node_and_arcs(pin_clk_exp)
kill_node_and_arcs(pin_ctrl_exp)

# Clean up any leftover dangling pins from previous CLK_int and CTRL_int wiring
for pnm in ["pin@405", "pin@406", "pin@407", "pin@408", "pin@409", "pin@410", "pin@1", "pin@15"]:
    n = top_sch.findNode(pnm)
    if n:
        kill_node_and_arcs(n)

# Let's also check if 8Bit_shi@0.CLK and 3Bit_cou@0.CLK have any remaining arcs
def clean_port_arcs(node_name, port_name):
    n = top_sch.findNode(node_name)
    pi = n.findPortInst(port_name)
    arcs = []
    ait = top_sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        if a.getHeadPortInst() == pi or a.getTailPortInst() == pi:
            arcs.append(a)
    for a in arcs:
        a.kill()

clean_port_arcs("8Bit_shi@0", "CLK")
clean_port_arcs("3Bit_cou@0", "CLK")
clean_port_arcs("Control_@0", "CLK")
clean_port_arcs("Control_@0", "CTRL")

# Now rebuild with pristine layout:
# 1. in_buf_clk at (-175.0, 42.0)
# Bounds: [-183.0, -167.0] x [37.0, 47.0]
# IN is at (-182.0, 42.0)
# OUT is at (-168.0, 42.0)
# VDD is at (-175.0, 46.0)
# GND is at (-175.0, 38.0)
new_ib_clk = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-175.0, 42.0), 16.0, 10.0, top_sch, Orientation.IDENT, "in_buf_clk")

# CLK Export Pin at (-195.0, 42.0)
pin_clk = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-195.0, 42.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_in")
Export.newInst(top_sch, pin_clk.getOnlyPortInst(), "CLK", PortCharacteristic.IN)
make_wire(pin_clk.getOnlyPortInst(), new_ib_clk.findPortInst("IN"), "CLK")

# in_buf_clk power pins
pin_clk_v = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_v")
make_wire(new_ib_clk.findPortInst("VDD"), pin_clk_v.getOnlyPortInst(), "VDD")

pin_clk_g = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, 34.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_g")
make_wire(new_ib_clk.findPortInst("GND"), pin_clk_g.getOnlyPortInst(), "GND")

# CLK_int distribution from new_ib_clk.OUT (-168.0, 42.0)
# Route horizontally to (-120.0, 42.0)
pin_clk_j1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-120.0, 42.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_j1")
make_wire(new_ib_clk.findPortInst("OUT"), pin_clk_j1.getOnlyPortInst(), "CLK_int")

# Branch 1: UP to 8Bit_shi@0.CLK (-142.0, 68.0)
# from (-120.0, 42.0) up to (-120.0, 62.0), left to (-142.0, 62.0), up to (-142.0, 68.0)
sreg = top_sch.findNode("8Bit_shi@0")
pin_clk_s1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-120.0, 62.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_s1")
pin_clk_s2 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-142.0, 62.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_s2")
make_wire(pin_clk_j1.getOnlyPortInst(), pin_clk_s1.getOnlyPortInst(), "CLK_int")
make_wire(pin_clk_s1.getOnlyPortInst(), pin_clk_s2.getOnlyPortInst(), "CLK_int")
make_wire(pin_clk_s2.getOnlyPortInst(), sreg.findPortInst("CLK"), "CLK_int")

# Branch 2: to Control_@0.CLK (-109.0, 24.0)
# from (-120.0, 42.0) down to (-120.0, 24.0), then right to (-109.0, 24.0)
ctrl = top_sch.findNode("Control_@0")
pin_clk_c1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-120.0, 24.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_c1")
make_wire(pin_clk_j1.getOnlyPortInst(), pin_clk_c1.getOnlyPortInst(), "CLK_int")
make_wire(pin_clk_c1.getOnlyPortInst(), ctrl.findPortInst("CLK"), "CLK_int")

# Branch 3: to 3Bit_cou@0.CLK (-144.0, 13.0)
# from (-120.0, 24.0) down to (-120.0, 7.0), left to (-144.0, 7.0), up to (-144.0, 13.0)
cnt = top_sch.findNode("3Bit_cou@0")
pin_clk_cnt1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-120.0, 7.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_cnt1")
pin_clk_cnt2 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-144.0, 7.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_clk_cnt2")
make_wire(pin_clk_c1.getOnlyPortInst(), pin_clk_cnt1.getOnlyPortInst(), "CLK_int")
make_wire(pin_clk_cnt1.getOnlyPortInst(), pin_clk_cnt2.getOnlyPortInst(), "CLK_int")
make_wire(pin_clk_cnt2.getOnlyPortInst(), cnt.findPortInst("CLK"), "CLK_int")


# 2. in_buf_ctrl at (-175.0, -8.0)
# Bounds: [-183.0, -167.0] x [-13.0, -3.0]
# IN is at (-182.0, -8.0)
# OUT is at (-168.0, -8.0)
# VDD is at (-175.0, -4.0)
# GND is at (-175.0, -12.0)
new_ib_ctrl = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-175.0, -8.0), 16.0, 10.0, top_sch, Orientation.IDENT, "in_buf_ctrl")

# CTRL Export Pin at (-195.0, -8.0)
pin_ctrl = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-195.0, -8.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_ctrl_in")
Export.newInst(top_sch, pin_ctrl.getOnlyPortInst(), "CTRL", PortCharacteristic.IN)
make_wire(pin_ctrl.getOnlyPortInst(), new_ib_ctrl.findPortInst("IN"), "CTRL")

# in_buf_ctrl power pins
pin_ctrl_v = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, 0.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_ctrl_v")
make_wire(new_ib_ctrl.findPortInst("VDD"), pin_ctrl_v.getOnlyPortInst(), "VDD")

pin_ctrl_g = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, -16.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_ctrl_g")
make_wire(new_ib_ctrl.findPortInst("GND"), pin_ctrl_g.getOnlyPortInst(), "GND")

# CTRL_int route: from (-168.0, -8.0) to (-109.0, -8.0), then up to (-109.0, 15.0) at Control_@0.CTRL
pin_ctrl_j1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-109.0, -8.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_ctrl_j1")
make_wire(new_ib_ctrl.findPortInst("OUT"), pin_ctrl_j1.getOnlyPortInst(), "CTRL_int")
make_wire(pin_ctrl_j1.getOnlyPortInst(), ctrl.findPortInst("CTRL"), "CTRL_int")


# 3. Export Global Bitlines (GBL and GBLB)
pin_dl = top_sch.findNode("pin@387")
pin_dlb = top_sch.findNode("pin@388")

eit = top_sch.getExports()
existing_exports = []
while eit.hasNext():
    existing_exports.append(eit.next().getName())

if "GBL" not in existing_exports:
    Export.newInst(top_sch, pin_dl.getOnlyPortInst(), "GBL", PortCharacteristic.BIDIR)
    print("Exported GBL on Top{sch}")

if "GBLB" not in existing_exports:
    Export.newInst(top_sch, pin_dlb.getOnlyPortInst(), "GBLB", PortCharacteristic.BIDIR)
    print("Exported GBLB on Top{sch}")

# Verify Manhattan check on Top{sch}
total_arcs = 0
non_m = 0
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    total_arcs += 1
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        non_m += 1
print("Top{sch} Manhattan Check: %d / %d perpendicular (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

# Save Top{sch}
Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Saved Top{sch} to %s" % jelib_path)
