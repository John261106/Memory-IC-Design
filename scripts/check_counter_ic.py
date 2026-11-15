# scripts/check_counter_ic.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

ic = lib.findNodeProto("3Bit_counter{ic}")
if ic:
    print("Found 3Bit_counter{ic}:")
    eit = ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("  IC Export: %s (%s)" % (e.getName(), e.getCharacteristic()))
else:
    print("No 3Bit_counter{ic}")
