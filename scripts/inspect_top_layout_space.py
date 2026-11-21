# scripts/inspect_top_layout_space.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_lay = lib.findNodeProto("Top{lay}")

print("=== Top{lay} Instance Positions & Bounds ===")
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto().getName()
    if any(k in proto.lower() for k in ["control", "shiftreg", "counter", "decoder", "array", "sense", "d_flip", "buffer", "write"]):
        b = n.getBounds()
        print("  %s ['%s']: at (%.1f, %.1f), bounds: X[%.1f, %.1f], Y[%.1f, %.1f]" % (
            proto, n.getName(), n.getAnchorCenterX(), n.getAnchorCenterY(),
            b.getX(), b.getX() + b.getWidth(), b.getY(), b.getY() + b.getHeight()
        ))

print("\n=== Top{lay} Total Bounds ===")
min_x, max_x = 1e9, -1e9
min_y, max_y = 1e9, -1e9
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    b = n.getBounds()
    if b:
        min_x = min(min_x, b.getX())
        max_x = max(max_x, b.getX() + b.getWidth())
        min_y = min(min_y, b.getY())
        max_y = max(max_y, b.getY() + b.getHeight())
print("Overall layout bounds: X in [%.1f, %.1f] (w=%.1f), Y in [%.1f, %.1f] (h=%.1f)" % (
    min_x, max_x, max_x - min_x, min_y, max_y, max_y - min_y))
