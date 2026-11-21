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
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.awt.geom import Point2D
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
cell = Cell.newInst(lib, "test_m2_rail{lay}")
cell.setTechnology(mocmos)

m2_wire = mocmos.findArcProto("Metal-2")
m1_wire = mocmos.findArcProto("Metal-1")
m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
m2_pin = mocmos.findNodeProto("Metal-2-Pin")
m1_pin = mocmos.findNodeProto("Metal-1-Pin")

via1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(20.0, 30.0), 5.0, 5.0, cell, Orientation.IDENT, None)
via2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(50.0, 30.0), 5.0, 5.0, cell, Orientation.IDENT, None)
p_l = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(0.0, 30.0), 4.0, 4.0, cell, Orientation.IDENT, None)
p_r = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(70.0, 30.0), 4.0, 4.0, cell, Orientation.IDENT, None)

ArcInst.makeInstance(m2_wire, ep, p_l.getOnlyPortInst(), via1.getOnlyPortInst())
ArcInst.makeInstance(m2_wire, ep, via1.getOnlyPortInst(), via2.getOnlyPortInst())
ArcInst.makeInstance(m2_wire, ep, via2.getOnlyPortInst(), p_r.getOnlyPortInst())

p_m1_1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(20.0, 10.0), 3.0, 3.0, cell, Orientation.IDENT, None)
ArcInst.makeInstance(m1_wire, ep, via1.getOnlyPortInst(), p_m1_1.getOnlyPortInst())

logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break
print("Quick DRC: errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))
it = logger.getLogs()
while it.hasNext():
    print("  " + it.next().getMessageString())

cell.kill()
java.lang.System.exit(0)
