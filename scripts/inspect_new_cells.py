from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

print("=== All Cells in Library ===")
cit = lib.getCells()
while cit.hasNext():
    c = cit.next()
    print("Cell: %-25s view=%s, nodes=%d, arcs=%d, exports=%d" % (
        c.getName(), c.getView(), c.getNumNodes(), c.getNumArcs(), c.getNumExports() if hasattr(c, "getNumExports") else -1))

java.lang.System.exit(0)
