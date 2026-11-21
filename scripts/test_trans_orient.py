from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst
from com.sun.electric.database.hierarchy import Cell
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
mocmos = Technology.findTechnology("mocmos")
p_proto = mocmos.findNodeProto("P-Transistor")

cell = Cell.newInst(lib, "dummy{lay}")
cell.setTechnology(mocmos)

t_ident = NodeInst.makeInstance(p_proto, ep, Point2D.Double(0.0, 0.0), 22.0, 15.0, cell, Orientation.IDENT, "t_ident")
t_ident.setPrimitiveNodeSize(32.0, 2.0, ep)
print("IDENT: XSize=%.1f, YSize=%.1f" % (t_ident.getXSize(), t_ident.getYSize()))
for p in ["diff-top", "diff-bottom", "diff-left", "diff-right", "poly-top", "poly-bottom", "poly-left", "poly-right"]:
    pi = t_ident.findPortInst(p)
    if pi:
        print("  port %-12s at (%.1f, %.1f)" % (p, pi.getCenter().getX(), pi.getCenter().getY()))

t_r = NodeInst.makeInstance(p_proto, ep, Point2D.Double(50.0, 0.0), 22.0, 15.0, cell, Orientation.R, "t_r")
t_r.setPrimitiveNodeSize(32.0, 2.0, ep)
print("\nOrientation.R: XSize=%.1f, YSize=%.1f" % (t_r.getXSize(), t_r.getYSize()))
for p in ["diff-top", "diff-bottom", "diff-left", "diff-right", "poly-top", "poly-bottom", "poly-left", "poly-right"]:
    pi = t_r.findPortInst(p)
    if pi:
        print("  port %-12s at (%.1f, %.1f)" % (p, pi.getCenter().getX(), pi.getCenter().getY()))

cell.kill()
java.lang.System.exit(0)
