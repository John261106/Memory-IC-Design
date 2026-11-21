# scripts/inspect_top_details.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.hierarchy import Cell

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")

# Find all nodes in X in [270, 370], Y in [20, 80]
nit = top_sch.getNodes()
nodes = []
while nit.hasNext():
    n = nit.next()
    x = n.getAnchorCenterX()
    y = n.getAnchorCenterY()
    if 270 <= x <= 370 and 20 <= y <= 80:
        nodes.append(n)
        print("Node: '%s' (%s) at (%.1f, %.1f)" % (n.getName(), n.getProto().getName(), x, y))

print("\n--- Exports on Top{sch} in this region ---")
eit = top_sch.getExports()
while eit.hasNext():
    e = eit.next()
    print("Export '%s' (%s), dir: %s" % (e.getName(), e.getCharacteristic(), str(dir(e))))
    break

print("\n--- Arcs in this region ---")
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst()
    t = a.getTailPortInst()
    hn = h.getNodeInst()
    tn = t.getNodeInst()
    hx, hy = h.getCenter().getX(), h.getCenter().getY()
    tx, ty = t.getCenter().getX(), t.getCenter().getY()
    if (270 <= hx <= 370 and 20 <= hy <= 80) or (270 <= tx <= 370 and 20 <= ty <= 80):
        print("Arc '%s' (%s): %s['%s'](%.1f, %.1f) <---> %s['%s'](%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(),
            hn.getProto().getName(), hn.getName(), hx, hy,
            tn.getProto().getName(), tn.getName(), tx, ty
        ))
