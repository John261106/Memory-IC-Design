# -*- coding: utf-8 -*-
# scripts/rewire_top_output_stage.py

from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
top_lay = lib.findNodeProto("Top{lay}")
sch_tech = Technology.findTechnology("schematic")
wire_arc = sch_tech.findArcProto("wire")
wire_pin = sch_tech.findNodeProto("Wire_Pin")

sa   = top_sch.findNode("Sense_am@0")
not0 = top_sch.findNode("Not@0")
dff0 = top_sch.findNode("D_flipfl@0")

pin_dout = top_sch.findNode("pin@391")
pin_ren_old = top_sch.findNode("pin_ren_not")
pin_vdd_old = top_sch.findNode("pin_vdd_out")
pin_gnd_old = top_sch.findNode("pin_gnd_out")

print("=== Found target nodes in Top{sch} ===")
print("Sense_am@0 at (%.1f, %.1f)" % (sa.getAnchorCenterX(), sa.getAnchorCenterY()))
print("Not@0 at (%.1f, %.1f)" % (not0.getAnchorCenterX(), not0.getAnchorCenterY()))
print("D_flipfl@0 at (%.1f, %.1f)" % (dff0.getAnchorCenterX(), dff0.getAnchorCenterY()))

# Step 1: Identify and kill the messy arcs connecting these nodes
arcs_to_kill = []
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst().getNodeInst()
    t = a.getTailPortInst().getNodeInst()
    name = a.getName()
    
    # 1. SENSE_OUT arc: sa.SENSE <-> dff0.D
    if (h == sa and t == dff0) or (h == dff0 and t == sa):
        arcs_to_kill.append(a)
    # 2. READ_CLK arc: not0.OUT <-> dff0.CLK
    elif (h == not0 and t == dff0) or (h == dff0 and t == not0):
        arcs_to_kill.append(a)
    # 3. DOUT arc: dff0.Q <-> pin_dout
    elif (h == dff0 and t == pin_dout) or (h == pin_dout and t == dff0):
        arcs_to_kill.append(a)
    # 4. Old VDD arcs from pin_vdd_old to not0 / dff0
    elif (h == pin_vdd_old or t == pin_vdd_old):
        arcs_to_kill.append(a)
    # 5. Old GND arcs from pin_gnd_old to not0 / dff0
    elif (h == pin_gnd_old or t == pin_gnd_old):
        arcs_to_kill.append(a)
    # 6. Old READ_EN arc to not0.IN
    elif (h == pin_ren_old or t == pin_ren_old):
        arcs_to_kill.append(a)

print("Killing %d messy arcs..." % len(arcs_to_kill))
for a in arcs_to_kill:
    print("  Killing arc: '%s' between %s and %s" % (
        a.getName(), a.getHeadPortInst().getNodeInst().getName(), a.getTailPortInst().getNodeInst().getName()))
    a.kill()

from com.sun.electric.database.prototype import PortCharacteristic

# Kill old intermediate pin nodes and pin_dout
if pin_vdd_old: pin_vdd_old.kill()
if pin_gnd_old: pin_gnd_old.kill()
if pin_ren_old: pin_ren_old.kill()
if pin_dout:    pin_dout.kill()

