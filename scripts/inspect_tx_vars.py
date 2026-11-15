# scripts/inspect_tx_vars.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def inspect():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")
    n0 = sch.findNode("nmos@0")
    if n0:
        print("nmos@0 proto:", n0.getProto().getName())
        vit = n0.getVariables()
        while vit.hasNext():
            v = vit.next()
            print("  Var: key=%s (%s), obj=%s (%s)" % (v.getKey(), type(v.getKey()), v.getObject(), type(v.getObject())))

        # Also check primitive node size or scale or attributes
        print("  PrimitiveNodeSize:", n0.getPrimitiveNodeSize())

if __name__ == "__main__":
    inspect()
