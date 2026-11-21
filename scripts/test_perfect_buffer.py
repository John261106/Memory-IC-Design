# -*- coding: utf-8 -*-
# scripts/test_perfect_buffer.py
import java.lang.Double
from java.awt.geom import Point2D
from java.util import ArrayList

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

def make_manhattan_arc(arc_proto, ep, port1, port2, width=None):
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    arc = ArcInst.makeInstance(arc_proto, ep, port1, port2)
    if width is not None:
        arc.setLambdaBaseWidth(width)
    return arc

def clear_cell(cell):
    eit = cell.getExports()
    ek = []
    while eit.hasNext(): ek.append(eit.next())
    for e in ek: e.kill()

    ait = cell.getArcs()
    ak = []
    while ait.hasNext(): ak.append(ait.next())
    for a in ak: a.kill()

    nit = cell.getNodes()
    nk = []
    while nit.hasNext():
        n = nit.next()
        if "Facet-Center" not in n.getProto().getName():
            nk.append(n)
    for n in nk: n.kill()

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

sch_tech = Technology.findTechnology("schematic")

# 1. Update Schematic
print("=== Step 1: Updating buffer{sch} ===")
buf_sch = lib.findNodeProto("buffer{sch}")
wire_sch = sch_tech.findArcProto("wire")
tx_proto = sch_tech.findNodeProto("Transistor")

nmos1 = buf_sch.findNode("nmos@1")
pmos5 = buf_sch.findNode("pmos@5")
nmos6 = buf_sch.findNode("nmos@6")
pin_g_p = buf_sch.findNode("pin@28")
pin_g_n = buf_sch.findNode("pin@29")
pin_vdd = buf_sch.findNode("pin@38")
pin_gnd = buf_sch.findNode("pin@39")
pin_out = buf_sch.findNode("pin@46")

# Set nmos@1 to W=4.0
vit = nmos1.getVariables()
while vit.hasNext():
    v = vit.next()
    if "width" in v.getKey().getName().lower():
        nmos1.addVar(v.withObject(java.lang.Double(4.0)))

# Set pmos@5 to W=16.0
vit = pmos5.getVariables()
while vit.hasNext():
    v = vit.next()
    if "width" in v.getKey().getName().lower():
        pmos5.addVar(v.withObject(java.lang.Double(16.0)))

# Set nmos@6 to W=8.0
vit = nmos6.getVariables()
while vit.hasNext():
    v = vit.next()
    if "width" in v.getKey().getName().lower():
        nmos6.addVar(v.withObject(java.lang.Double(8.0)))

# Remove old parallel nodes if present
p6_old = buf_sch.findNode("pmos@6")
if p6_old: p6_old.kill()
n7_old = buf_sch.findNode("nmos@7")
if n7_old: n7_old.kill()

# Create pmos@6 and nmos@7
pmos6 = NodeInst.makeInstance(tx_proto, ep, Point2D.Double(pmos5.getAnchorCenterX() + 15.0, pmos5.getAnchorCenterY()),
                              pmos5.getXSize(), pmos5.getYSize(), buf_sch, Orientation.IDENT, "pmos@6")
pmos6.copyVarsFrom(pmos5)
pmos6.setPrimitiveFunction(pmos5.getFunction())

nmos7 = NodeInst.makeInstance(tx_proto, ep, Point2D.Double(nmos6.getAnchorCenterX() + 15.0, nmos6.getAnchorCenterY()),
                              nmos6.getXSize(), nmos6.getYSize(), buf_sch, Orientation.IDENT, "nmos@7")
nmos7.copyVarsFrom(nmos6)
nmos7.setPrimitiveFunction(nmos6.getFunction())

# Wire pmos@6
ArcInst.makeInstance(wire_sch, ep, pin_g_p.getOnlyPortInst(), pmos6.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, pmos6.findPortInst("d"), pin_vdd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, pmos6.findPortInst("s"), pin_out.getOnlyPortInst())

# Wire nmos@7
ArcInst.makeInstance(wire_sch, ep, pin_g_n.getOnlyPortInst(), nmos7.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, nmos7.findPortInst("s"), pin_gnd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, nmos7.findPortInst("d"), pin_out.getOnlyPortInst())
print("buffer{sch} successfully updated: Stage 1 (4/4), Stage 2 (8/4), Stage 3 (16/8), Stage 4 (16/8 || 16/8).")

