from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

print("=== EXPORTS IN TOP{SCH} ===")
eit = cell_sch.getExports()
while eit.hasNext():
    exp = eit.next()
    td = exp.getTextDescriptor(Export.EXPORT_NAME)
    print("Export %s: td=%s, display=%s" % (exp.getName(), td, td.isDisplay() if td else None))
