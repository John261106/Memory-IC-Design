from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

wl = lib.findNodeProto("WL_driver{lay}")
print("=== WL_driver{lay} Nodes ===")
nit = wl.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto().getName()
    if "Transistor" in proto:
        print("Transistor '%s' (%s) at (%.1f, %.1f), size=(%.1f, %.1f), orient=%s, W=%.1f, L=%.1f" % (
            n.getName(), proto, n.getAnchorCenterX(), n.getAnchorCenterY(),
            n.getXSize(), n.getYSize(), n.getOrientation(),
            n.getPrimitiveNodeWidth(), n.getPrimitiveNodeLength()))

java.lang.System.exit(0)
