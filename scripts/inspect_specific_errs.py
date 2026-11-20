from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
top = lib.findNodeProto("Top{lay}")

# Let's inspect the remaining error objects
nit = top.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() in ["top_via_122", "top_via_129", "top_via_1276"]:
        print("Node %s @ %s proto %s" % (n.getName(), n.getAnchorCenter(), n.getProto().getName()))

ait = top.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getName() in ["net@14371", "net@14394", "net@13593", "net@13586", "net@15184"]:
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        print("Arc %s (%s) from (%.1f, %.1f) to (%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