# 2. Build Layout
print("\n=== Step 2: Building buffer{lay} ===")
cell = lib.findNodeProto("buffer{lay}")
if cell is None:
    cell = Cell.newInst(lib, "buffer{lay}")
cell.setTechnology(mocmos)
clear_cell(cell)

n_proto = mocmos.findNodeProto("N-Transistor")
p_proto = mocmos.findNodeProto("P-Transistor")

m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

n_well_node = mocmos.findNodeProto("N-Well-Node")
p_well_node = mocmos.findNodeProto("P-Well-Node")

m1_pin = mocmos.findNodeProto("Metal-1-Pin")
poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")

m1_wire = mocmos.findArcProto("Metal-1")
poly_wire = mocmos.findArcProto("Polysilicon-1")
n_act_wire = mocmos.findArcProto("N-Active")
p_act_wire = mocmos.findArcProto("P-Active")

Y_P = 14.0
Y_N = -12.0
Y_VDD = 28.0
Y_GND = -22.0

X_LEFT = 0.0
X_RIGHT = 120.0

# N-Well and P-Well coverage extending well past edges
nw = NodeInst.makeInstance(n_well_node, ep, Point2D.Double((X_LEFT + X_RIGHT)/2.0, 19.0),
                      (X_RIGHT - X_LEFT) + 16.0, 42.0, cell, Orientation.IDENT, None)
nw.setPrimitiveNodeSize((X_RIGHT - X_LEFT) + 16.0, 42.0, ep)

pw = NodeInst.makeInstance(p_well_node, ep, Point2D.Double((X_LEFT + X_RIGHT)/2.0, -18.0),
                      (X_RIGHT - X_LEFT) + 16.0, 32.0, cell, Orientation.IDENT, None)
pw.setPrimitiveNodeSize((X_RIGHT - X_LEFT) + 16.0, 32.0, ep)

vdd_pins = []
gnd_pins = []

# Left rails
p_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_LEFT, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
p_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_LEFT, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
vdd_pins.append(p_vdd_l)
gnd_pins.append(p_gnd_l)

# Well taps at X = 108.0
tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(108.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, None)
tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(108.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, None)
vdd_pins.append(tap_vdd)
gnd_pins.append(tap_gnd)

# Input contact at X = 4.0, Y = 0.0
con_in = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(4.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)

dx_std = 4.5

# --- Stage 1 ---
# Gate at X = 13.5, Source at 9.0, Drain at 18.0
x1 = 13.5
p1 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x1, Y_P), 22.0, 15.0, cell, Orientation.R, None)
p1.setPrimitiveNodeSize(4.0, 2.0, ep)
n1 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x1, Y_N), 22.0, 15.0, cell, Orientation.R, None)
n1.setPrimitiveNodeSize(4.0, 2.0, ep)

pin_g1 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x1, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(poly_wire, ep, p1.findPortInst("poly-left"), pin_g1.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g1.getOnlyPortInst(), n1.findPortInst("poly-right"))
make_manhattan_arc(poly_wire, ep, con_in.getOnlyPortInst(), pin_g1.getOnlyPortInst())

# Source 1 @ 9.0
c_p_s1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x1 - dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, c_p_s1.getOnlyPortInst(), p1.findPortInst("diff-top"))
pv_s1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x1 - dx_std, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_s1.getOnlyPortInst(), pv_s1.getOnlyPortInst())
vdd_pins.append(pv_s1)

c_n_s1 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x1 - dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, c_n_s1.getOnlyPortInst(), n1.findPortInst("diff-top"))
pg_s1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x1 - dx_std, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_n_s1.getOnlyPortInst(), pg_s1.getOnlyPortInst())
gnd_pins.append(pg_s1)

# Drain 1 @ 18.0
c_p_d1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x1 + dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, p1.findPortInst("diff-bottom"), c_p_d1.getOnlyPortInst())
c_n_d1 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x1 + dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, n1.findPortInst("diff-bottom"), c_n_d1.getOnlyPortInst())

pin_d1_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x1 + dx_std, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_d1.getOnlyPortInst(), pin_d1_m.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, pin_d1_m.getOnlyPortInst(), c_n_d1.getOnlyPortInst())

# Interconnect 1->2: contact at X = 25.0, Y = 0.0 (distance 7.0 from pin_d1_m -> no M1 notch!)
con_g2 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(25.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, pin_d1_m.getOnlyPortInst(), con_g2.getOnlyPortInst())

