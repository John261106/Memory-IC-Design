# scripts/list_all_cells_now.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

print("=== All Cells in Memory-IC-Design.jelib ===")
cit = lib.getCells()
while cit.hasNext():
    c = cit.next()
    eit = c.getExports()
    num_exp = 0
    while eit.hasNext():
        eit.next()
        num_exp += 1
    print("Cell: %s (view: %s, nodes: %d, arcs: %d, exports: %d)" % (
        c.getName(), str(c.getView()), c.getNumNodes(), c.getNumArcs(), num_exp))
