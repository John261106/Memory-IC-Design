# scripts/inspect_top_ic.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_ic = lib.findNodeProto("Top{ic}")
if top_ic:
    print("=== Top{ic} ===")
    eit = top_ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("Export: %s (%s)" % (e.getName(), e.getCharacteristic()))
else:
    print("Top{ic} does not exist.")
