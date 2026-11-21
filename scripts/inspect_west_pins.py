from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.tool.drc import Schematic, DRC
from com.sun.electric.tool.user import ErrorLogger

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# Check pin locations around CLK branches
print("--- Western pins between Y=0 and Y=70, X between -150 and -110 ---")
for ni in cell_sch.getNodes():
    cx = ni.getTrueCenterX()
    cy = ni.getTrueCenterY()
    if -150 <= cx <= -110 and -10 <= cy <= 75:
        print("Node: %s (%s) at (%.1f, %.1f)" % (ni.getName(), ni.getProto().getName() if ni.getProto() else None, cx, cy))
