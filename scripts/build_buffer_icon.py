# -*- coding: utf-8 -*-
# scripts/build_buffer_icon.py

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from java.awt.geom import Point2D
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch_tech = Technology.findTechnology("schematic")
generic_tech = Technology.findTechnology("generic")

from com.sun.electric.util.math import Orientation

def build_buffer_icon():
    ic = lib.findNodeProto("buffer{ic}")
    if ic is None:
        ic = Cell.newInst(lib, "buffer{ic}")
    ic.setTechnology(sch_tech)

    # Clear cell
    eit = ic.getExports()
    ek = []
    while eit.hasNext(): ek.append(eit.next())
    for e in ek: e.kill()

    ait = ic.getArcs()
    ak = []
    while ait.hasNext(): ak.append(ait.next())
    for a in ak: a.kill()

    nit = ic.getNodes()
    nk = []
    while nit.hasNext():
        n = nit.next()
        if "Facet-Center" not in n.getProto().getName():
            nk.append(n)
    for n in nk: n.kill()

    # Create pins
    bus_pin = sch_tech.findNodeProto("Bus_Pin")
    pin_in  = NodeInst.makeInstance(bus_pin, ep, Point2D.Double(-6.0, 0.0), 2.0, 2.0, ic, Orientation.IDENT, None)
    pin_out = NodeInst.makeInstance(bus_pin, ep, Point2D.Double(6.0, 0.0), 2.0, 2.0, ic, Orientation.IDENT, None)
    pin_vdd = NodeInst.makeInstance(bus_pin, ep, Point2D.Double(0.0, 4.0), 2.0, 2.0, ic, Orientation.IDENT, None)
    pin_gnd = NodeInst.makeInstance(bus_pin, ep, Point2D.Double(0.0, -4.0), 2.0, 2.0, ic, Orientation.IDENT, None)

    # Box outline
    box_proto = generic_tech.findNodeProto("Opened-Thicker-Polygon")
    if box_proto:
        NodeInst.makeInstance(box_proto, ep, Point2D.Double(0.0, 0.0), 8.0, 4.0, ic, Orientation.IDENT, None)

    # Exports
    Export.newInst(ic, pin_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
    Export.newInst(ic, pin_out.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
    Export.newInst(ic, pin_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(ic, pin_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    print("buffer{ic} created successfully!")
    return ic

ic = build_buffer_icon()
Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Library saved.")
java.lang.System.exit(0)