# Step 2: Create new pin_dout at (375.0, 50.0) cleanly to the right of D_flipflop
pin_dout = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(375.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin@391")
Export.newInst(top_sch, pin_dout.getOnlyPortInst(), "DOUT", PortCharacteristic.OUT)
print("Created pin@391 (DOUT export) at (375.0, 50.0)")

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

# Step 3: Connect DOUT: dff0.Q (359.0, 50.0) -> pin_dout (375.0, 50.0)
print("\n--- Connecting DOUT ---")
make_wire(dff0.findPortInst("Q"), pin_dout.getOnlyPortInst(), "DOUT")

# Step 4: Connect VDD rail
print("--- Connecting VDD Rail ---")
# Not@0.VDD is at (320.0, 57.0), D_flipfl@0.VDD is at (350.0, 57.0)
p_v_not = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(320.0, 65.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_v_dff = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(350.0, 65.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(not0.findPortInst("VDD"), p_v_not.getOnlyPortInst(), "VDD")
make_wire(dff0.findPortInst("VDD"), p_v_dff.getOnlyPortInst(), "VDD")
make_wire(p_v_not.getOnlyPortInst(), p_v_dff.getOnlyPortInst(), "VDD")

# Step 5: Connect GND rail
print("--- Connecting GND Rail ---")
# Not@0.GND is at (320.0, 43.0), D_flipfl@0.GND is at (352.0, 43.0)
p_g_not = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(320.0, 35.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_g_dff = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(352.0, 35.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
make_wire(not0.findPortInst("GND"), p_g_not.getOnlyPortInst(), "GND")
make_wire(dff0.findPortInst("GND"), p_g_dff.getOnlyPortInst(), "GND")
make_wire(p_g_not.getOnlyPortInst(), p_g_dff.getOnlyPortInst(), "GND")

# Step 6: Connect READ_EN to Not@0.IN
print("--- Connecting READ_EN to Not@0.IN ---")
# Not@0.IN is at (311.0, 50.0). We route left to (308.0, 50.0) then up to (308.0, 58.0)
p_ren_corner = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(308.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_ren_top    = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(308.0, 58.0), 1.0, 1.0, top_sch, Orientation.IDENT, "pin_ren_not")
make_wire(not0.findPortInst("IN"), p_ren_corner.getOnlyPortInst(), "READ_EN")
make_wire(p_ren_corner.getOnlyPortInst(), p_ren_top.getOnlyPortInst(), "READ_EN")

# Step 7: Connect SENSE_OUT (Sense_am@0.SENSE -> D_flipfl@0.D) around Not@0
print("--- Connecting SENSE_OUT ---")
# Sense_am@0.SENSE is at (287.0, 43.0). D_flipfl@0.D is at (341.0, 50.0).
# Route: (287, 43) -> (287, 39) -> (338, 39) -> (338, 50) -> (341, 50)
p_so1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(287.0, 39.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_so2 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(338.0, 39.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_so3 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(338.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)

make_wire(sa.findPortInst("SENSE"), p_so1.getOnlyPortInst(), "SENSE_OUT")
make_wire(p_so1.getOnlyPortInst(), p_so2.getOnlyPortInst(), "SENSE_OUT")
make_wire(p_so2.getOnlyPortInst(), p_so3.getOnlyPortInst(), "SENSE_OUT")
make_wire(p_so3.getOnlyPortInst(), dff0.findPortInst("D"), "SENSE_OUT")

# Step 8: Connect READ_CLK (Not@0.OUT -> D_flipfl@0.CLK)
print("--- Connecting READ_CLK ---")
# Not@0.OUT is at (329.0, 50.0). D_flipfl@0.CLK is at (347.0, 43.0).
# Route: (329, 50) -> (334, 50) -> (334, 43) -> (347, 43)
p_clk1 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(334.0, 50.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)
p_clk2 = NodeInst.makeInstance(wire_pin, ep, Point2D.Double(334.0, 43.0), 1.0, 1.0, top_sch, Orientation.IDENT, None)

make_wire(not0.findPortInst("OUT"), p_clk1.getOnlyPortInst(), "READ_CLK")
make_wire(p_clk1.getOnlyPortInst(), p_clk2.getOnlyPortInst(), "READ_CLK")
make_wire(p_clk2.getOnlyPortInst(), dff0.findPortInst("CLK"), "READ_CLK")

print("\n=== All wires successfully routed with 100% straight Manhattan lines! ===")

# Step 9: Verify Manhattan Arcs in Top{sch}
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
        print("  WARNING Non-Manhattan Arc: %s from (%.1f, %.1f) to (%.1f, %.1f)" % (
            a.getName(), p_1.getX(), p_1.getY(), p_2.getX(), p_2.getY()))

print("Top{sch} Manhattan Check: %d / %d arcs (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

# Step 10: Run NCC between Top{sch} and Top{lay}
print("\n--- Running Hierarchical NCC on Top ---")
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print("Top NCC (checkSizes=True): match = %s" % res.match())
if not res.match():
    raise AssertionError("NCC Failed after rewiring!")

# Step 11: Save library
print("\n=== Step 11: Saving Library ===")
Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Library successfully saved to: " + jelib_path)
