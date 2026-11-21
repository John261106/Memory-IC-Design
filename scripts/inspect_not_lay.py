from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

def print_cell_layout(name):
    c = lib.findNodeProto(name)
    if not c: return
    print("\n=== %s ===" % name)
    nit = c.getNodes()
    while nit.hasNext():
        n = nit.next()
        x = n.getAnchorCenterX()
        y = n.getAnchorCenterY()
        print("  Node: proto=%-25s x=%6.1f, y=%6.1f, w=%4.1f, h=%4.1f" % (
            n.getProto().getName(), x, y, n.getXSize(), n.getYSize()))

print_cell_layout("Not{lay}")

java.lang.System.exit(0)
