import java.lang.Double
from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

dff_lay = lib.findNodeProto("D_flipflop{lay}")
print("D_flipflop{lay} exports:")
eit = dff_lay.getExports()
while eit.hasNext():
    exp = eit.next()
    pi = exp.getOriginalPort()
    pt = pi.getCenter()
    print("  Export: %s at (%f, %f)" % (exp.getName(), pt.getX(), pt.getY()))

print("Nodes near X=-20 in dff_lay:")
nit = dff_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    c = n.getTrueCenter()
    if -25 < c.getX() < -15:
        print("  Node %s (%s) at (%.1f, %.1f)" % (n.getName(), n.getProto().getName(), c.getX(), c.getY()))

print("Arcs near X=-20 in dff_lay:")
ait = dff_lay.getArcs()
while ait.hasNext():
    a = ait.next()
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    minx = min(p1.getX(), p2.getX())
    maxx = max(p1.getX(), p2.getX())
    if minx < -15 and maxx > -25:
        print("  Arc %s (%s) from (%.1f, %.1f) to (%.1f, %.1f)" % (a.getName(), a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