# --- Stage 2 ---
# Gate at X = 35.0, Source at 30.5, Drain at 39.5
x2 = 35.0
p2 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x2, Y_P), 22.0, 15.0, cell, Orientation.R, None)
p2.setPrimitiveNodeSize(8.0, 2.0, ep)
n2 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x2, Y_N), 22.0, 15.0, cell, Orientation.R, None)
n2.setPrimitiveNodeSize(4.0, 2.0, ep)

pin_g2 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x2, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(poly_wire, ep, p2.findPortInst("poly-left"), pin_g2.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g2.getOnlyPortInst(), n2.findPortInst("poly-right"))
make_manhattan_arc(poly_wire, ep, con_g2.getOnlyPortInst(), pin_g2.getOnlyPortInst())

# Source 2 @ 30.5
c_p_s2 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x2 - dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, c_p_s2.getOnlyPortInst(), p2.findPortInst("diff-top"))
pv_s2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x2 - dx_std, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_s2.getOnlyPortInst(), pv_s2.getOnlyPortInst())
vdd_pins.append(pv_s2)

c_n_s2 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x2 - dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, c_n_s2.getOnlyPortInst(), n2.findPortInst("diff-top"))
pg_s2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x2 - dx_std, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_n_s2.getOnlyPortInst(), pg_s2.getOnlyPortInst())
gnd_pins.append(pg_s2)

# Drain 2 @ 39.5
c_p_d2 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x2 + dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, p2.findPortInst("diff-bottom"), c_p_d2.getOnlyPortInst())
c_n_d2 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x2 + dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, n2.findPortInst("diff-bottom"), c_n_d2.getOnlyPortInst())

pin_d2_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x2 + dx_std, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_d2.getOnlyPortInst(), pin_d2_m.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, pin_d2_m.getOnlyPortInst(), c_n_d2.getOnlyPortInst())

# Interconnect 2->3: contact at X = 46.5, Y = 0.0 (distance 7.0 from pin_d2_m -> no M1 notch!)
con_g3 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(46.5, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, pin_d2_m.getOnlyPortInst(), con_g3.getOnlyPortInst())

# --- Stage 3 ---
# Gate at X = 56.5, Source at 52.0, Drain at 61.0
x3 = 56.5
p3 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x3, Y_P), 22.0, 15.0, cell, Orientation.R, None)
p3.setPrimitiveNodeSize(16.0, 2.0, ep)
n3 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x3, Y_N), 22.0, 15.0, cell, Orientation.R, None)
n3.setPrimitiveNodeSize(8.0, 2.0, ep)

pin_g3 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x3, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(poly_wire, ep, p3.findPortInst("poly-left"), pin_g3.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g3.getOnlyPortInst(), n3.findPortInst("poly-right"))
make_manhattan_arc(poly_wire, ep, con_g3.getOnlyPortInst(), pin_g3.getOnlyPortInst())

# Source 3 @ 52.0
c_p_s3 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x3 - dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, c_p_s3.getOnlyPortInst(), p3.findPortInst("diff-top"))
pv_s3 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x3 - dx_std, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_s3.getOnlyPortInst(), pv_s3.getOnlyPortInst())
vdd_pins.append(pv_s3)

c_n_s3 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x3 - dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, c_n_s3.getOnlyPortInst(), n3.findPortInst("diff-top"))
pg_s3 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x3 - dx_std, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_n_s3.getOnlyPortInst(), pg_s3.getOnlyPortInst())
gnd_pins.append(pg_s3)

# Drain 3 @ 61.0
c_p_d3 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x3 + dx_std, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(p_act_wire, ep, p3.findPortInst("diff-bottom"), c_p_d3.getOnlyPortInst())
c_n_d3 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x3 + dx_std, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
make_manhattan_arc(n_act_wire, ep, n3.findPortInst("diff-bottom"), c_n_d3.getOnlyPortInst())

pin_d3_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x3 + dx_std, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_d3.getOnlyPortInst(), pin_d3_m.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, pin_d3_m.getOnlyPortInst(), c_n_d3.getOnlyPortInst())

# Interconnect 3->4: contact at X = 68.0, Y = 0.0 (distance 7.0 from pin_d3_m -> no M1 notch!)
con_g4 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(68.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, pin_d3_m.getOnlyPortInst(), con_g4.getOnlyPortInst())

