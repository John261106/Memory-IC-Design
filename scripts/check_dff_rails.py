# scripts/check_dff_rails.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
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
while nit.hasNext():
    n = nit.next()
    if "rail" in n.getName().lower() or "vdd" in n.getName().lower() or "gnd" in n.getName().lower():
        print("Node: %s (%s) at %s, size: (%f, %f)" % (n.getName(), n.getProto().getName(), str(n.getAnchorPoint()), n.getXSize(), n.getYSize()))
