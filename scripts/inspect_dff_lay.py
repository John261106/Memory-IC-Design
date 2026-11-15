# scripts/inspect_dff_lay.py
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
if dff_lay:
    print("D_flipflop{lay} found!")
    # exports
    eit = dff_lay.getExports()
    while eit.hasNext():
        e = eit.next()
        pi = e.getOriginalPort()
        pt = pi.getCenter() if pi else None
        print("  Export: %s (%s) at (%f, %f)" % (e.getName(), e.getCharacteristic(), pt.getX() if pt else 0, pt.getY() if pt else 0))
else:
    print("D_flipflop{lay} NOT found!")
