# scripts/check_node_methods.py
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

dff_lay = lib.findNodeProto("D_flipflop{lay}")
nit = dff_lay.getNodes()
n = nit.next()
print("NodeInst methods:")
for m in dir(n):
    if "point" in m.lower() or "center" in m.lower() or "pos" in m.lower() or "loc" in m.lower() or "bound" in m.lower():
        print("  " + m)
