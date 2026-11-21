# scripts/inspect_top_io.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
top_lay = lib.findNodeProto("Top{lay}")

print("=== Top{sch} Exports ===")
eit = top_sch.getExports()
while eit.hasNext():
    e = eit.next()
    op = e.getOriginalPort()
    on = op.getNodeInst()
    print("  Export: '%s' (%s) on %s['%s'] at (%.1f, %.1f)" % (
        e.getName(), e.getCharacteristic(), on.getProto().getName(), on.getName(),
        on.getAnchorCenterX(), on.getAnchorCenterY()))

print("\n=== Top{lay} Exports ===")
eit = top_lay.getExports()
while eit.hasNext():
    e = eit.next()
    op = e.getOriginalPort()
    on = op.getNodeInst()
    print("  Export: '%s' (%s) on %s['%s'] at (%.1f, %.1f)" % (
        e.getName(), e.getCharacteristic(), on.getProto().getName(), on.getName(),
        on.getAnchorCenterX(), on.getAnchorCenterY()))

print("\n=== Top{lay} Instances ===")
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto().getName()
    if any(k in proto.lower() for k in ["control", "shiftreg", "counter", "decoder", "array", "sense", "d_flip", "buffer"]):
        print("  Instance '%s' (%s) at (%.1f, %.1f), size (%.1f, %.1f), bounds: %s" % (
            n.getName(), proto, n.getAnchorCenterX(), n.getAnchorCenterY(),
            n.getXSize(), n.getYSize(), str(n.getBounds())))
