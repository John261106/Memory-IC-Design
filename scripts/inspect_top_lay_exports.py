# scripts/inspect_top_lay_exports.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_lay = lib.findNodeProto("Top{lay}")
if top_lay:
    print("=== Top{lay} ===")
    eit = top_lay.getExports()
    while eit.hasNext():
        e = eit.next()
        print("Export: %s (%s)" % (e.getName(), e.getCharacteristic()))
