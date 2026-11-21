# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from java.awt.geom import Point2D
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
sch_tech = Technology.findTechnology("schematic")

# Let's create dummy_sch with 1 PMOS W=32 and 1 NMOS W=16
sch = Cell.newInst(lib, "test_par_sch{sch}")
sch.setTechnology(sch_tech)
p_tx = sch_tech.findNodeProto("Transistor")
w_proto = sch_tech.findArcProto("wire")
pin_proto = sch_tech.findNodeProto("Wire_Pin")

from com.sun.electric.database.variable import Variable

p0 = NodeInst.makeInstance(p_tx, ep, Point2D.Double(0.0, 10.0), 3.0, 3.0, sch, Orientation.IDENT, "p0")
n0 = NodeInst.makeInstance(p_tx, ep, Point2D.Double(0.0, -10.0), 3.0, 3.0, sch, Orientation.IDENT, "n0")
buf_sch = lib.findNodeProto("buffer{sch}")
nit = buf_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() == "pmos@5":
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            if "width" in v.getKey().getName().lower():
                p0.addVar(v.withObject(java.lang.Double(32.0)))
            elif "length" in v.getKey().getName().lower():
                p0.addVar(v.withObject(java.lang.Double(2.0)))
            elif "model" in v.getKey().getName().lower():
                p0.addVar(v.withObject("CMOSP"))
    elif n.getName() == "nmos@6":
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            if "width" in v.getKey().getName().lower():
                n0.addVar(v.withObject(java.lang.Double(16.0)))
            elif "length" in v.getKey().getName().lower():
                n0.addVar(v.withObject(java.lang.Double(2.0)))
            elif "model" in v.getKey().getName().lower():
                n0.addVar(v.withObject("CMOSN"))

pin_in = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-20.0, 0.0), 1.0, 1.0, sch, Orientation.IDENT, "pin_in")
pin_out = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(20.0, 0.0), 1.0, 1.0, sch, Orientation.IDENT, "pin_out")
pin_vdd = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(0.0, 20.0), 1.0, 1.0, sch, Orientation.IDENT, "pin_vdd")
pin_gnd = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(0.0, -20.0), 1.0, 1.0, sch, Orientation.IDENT, "pin_gnd")

ArcInst.makeInstance(w_proto, ep, pin_in.getOnlyPortInst(), p0.findPortInst("g"))
ArcInst.makeInstance(w_proto, ep, pin_in.getOnlyPortInst(), n0.findPortInst("g"))
ArcInst.makeInstance(w_proto, ep, pin_out.getOnlyPortInst(), p0.findPortInst("d"))
ArcInst.makeInstance(w_proto, ep, pin_out.getOnlyPortInst(), n0.findPortInst("d"))
ArcInst.makeInstance(w_proto, ep, pin_vdd.getOnlyPortInst(), p0.findPortInst("s"))
ArcInst.makeInstance(w_proto, ep, pin_gnd.getOnlyPortInst(), n0.findPortInst("s"))

Export.newInst(sch, pin_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
Export.newInst(sch, pin_out.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
Export.newInst(sch, pin_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
Export.newInst(sch, pin_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)

# Now create dummy_lay with 2 PMOS W=16 and 2 NMOS W=8 in parallel
lay = Cell.newInst(lib, "test_par_lay{lay}")
lay.setTechnology(mocmos)

pmos_proto = mocmos.findNodeProto("P-Transistor")
nmos_proto = mocmos.findNodeProto("N-Transistor")
m1_proto = mocmos.findArcProto("Metal-1")
poly_proto = mocmos.findArcProto("Polysilicon-1")
m1_pin = mocmos.findNodeProto("Metal-1-Pin")
poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")

p1 = NodeInst.makeInstance(pmos_proto, ep, Point2D.Double(0.0, 20.0), 22.0, 15.0, lay, Orientation.R, "p1")
p1.setPrimitiveNodeSize(16.0, 2.0, ep)
p2 = NodeInst.makeInstance(pmos_proto, ep, Point2D.Double(20.0, 20.0), 22.0, 15.0, lay, Orientation.R, "p2")
p2.setPrimitiveNodeSize(16.0, 2.0, ep)

n1 = NodeInst.makeInstance(nmos_proto, ep, Point2D.Double(0.0, -20.0), 22.0, 15.0, lay, Orientation.R, "n1")
n1.setPrimitiveNodeSize(8.0, 2.0, ep)
n2 = NodeInst.makeInstance(nmos_proto, ep, Point2D.Double(20.0, -20.0), 22.0, 15.0, lay, Orientation.R, "n2")
n2.setPrimitiveNodeSize(8.0, 2.0, ep)

pin_in_lay = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(-20.0, 0.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_in")
pin_out_lay = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(40.0, 0.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_out")
pin_vdd_lay = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(0.0, 40.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_vdd")
pin_gnd_lay = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(0.0, -40.0), 3.0, 3.0, lay, Orientation.IDENT, "pin_gnd")

ArcInst.makeInstance(poly_proto, ep, pin_in_lay.getOnlyPortInst(), p1.findPortInst("poly-left"))
ArcInst.makeInstance(poly_proto, ep, p1.findPortInst("poly-left"), n1.findPortInst("poly-right"))
ArcInst.makeInstance(poly_proto, ep, pin_in_lay.getOnlyPortInst(), p2.findPortInst("poly-left"))
ArcInst.makeInstance(poly_proto, ep, p2.findPortInst("poly-left"), n2.findPortInst("poly-right"))

ArcInst.makeInstance(m1_proto, ep, p1.findPortInst("diff-bottom"), pin_out_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, p2.findPortInst("diff-bottom"), pin_out_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, n1.findPortInst("diff-bottom"), pin_out_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, n2.findPortInst("diff-bottom"), pin_out_lay.getOnlyPortInst())

ArcInst.makeInstance(m1_proto, ep, p1.findPortInst("diff-top"), pin_vdd_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, p2.findPortInst("diff-top"), pin_vdd_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, n1.findPortInst("diff-top"), pin_gnd_lay.getOnlyPortInst())
ArcInst.makeInstance(m1_proto, ep, n2.findPortInst("diff-top"), pin_gnd_lay.getOnlyPortInst())

Export.newInst(lay, pin_in_lay.getOnlyPortInst(), "IN", PortCharacteristic.IN)
Export.newInst(lay, pin_out_lay.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
Export.newInst(lay, pin_vdd_lay.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
Export.newInst(lay, pin_gnd_lay.getOnlyPortInst(), "GND", PortCharacteristic.GND)

opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(sch, None, lay, None, opts)
print("NCC match (single W=32 in sch vs two W=16 in lay):", res.match())

sch.kill()
lay.kill()
java.lang.System.exit(0)
