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
from java.awt.geom import Point2D
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch_tech = Technology.findTechnology("schematic")
test_sch = Cell.newInst(lib, "dummy_top_pkg{sch}")
test_sch.setTechnology(sch_tech)

top_proto = lib.findNodeProto("Top{sch}")
buf_proto = lib.findNodeProto("buffer{sch}")
pkg_proto = lib.findNodeProto("package{sch}")

print("top_proto:", top_proto)
print("buf_proto:", buf_proto)
print("pkg_proto:", pkg_proto)

top_inst = NodeInst.makeInstance(top_proto, ep, Point2D.Double(0.0, 0.0), 30.0, 30.0, test_sch, Orientation.IDENT, "Top@0")
buf_inst = NodeInst.makeInstance(buf_proto, ep, Point2D.Double(-50.0, 0.0), 10.0, 10.0, test_sch, Orientation.IDENT, "buf@0")
pkg_inst = NodeInst.makeInstance(pkg_proto, ep, Point2D.Double(-100.0, 0.0), 10.0, 10.0, test_sch, Orientation.IDENT, "pkg@0")

print("Top CLK port:", top_inst.findPortInst("CLK"))
print("buf IN port:", buf_inst.findPortInst("IN"))
print("buf OUT port:", buf_inst.findPortInst("OUT"))
print("buf VDD port:", buf_inst.findPortInst("VDD"))
print("buf GND port:", buf_inst.findPortInst("GND"))
print("pkg CIRCUIT port:", pkg_inst.findPortInst("CIRCUIT"))
print("pkg PCB_TRACE port:", pkg_inst.findPortInst("PCB_TRACE"))
print("pkg PCB_GND port:", pkg_inst.findPortInst("PCB_GND"))

test_sch.kill()
java.lang.System.exit(0)
