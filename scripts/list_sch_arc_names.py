# scripts/list_sch_arc_names.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def list_arcs():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")
    ait = sch.getArcs()
    names = set()
    while ait.hasNext():
        a = ait.next()
        names.add(a.getName())

    print("Unique arc names in Control_logic{sch} (%d total):" % len(names))
    for n in sorted(names):
        print("  " + n)

if __name__ == "__main__":
    list_arcs()
