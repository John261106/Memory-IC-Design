# scripts/find_buffer_placements.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_lay = lib.findNodeProto("Top{lay}")

print("=== Checking Existing Cell Instances and Pin Locations ===")
nit = top_lay.getNodes()
boxes = []
while nit.hasNext():
    n = nit.next()
    proto = n.getProto().getName()
    if not any(k in proto for k in ["Con", "Pin", "Facet"]):
        b = n.getBounds()
        boxes.append((n.getName(), proto, b.getX(), b.getX() + b.getWidth(), b.getY(), b.getY() + b.getHeight()))

for name, proto, x1, x2, y1, y2 in sorted(boxes, key=lambda b: b[4]):
    print("  %s (%s): X[%.1f, %.1f], Y[%.1f, %.1f]" % (name, proto, x1, x2, y1, y2))
