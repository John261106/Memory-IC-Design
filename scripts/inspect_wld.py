from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
wld = lib.findNodeProto("WL_driver{lay}")

print("WL_driver exports:")
eit = wld.getExports()
while eit.hasNext():
    e = eit.next()
    pi = e.getOriginalPort()
    pt = pi.getCenter()
    print("  %s @ (%.1f, %.1f) on node %s" % (
        e.getName(), pt.getX(), pt.getY(), pi.getNodeInst().getName()))

print("\nWL_driver arcs:")
ait = wld.getArcs()
while ait.hasNext():
    a = ait.next()
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    print("  %s (%s) from (%.1f, %.1f) to (%.1f, %.1f)" % (
        a.getName(), a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
