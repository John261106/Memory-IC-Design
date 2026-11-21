# -*- coding: utf-8 -*-
# scripts/update_top_sch_with_buffers.py

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

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
sch_tech = Technology.findTechnology("schematic")
wire_arc = sch_tech.findArcProto("wire")
wire_pin = sch_tech.findNodeProto("Wire_Pin")

p_inbuf = lib.findNodeProto("input_buffer{ic}")
p_outbuf = lib.findNodeProto("output_buffer{ic}")

print("=== Modifying Top{sch} to add input_buffer and output_buffer ===")

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

# Helper function for strictly Manhattan arcs
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

# 1. ADDR_IN Buffer
sreg = top_sch.findNode("8Bit_shi@0")
pin_addr = top_sch.findNode("pin@0")
kill_node_and_arcs(pin_addr)

# Create input_buffer for ADDR_IN at (-175.0, 80.0)
ib_addr = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-175.0, 80.0), 14.0, 8.0, top_sch, Orientation.IDENT, "in_buf_addr")
# Connect ib_addr.OUT (-168.0, 80.0) -> sreg.D (-149.0, 80.0)
make_wire(ib_addr.findPortInst("OUT"), sreg.findPortInst("D"), "ADDR_IN_int")

# New pin@0 for ADDR_IN export at (-195.0, 80.0)
pin_addr = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-195.0, 80.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@0")
Export.newInst(top_sch, pin_addr.getOnlyPortInst(), "ADDR_IN", PortCharacteristic.IN)
make_wire(pin_addr.getOnlyPortInst(), ib_addr.findPortInst("IN"), "ADDR_IN")

# Power stubs for ib_addr
p_v_addr = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, 88.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_addr = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-175.0, 72.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ib_addr.findPortInst("VDD"), p_v_addr.getOnlyPortInst(), "VDD")
make_wire(ib_addr.findPortInst("GND"), p_g_addr.getOnlyPortInst(), "GND")
print("  Added in_buf_addr at (-175.0, 80.0)")

# 2. CLK Buffer
pin_clk = top_sch.findNode("pin@18")
kill_node_and_arcs(pin_clk)

ctrl = top_sch.findNode("Control_@0")
# Reconnect ctrl.CLK with CLK_int
p_cclk = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-119.0, 24.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@18_int")
make_wire(ctrl.findPortInst("CLK"), p_cclk.getOnlyPortInst(), "CLK_int")

# Rename other CLK arcs to CLK_int
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getName() == "CLK":
        a.setName("CLK_int", ep)

# Create input_buffer for CLK at (-145.0, 24.0)
ib_clk = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-145.0, 24.0), 14.0, 8.0, top_sch, Orientation.IDENT, "in_buf_clk")
# Connect ib_clk.OUT (-138.0, 24.0) -> pin@18_int (-119.0, 24.0)
make_wire(ib_clk.findPortInst("OUT"), p_cclk.getOnlyPortInst(), "CLK_int")

# New pin@18 for CLK export at (-165.0, 24.0)
pin_clk = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-165.0, 24.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@18")
Export.newInst(top_sch, pin_clk.getOnlyPortInst(), "CLK", PortCharacteristic.IN)
make_wire(pin_clk.getOnlyPortInst(), ib_clk.findPortInst("IN"), "CLK")

p_v_clk = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-145.0, 32.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_clk = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-145.0, 16.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ib_clk.findPortInst("VDD"), p_v_clk.getOnlyPortInst(), "VDD")
make_wire(ib_clk.findPortInst("GND"), p_g_clk.getOnlyPortInst(), "GND")
print("  Added in_buf_clk at (-145.0, 24.0)")

# 3. CTRL Buffer
pin_ctrl = top_sch.findNode("pin@19")
kill_node_and_arcs(pin_ctrl)

# Create input_buffer for CTRL at (-145.0, 0.0)
ib_ctrl = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-145.0, 0.0), 14.0, 8.0, top_sch, Orientation.IDENT, "in_buf_ctrl")
# Connect ib_ctrl.OUT (-138.0, 0.0) -> (-109.0, 0.0) -> (-109.0, 15.0) ctrl.CTRL
p_ctrl_j1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-109.0, 0.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ib_ctrl.findPortInst("OUT"), p_ctrl_j1.getOnlyPortInst(), "CTRL_int")
make_wire(p_ctrl_j1.getOnlyPortInst(), ctrl.findPortInst("CTRL"), "CTRL_int")

