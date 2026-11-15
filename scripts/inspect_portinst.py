# scripts/inspect_portinst.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch = lib.findNodeProto("3Bit_counter{sch}")
nit = sch.getNodes()
while nit.hasNext():
    n = nit.next()
    pname = n.getProto().getName()
    if "D_flipflop" in pname:
        pit = n.getPortInsts()
        pi = pit.next()
        print("PortInst methods:")
        for m in dir(pi):
            print("  " + m)
        break
