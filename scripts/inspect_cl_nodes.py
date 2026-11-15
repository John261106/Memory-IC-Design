# scripts/inspect_cl_nodes.py
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
cl = lib.findNodeProto("Control_logic{lay}")
nit = cl.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() in ["pmos@11", "pmos@12", "nmos@11", "nmos@12"]:
        print(n.getName(), "bounds:", str(n.getBounds()), "size:", n.getXSize(), n.getYSize())