# New pin@19 for CTRL export at (-165.0, 0.0)
pin_ctrl = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-165.0, 0.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@19")
Export.newInst(top_sch, pin_ctrl.getOnlyPortInst(), "CTRL", PortCharacteristic.IN)
make_wire(pin_ctrl.getOnlyPortInst(), ib_ctrl.findPortInst("IN"), "CTRL")

p_v_ctrl = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-145.0, 8.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_ctrl = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(-145.0, -8.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ib_ctrl.findPortInst("VDD"), p_v_ctrl.getOnlyPortInst(), "VDD")
make_wire(ib_ctrl.findPortInst("GND"), p_g_ctrl.getOnlyPortInst(), "GND")
print("  Added in_buf_ctrl at (-145.0, 0.0)")

# 4. DIN Buffer
wd = top_sch.findNode("Write_dr@0")
pin_din = top_sch.findNode("pin@385")
kill_node_and_arcs(pin_din)

# Create input_buffer for DIN at (195.0, 43.0)
ib_din = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(195.0, 43.0), 14.0, 8.0, top_sch, Orientation.IDENT, "in_buf_din")
# Connect ib_din.OUT (202.0, 43.0) -> wd.DATA (227.0, 43.0)
make_wire(ib_din.findPortInst("OUT"), wd.findPortInst("DATA"), "DIN_int")

# New pin@385 for DIN export at (175.0, 43.0)
pin_din = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(175.0, 43.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@385")
Export.newInst(top_sch, pin_din.getOnlyPortInst(), "DIN", PortCharacteristic.IN)
make_wire(pin_din.getOnlyPortInst(), ib_din.findPortInst("IN"), "DIN")

p_v_din = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(195.0, 51.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_din = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(195.0, 35.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ib_din.findPortInst("VDD"), p_v_din.getOnlyPortInst(), "VDD")
make_wire(ib_din.findPortInst("GND"), p_g_din.getOnlyPortInst(), "GND")
print("  Added in_buf_din at (195.0, 43.0)")

# 5. DOUT Buffer
dff0 = top_sch.findNode("D_flipfl@0")
pin_dout = top_sch.findNode("pin@391")
kill_node_and_arcs(pin_dout)

# Create output_buffer for DOUT at (380.0, 50.0)
ob_dout = NodeInst.makeInstance(p_outbuf, ep, Point2D.Double(380.0, 50.0), 14.0, 8.0, top_sch, Orientation.IDENT, "out_buf_dout")
# Connect dff0.Q (359.0, 50.0) -> ob_dout.IN (373.0, 50.0)
make_wire(dff0.findPortInst("Q"), ob_dout.findPortInst("IN"), "DOUT_int")

# New pin@391 for DOUT export at (405.0, 50.0)
pin_dout = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(405.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@391")
Export.newInst(top_sch, pin_dout.getOnlyPortInst(), "DOUT", PortCharacteristic.OUT)
make_wire(ob_dout.findPortInst("OUT"), pin_dout.getOnlyPortInst(), "DOUT")

# Connect power for ob_dout to existing top/bottom rails
p_v_dout = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(380.0, 65.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_dout = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(380.0, 35.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(ob_dout.findPortInst("VDD"), p_v_dout.getOnlyPortInst(), "VDD")
make_wire(ob_dout.findPortInst("GND"), p_g_dout.getOnlyPortInst(), "GND")
print("  Added out_buf_dout at (380.0, 50.0)")

# Manhattan check on Top{sch}
total_arcs = 0
non_m = 0
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    total_arcs += 1
    p_1 = a.getHeadPortInst().getCenter()
    p_2 = a.getTailPortInst().getCenter()
    dx = abs(p_1.getX() - p_2.getX())
    dy = abs(p_1.getY() - p_2.getY())
    if dx > 0.001 and dy > 0.001:
        non_m += 1
print("Top{sch} Manhattan Check: %d / %d arcs (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Top{sch} successfully updated with all 5 buffers and saved to " + jelib_path)
