# -*- coding: utf-8 -*-
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
from com.sun.electric.tool.ncc import Ncc, NccOptions
from java.awt.geom import Point2D
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch_tech = Technology.findTechnology("schematic")
wire_proto = sch_tech.findArcProto("wire")
pin_proto = sch_tech.findNodeProto("Wire_Pin")
tx_proto = sch_tech.findNodeProto("Transistor")

buf_sch = lib.findNodeProto("buffer{sch}")
print("=== Current buffer{sch} ===")
nit = buf_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    if "Transistor" in n.getProto().getName():
        vit = n.getVariables()
        vars_l = []
        while vit.hasNext():
            v = vit.next()
            vars_l.append("%s=%s" % (v.getKey().getName(), v.getObject()))
        print("  %s: %s" % (n.getName(), ", ".join(vars_l)))

java.lang.System.exit(0)
