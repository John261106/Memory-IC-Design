# scripts/check_tx_sizes.py
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
    if "Transistor" in pname:
        vars = n.getVariables()
        w = None
        l = None
        while vars.hasNext():
            v = vars.next()
            k = v.getKey().getName()
            if "width" in k.lower():
                w = v.getObject()
            if "length" in k.lower():
                l = v.getObject()
        print("%s: W=%s, L=%s" % (n.getName(), str(w), str(l)))
