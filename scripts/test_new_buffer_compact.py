# -*- coding: utf-8 -*-
# scripts/test_new_buffer_compact.py

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

# 1. Update buffer{sch} so Stage 4 has two inverters of size 16 (PMOS 16, NMOS 8) in parallel
buf_sch = lib.findNodeProto("buffer{sch}")
clear_cell(buf_sch)

wire_sch = sch_tech.findArcProto("wire")
pin_sch = sch_tech.findNodeProto("Wire_Pin")
tx_sch = sch_tech.findNodeProto("Transistor")

# Pins in schematic
p_in = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(-10.0, 0.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "pin_in")
p_out = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(90.0, 0.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "pin_out")
p_vdd = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(40.0, 30.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "pin_vdd")
p_gnd = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(40.0, -30.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "pin_gnd")

from com.sun.electric.database.variable import Variable
def add_tx_vars(inst, w, l, model):
    inst.addVar(Variable.newInst(Variable.findKey("ATTR_width"), java.lang.Double(w), None))
    inst.addVar(Variable.newInst(Variable.findKey("ATTR_length"), java.lang.Double(l), None))
    inst.addVar(Variable.newInst(Variable.findKey("SIM_spice_model"), model, None))

# 4 stages in schematic (Stage 4 has two parallel inverters):
# Stage 1: P=4, N=3 @ X=0
p_s1 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(0.0, 15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "pmos@0")
add_tx_vars(p_s1, 4.0, 2.0, "CMOSP")
n_s1 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(0.0, -15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "nmos@1")
add_tx_vars(n_s1, 3.0, 2.0, "CMOSN")

# Stage 2: P=8, N=4 @ X=20
p_s2 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(20.0, 15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "pmos@1")
add_tx_vars(p_s2, 8.0, 2.0, "CMOSP")
n_s2 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(20.0, -15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "nmos@2")
add_tx_vars(n_s2, 4.0, 2.0, "CMOSN")

# Stage 3: P=16, N=8 @ X=40
p_s3 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(40.0, 15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "pmos@4")
add_tx_vars(p_s3, 16.0, 2.0, "CMOSP")
n_s3 = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(40.0, -15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "nmos@5")
add_tx_vars(n_s3, 8.0, 2.0, "CMOSN")

# Stage 4A: P=16, N=8 @ X=60
p_s4a = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(60.0, 15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "pmos@5")
add_tx_vars(p_s4a, 16.0, 2.0, "CMOSP")
n_s4a = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(60.0, -15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "nmos@6")
add_tx_vars(n_s4a, 8.0, 2.0, "CMOSN")

# Stage 4B: P=16, N=8 @ X=80
p_s4b = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(80.0, 15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "pmos@6")
add_tx_vars(p_s4b, 16.0, 2.0, "CMOSP")
n_s4b = NodeInst.makeInstance(tx_sch, ep, Point2D.Double(80.0, -15.0), 3.0, 3.0, buf_sch, Orientation.IDENT, "nmos@7")
add_tx_vars(n_s4b, 8.0, 2.0, "CMOSN")

# Intermediate nodes
net1_pin = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(10.0, 0.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "net1")
net2_pin = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(30.0, 0.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "net2")
net3_pin = NodeInst.makeInstance(pin_sch, ep, Point2D.Double(50.0, 0.0), 1.0, 1.0, buf_sch, Orientation.IDENT, "net3")

# Wire Stage 1
ArcInst.makeInstance(wire_sch, ep, p_in.getOnlyPortInst(), p_s1.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, p_in.getOnlyPortInst(), n_s1.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, p_s1.findPortInst("d"), net1_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s1.findPortInst("d"), net1_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, p_s1.findPortInst("s"), p_vdd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s1.findPortInst("s"), p_gnd.getOnlyPortInst())

# Wire Stage 2
ArcInst.makeInstance(wire_sch, ep, net1_pin.getOnlyPortInst(), p_s2.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, net1_pin.getOnlyPortInst(), n_s2.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, p_s2.findPortInst("d"), net2_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s2.findPortInst("d"), net2_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, p_s2.findPortInst("s"), p_vdd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s2.findPortInst("s"), p_gnd.getOnlyPortInst())

# Wire Stage 3
ArcInst.makeInstance(wire_sch, ep, net2_pin.getOnlyPortInst(), p_s3.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, net2_pin.getOnlyPortInst(), n_s3.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, p_s3.findPortInst("d"), net3_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s3.findPortInst("d"), net3_pin.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, p_s3.findPortInst("s"), p_vdd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, n_s3.findPortInst("s"), p_gnd.getOnlyPortInst())

# Wire Stage 4A & 4B in parallel
for p_s4, n_s4 in [(p_s4a, n_s4a), (p_s4b, n_s4b)]:
    ArcInst.makeInstance(wire_sch, ep, net3_pin.getOnlyPortInst(), p_s4.findPortInst("g"))
    ArcInst.makeInstance(wire_sch, ep, net3_pin.getOnlyPortInst(), n_s4.findPortInst("g"))
    ArcInst.makeInstance(wire_sch, ep, p_s4.findPortInst("d"), p_out.getOnlyPortInst())
    ArcInst.makeInstance(wire_sch, ep, n_s4.findPortInst("d"), p_out.getOnlyPortInst())
    ArcInst.makeInstance(wire_sch, ep, p_s4.findPortInst("s"), p_vdd.getOnlyPortInst())
    ArcInst.makeInstance(wire_sch, ep, n_s4.findPortInst("s"), p_gnd.getOnlyPortInst())

Export.newInst(buf_sch, p_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
Export.newInst(buf_sch, p_out.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
Export.newInst(buf_sch, p_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
Export.newInst(buf_sch, p_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)

print("buffer{sch} updated with split Stage 4 (two inverters of size 16 in parallel).")

java.lang.System.exit(0)
