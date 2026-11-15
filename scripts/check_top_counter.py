# scripts/check_top_counter.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
if top_sch:
    nit = top_sch.getNodes()
    while nit.hasNext():
        n = nit.next()
        if "3Bit_counter" in n.getProto().getName():
            print("Found counter in Top{sch}: " + n.getName())
            pit = n.getPortInsts()
            while pit.hasNext():
                pi = pit.next()
                print("  Port: %s" % pi.getPortProto().getName())
