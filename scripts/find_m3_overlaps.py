from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
top = lib.findNodeProto("Top{lay}")

# Find any overlapping arcs on Metal-3
arcs = []
ait = top.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getProto().getName() == "Metal-3":
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        arcs.append((a.getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))

print("Found %d Metal-3 arcs" % len(arcs))
for i in range(len(arcs)):
    for j in range(i + 1, len(arcs)):
        n1, x1a, y1a, x1b, y1b = arcs[i]
        n2, x2a, y2a, x2b, y2b = arcs[j]
        # Check if collinear and overlapping
        # vertical
        if abs(x1a - x1b) < 0.001 and abs(x2a - x2b) < 0.001 and abs(x1a - x2a) < 0.001:
            min1, max1 = min(y1a, y1b), max(y1a, y1b)
            min2, max2 = min(y2a, y2b), max(y2a, y2b)
            if not (max1 <= min2 or max2 <= min1):
                print("OVERLAP VERTICAL: %s (%.1f..%.1f) and %s (%.1f..%.1f) @ X=%.1f" % (n1, min1, max1, n2, min2, max2, x1a))
        # horizontal
        if abs(y1a - y1b) < 0.001 and abs(y2a - y2b) < 0.001 and abs(y1a - y2a) < 0.001:
            min1, max1 = min(x1a, x1b), max(x1a, x1b)
            min2, max2 = min(x2a, x2b), max(x2a, x2b)
            if not (max1 <= min2 or max2 <= min1):
                print("OVERLAP HORIZ: %s (%.1f..%.1f) and %s (%.1f..%.1f) @ Y=%.1f" % (n1, min1, max1, n2, min2, max2, y1a))
