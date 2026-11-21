# -*- coding: utf-8 -*-
# scripts/build_top_package_sch.py

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
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
wire_proto = sch_tech.findArcProto("wire")
pin_proto = sch_tech.findNodeProto("Wire_Pin")

top_proto = lib.findNodeProto("Top{sch}")
buf_proto = lib.findNodeProto("buffer{sch}")
pkg_proto = lib.findNodeProto("package{sch}")

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

def build_top_package():
    cell_name = "Top_package{sch}"
    cell = lib.findNodeProto(cell_name)
    if cell is None:
        cell = Cell.newInst(lib, cell_name)
    cell.setTechnology(sch_tech)
    clear_cell(cell)

    print("Building %s..." % cell_name)

    # 1. Instantiate Top macro at (0.0, 0.0)
    top_inst = NodeInst.makeInstance(top_proto, ep, Point2D.Double(0.0, 0.0), 30.0, 30.0, cell, Orientation.IDENT, "Top@0")

    # 2. Central power and ground distribution pins
    pin_chip_vdd = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-20.0, 50.0), 1.0, 1.0, cell, Orientation.IDENT, "pin_chip_vdd")
    pin_chip_gnd = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-20.0, -50.0), 1.0, 1.0, cell, Orientation.IDENT, "pin_chip_gnd")

    # Connect chip power/gnd pins to Top
    ArcInst.makeInstance(wire_proto, ep, pin_chip_vdd.getOnlyPortInst(), top_inst.findPortInst("VDD"))
    ArcInst.makeInstance(wire_proto, ep, pin_chip_gnd.getOnlyPortInst(), top_inst.findPortInst("GND"))

    # 3. PCB Power and Ground
    # VDD Package
    pin_vdd_pcb = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-90.0, 70.0), 1.0, 1.0, cell, Orientation.IDENT, "pin_vdd_pcb")
    pkg_vdd = NodeInst.makeInstance(pkg_proto, ep, Point2D.Double(-50.0, 70.0), 10.0, 10.0, cell, Orientation.IDENT, "pkg_vdd")
    ArcInst.makeInstance(wire_proto, ep, pin_vdd_pcb.getOnlyPortInst(), pkg_vdd.findPortInst("PCB_TRACE"))
    ArcInst.makeInstance(wire_proto, ep, pkg_vdd.findPortInst("CIRCUIT"), pin_chip_vdd.getOnlyPortInst())

    # GND Package
    pin_gnd_pcb = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-90.0, -70.0), 1.0, 1.0, cell, Orientation.IDENT, "pin_gnd_pcb")
    pkg_gnd = NodeInst.makeInstance(pkg_proto, ep, Point2D.Double(-50.0, -70.0), 10.0, 10.0, cell, Orientation.IDENT, "pkg_gnd")
    ArcInst.makeInstance(wire_proto, ep, pin_gnd_pcb.getOnlyPortInst(), pkg_gnd.findPortInst("PCB_TRACE"))
    ArcInst.makeInstance(wire_proto, ep, pkg_gnd.findPortInst("CIRCUIT"), pin_chip_gnd.getOnlyPortInst())

    # Connect pkg_vdd PCB_GND to pin_gnd_pcb
    ArcInst.makeInstance(wire_proto, ep, pkg_vdd.findPortInst("PCB_GND"), pin_gnd_pcb.getOnlyPortInst())
    ArcInst.makeInstance(wire_proto, ep, pkg_gnd.findPortInst("PCB_GND"), pin_gnd_pcb.getOnlyPortInst())

    # 4. Inputs: CLK, CTRL, ADDR_IN, DIN
    inputs = [
        {"name": "CLK",     "y": 30.0},
        {"name": "CTRL",    "y": 10.0},
        {"name": "ADDR_IN", "y": -10.0},
        {"name": "DIN",     "y": -30.0}
    ]

    for item in inputs:
        name = item["name"]
        y = item["y"]

        # PCB Pin
        p_pcb = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(-130.0, y), 1.0, 1.0, cell, Orientation.IDENT, "pin_" + name.lower() + "_pcb")
        # Package
        pkg = NodeInst.makeInstance(pkg_proto, ep, Point2D.Double(-90.0, y), 10.0, 10.0, cell, Orientation.IDENT, "pkg_" + name.lower())
        # Buffer
        buf = NodeInst.makeInstance(buf_proto, ep, Point2D.Double(-50.0, y), 10.0, 10.0, cell, Orientation.IDENT, "buf_" + name.lower())

        # Wires:
        # PCB -> pkg.PCB_TRACE
        ArcInst.makeInstance(wire_proto, ep, p_pcb.getOnlyPortInst(), pkg.findPortInst("PCB_TRACE"))
        # pkg.PCB_GND -> pin_gnd_pcb
        ArcInst.makeInstance(wire_proto, ep, pkg.findPortInst("PCB_GND"), pin_gnd_pcb.getOnlyPortInst())
        # pkg.CIRCUIT -> buf.IN
        ArcInst.makeInstance(wire_proto, ep, pkg.findPortInst("CIRCUIT"), buf.findPortInst("IN"))
        # buf.OUT -> top_inst.<name>
        ArcInst.makeInstance(wire_proto, ep, buf.findPortInst("OUT"), top_inst.findPortInst(name))
        # buf power & gnd
        ArcInst.makeInstance(wire_proto, ep, buf.findPortInst("VDD"), pin_chip_vdd.getOnlyPortInst())
        ArcInst.makeInstance(wire_proto, ep, buf.findPortInst("GND"), pin_chip_gnd.getOnlyPortInst())

        # Export PCB Pin as <name>_PCB
        Export.newInst(cell, p_pcb.getOnlyPortInst(), name + "_PCB", PortCharacteristic.IN)

    # 5. Output: DOUT
    # buf_dout at (50.0, 0.0)
    buf_dout = NodeInst.makeInstance(buf_proto, ep, Point2D.Double(50.0, 0.0), 10.0, 10.0, cell, Orientation.IDENT, "buf_dout")
    # pkg_dout at (90.0, 0.0)
    pkg_dout = NodeInst.makeInstance(pkg_proto, ep, Point2D.Double(90.0, 0.0), 10.0, 10.0, cell, Orientation.IDENT, "pkg_dout")
    # pin_dout_pcb at (130.0, 0.0)
    pin_dout_pcb = NodeInst.makeInstance(pin_proto, ep, Point2D.Double(130.0, 0.0), 1.0, 1.0, cell, Orientation.IDENT, "pin_dout_pcb")

    # Wires:
    # top_inst.DOUT -> buf_dout.IN
    ArcInst.makeInstance(wire_proto, ep, top_inst.findPortInst("DOUT"), buf_dout.findPortInst("IN"))
    # buf_dout.OUT -> pkg_dout.CIRCUIT
    ArcInst.makeInstance(wire_proto, ep, buf_dout.findPortInst("OUT"), pkg_dout.findPortInst("CIRCUIT"))
    # pkg_dout.PCB_TRACE -> pin_dout_pcb
    ArcInst.makeInstance(wire_proto, ep, pkg_dout.findPortInst("PCB_TRACE"), pin_dout_pcb.getOnlyPortInst())
    # pkg_dout.PCB_GND -> pin_gnd_pcb
    ArcInst.makeInstance(wire_proto, ep, pkg_dout.findPortInst("PCB_GND"), pin_gnd_pcb.getOnlyPortInst())
    # buf_dout power & gnd
    ArcInst.makeInstance(wire_proto, ep, buf_dout.findPortInst("VDD"), pin_chip_vdd.getOnlyPortInst())
    ArcInst.makeInstance(wire_proto, ep, buf_dout.findPortInst("GND"), pin_chip_gnd.getOnlyPortInst())

    # Export DOUT_PCB
    Export.newInst(cell, pin_dout_pcb.getOnlyPortInst(), "DOUT_PCB", PortCharacteristic.OUT)

    # Export Power and GND
    Export.newInst(cell, pin_vdd_pcb.getOnlyPortInst(), "VDD_PCB", PortCharacteristic.PWR)
    Export.newInst(cell, pin_gnd_pcb.getOnlyPortInst(), "GND_PCB", PortCharacteristic.GND)

    print("Top_package{sch} successfully built!")
    return cell

top_pkg = build_top_package()

print("\n=== Exports in Top_package{sch} ===")
eit = top_pkg.getExports()
while eit.hasNext():
    e = eit.next()
    print("  Export: %-15s (characteristic=%s)" % (e.getName(), e.getCharacteristic()))

print("\nSaving library...")
Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
print("Library saved successfully.")

java.lang.System.exit(0)