# --- Stage 4: Two Parallel Fingers with Shared Central Drain ---
# Pitch for shared drain: 5.5 lambda!
pitch_sh = 5.5
x_4a = 78.0
x_sh = x_4a + pitch_sh          # 83.5
x_4b = x_sh + pitch_sh          # 89.0
x_s4a = x_4a - pitch_sh         # 72.5
x_s4b = x_4b + pitch_sh         # 94.5

p4a = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x_4a, Y_P), 22.0, 15.0, cell, Orientation.R, None)
p4a.setPrimitiveNodeSize(16.0, 2.0, ep)
p4b = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x_4b, Y_P), 22.0, 15.0, cell, Orientation.R, None)
p4b.setPrimitiveNodeSize(16.0, 2.0, ep)

n4a = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_4a, Y_N), 22.0, 15.0, cell, Orientation.R, None)
n4a.setPrimitiveNodeSize(8.0, 2.0, ep)
n4b = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_4b, Y_N), 22.0, 15.0, cell, Orientation.R, None)
n4b.setPrimitiveNodeSize(8.0, 2.0, ep)

# Gate 4A & 4B
pin_g4a = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x_4a, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(poly_wire, ep, p4a.findPortInst("poly-left"), pin_g4a.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g4a.getOnlyPortInst(), n4a.findPortInst("poly-right"))

pin_g4b = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x_4b, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(poly_wire, ep, p4b.findPortInst("poly-left"), pin_g4b.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g4b.getOnlyPortInst(), n4b.findPortInst("poly-right"))

# Poly bus connecting con_g4 -> Gate 4A -> Gate 4B
make_manhattan_arc(poly_wire, ep, con_g4.getOnlyPortInst(), pin_g4a.getOnlyPortInst())
make_manhattan_arc(poly_wire, ep, pin_g4a.getOnlyPortInst(), pin_g4b.getOnlyPortInst())

# PMOS Stage 4 contacts
c_p_s4a = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_s4a, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
c_p_sh  = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_sh, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
c_p_s4b = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_s4b, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)

make_manhattan_arc(p_act_wire, ep, c_p_s4a.getOnlyPortInst(), p4a.findPortInst("diff-top"))
make_manhattan_arc(p_act_wire, ep, p4a.findPortInst("diff-bottom"), c_p_sh.getOnlyPortInst())
make_manhattan_arc(p_act_wire, ep, c_p_sh.getOnlyPortInst(), p4b.findPortInst("diff-top"))
make_manhattan_arc(p_act_wire, ep, p4b.findPortInst("diff-bottom"), c_p_s4b.getOnlyPortInst())

pv_s4a = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_s4a, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_s4a.getOnlyPortInst(), pv_s4a.getOnlyPortInst())
vdd_pins.append(pv_s4a)

pv_s4b = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_s4b, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_s4b.getOnlyPortInst(), pv_s4b.getOnlyPortInst())
vdd_pins.append(pv_s4b)

# NMOS Stage 4 contacts
c_n_s4a = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_s4a, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
c_n_sh  = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_sh, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
c_n_s4b = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_s4b, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)

make_manhattan_arc(n_act_wire, ep, c_n_s4a.getOnlyPortInst(), n4a.findPortInst("diff-top"))
make_manhattan_arc(n_act_wire, ep, n4a.findPortInst("diff-bottom"), c_n_sh.getOnlyPortInst())
make_manhattan_arc(n_act_wire, ep, c_n_sh.getOnlyPortInst(), n4b.findPortInst("diff-top"))
make_manhattan_arc(n_act_wire, ep, n4b.findPortInst("diff-bottom"), c_n_s4b.getOnlyPortInst())

pg_s4a = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_s4a, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_n_s4a.getOnlyPortInst(), pg_s4a.getOnlyPortInst())
gnd_pins.append(pg_s4a)

pg_s4b = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_s4b, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_n_s4b.getOnlyPortInst(), pg_s4b.getOnlyPortInst())
gnd_pins.append(pg_s4b)

# Shared Drain Output M1 Trunk at X = 83.5:
pin_out_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_sh, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, c_p_sh.getOnlyPortInst(), pin_out_m.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, pin_out_m.getOnlyPortInst(), c_n_sh.getOnlyPortInst())

# Output pin OUT at X = X_RIGHT
pin_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_RIGHT, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
make_manhattan_arc(m1_wire, ep, pin_out_m.getOnlyPortInst(), pin_out.getOnlyPortInst())

