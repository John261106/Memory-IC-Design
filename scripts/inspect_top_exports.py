# scripts/inspect_top_exports.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
eit = top_sch.getExports()
while eit.hasNext():
    e = eit.next()
    op = e.getOriginalPort()
    on = op.getNodeInst()
    print("Export '%s' (%s) on node '%s' (%s) at (%.1f, %.1f)" % (
        e.getName(), e.getCharacteristic(), on.getName(), on.getProto().getName(),
        on.getAnchorCenterX(), on.getAnchorCenterY()))
