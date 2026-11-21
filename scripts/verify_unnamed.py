from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.hierarchy import Cell, View
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

print("=== Checking isUsernamed across all layout cells ===")
cit = lib.getCells()
total_usernamed = 0
total_nodes = 0
while cit.hasNext():
    c = cit.next()
    if c.getView() != View.LAYOUT: continue
    c_usernamed = 0
    c_nodes = 0
    nit = c.getNodes()
    while nit.hasNext():
        ni = nit.next()
        c_nodes += 1
        if ni.isUsernamed():
            c_usernamed += 1
    total_usernamed += c_usernamed
    total_nodes += c_nodes
    print("Cell %-20s: total_nodes=%4d, usernamed_nodes=%d" % (c.getName(), c_nodes, c_usernamed))

print("\nGrand Total: %d / %d nodes are usernamed." % (total_usernamed, total_nodes))
java.lang.System.exit(0)