# Rightmost rail pins
p_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_RIGHT, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
p_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_RIGHT, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
vdd_pins.append(p_vdd_r)
gnd_pins.append(p_gnd_r)

# Stitch VDD & GND rails
vdd_pins.sort(key=lambda p: p.getAnchorCenterX())
for i in range(len(vdd_pins) - 1):
    make_manhattan_arc(m1_wire, ep, vdd_pins[i].getOnlyPortInst(), vdd_pins[i+1].getOnlyPortInst(), width=5.0)

gnd_pins.sort(key=lambda p: p.getAnchorCenterX())
for i in range(len(gnd_pins) - 1):
    make_manhattan_arc(m1_wire, ep, gnd_pins[i].getOnlyPortInst(), gnd_pins[i+1].getOnlyPortInst(), width=5.0)

# Exports
Export.newInst(cell, con_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
Export.newInst(cell, pin_out.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
Export.newInst(cell, p_vdd_r.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
Export.newInst(cell, p_gnd_r.getOnlyPortInst(), "GND", PortCharacteristic.GND)

# Clear all node names
nit = cell.getNodes()
while nit.hasNext():
    ni = nit.next()
    if ni.isUsernamed():
        ni.setName("")

print("Compact buffer{lay} built successfully: %f x %f" % (X_RIGHT - X_LEFT, Y_VDD - Y_GND))

# 3. Verification & Cleanup
print("\n=== Step 3: Verification & Cleanup ===")

# Remove Top_package if present
top_pkg = lib.findNodeProto("Top_package{sch}")
if top_pkg:
    print("Removing Top_package{sch} as requested by user...")
    top_pkg.kill()

# Manhattan
total_arcs = 0
non_m = 0
ait = cell.getArcs()
while ait.hasNext():
    a = ait.next()
    total_arcs += 1
    p_1 = a.getHeadPortInst().getCenter()
    p_2 = a.getTailPortInst().getCenter()
    if abs(p_1.getX() - p_2.getX()) > 0.001 and abs(p_1.getY() - p_2.getY()) > 0.001:
        non_m += 1
print("Manhattan Check: %d / %d (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

# Quick DRC on buffer{lay}
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break
q_err = logger.getNumErrors()
q_warn = logger.getNumWarnings()
print("buffer{lay} Quick DRC: %d errors, %d warnings" % (q_err, q_warn))
it = logger.getLogs()
while it.hasNext():
    log = it.next()
    print("  DRC: " + log.getMessageString())

# Hierarchical DRC on buffer{lay}
errs = ArrayList()
DRC.checkDRCHierarchically(prefs, cell, errs, None, mode, False)
h_err = len(errs)
print("buffer{lay} Hierarchical DRC: %d errors" % h_err)

# NCC with size checking
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(buf_sch, None, cell, None, opts)
print("NCC (checkSizes=True): match = %s" % res.match())

# Verify Top{lay}
print("\n--- Checking Top{lay} ---")
top_lay = lib.findNodeProto("Top{lay}")
logger_top = ErrorLogger()
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger_top, top_lay, None, None, None, None, prefs, mode, False])
        break
top_q_err = logger_top.getNumErrors()
top_q_warn = logger_top.getNumWarnings()
top_errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, top_errs, None, mode, False)
top_h_err = len(top_errs)
print("Top{lay} Quick DRC:        %d errors, %d warnings" % (top_q_err, top_q_warn))
print("Top{lay} Hierarchical DRC: %d errors" % top_h_err)

# Check all layout cells for usernamed nodes
print("\n--- Checking Node Names Across All Layout Cells ---")
from com.sun.electric.database.hierarchy import View
cit = lib.getCells()
total_unnamed = 0
total_usernamed = 0
while cit.hasNext():
    c = cit.next()
    if c.getView() == View.LAYOUT:
        nit = c.getNodes()
        c_un = 0
        c_user = 0
        while nit.hasNext():
            n = nit.next()
            if n.isUsernamed():
                c_user += 1
            else:
                c_un += 1
        total_unnamed += c_un
        total_usernamed += c_user
        if c_user > 0:
            print("  WARNING: %s has %d usernamed nodes!" % (c.getName(), c_user))
print("Total layout nodes checked: %d (unnamed/clean: %d, usernamed: %d)" % (
    total_unnamed + total_usernamed, total_unnamed, total_usernamed))

# 4. Save Library
print("\n=== Step 4: Saving Library ===")
Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Library successfully saved to: " + jelib_path)

