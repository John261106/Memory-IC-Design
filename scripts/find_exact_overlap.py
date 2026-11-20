from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.text import Setting
import java.lang.Double

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

import sys
sys.path.append("scripts")
from test_top_generator import test_build

# Run build but don't clear at end so we can inspect
top_lay = lib.findNodeProto("Top{lay}")
# Just inspect the arcs in top_lay
ait = top_lay.getArcs()
arcs = []
while ait.hasNext():
    a = ait.next()
    if a.getProto().getName() == "Metal-3":
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        arcs.append((a.getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))

print("Examining %d Metal-3 arcs..." % len(arcs))
for i in range(len(arcs)):
    for j in range(i + 1, len(arcs)):
        n1, x1a, y1a, x1b, y1b = arcs[i]
        n2, x2a, y2a, x2b, y2b = arcs[j]
        # vertical
        if abs(x1a - x1b) < 0.001 and abs(x2a - x2b) < 0.001 and abs(x1a - x2a) < 0.001:
            min1, max1 = min(y1a, y1b), max(y1a, y1b)
            min2, max2 = min(y2a, y2b), max(y2a, y2b)
            overlap = min(max1, max2) - max(min1, min2)
            if overlap > 0.001:
                print("VERTICAL OVERLAP (by %.1f): %s (%.1f..%.1f) and %s (%.1f..%.1f) @ X=%.1f" % (
                    overlap, n1, min1, max1, n2, min2, max2, x1a))
        # horizontal
        if abs(y1a - y1b) < 0.001 and abs(y2a - y2b) < 0.001 and abs(y1a - y2a) < 0.001:
            min1, max1 = min(x1a, x1b), max(x1a, x1b)
            min2, max2 = min(x2a, x2b), max(x2a, x2b)
            overlap = min(max1, max2) - max(min1, min2)
            if overlap > 0.001:
                print("HORIZ OVERLAP (by %.1f): %s (%.1f..%.1f) and %s (%.1f..%.1f) @ Y=%.1f" % (
                    overlap, n1, min1, max1, n2, min2, max2, y1a))
