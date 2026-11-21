from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")
s1 = cell_sch.findNode("pin_clk_s1")
for ai in cell_sch.getArcs():
    if ai.getHeadPortInst().getNodeInst() == s1 or ai.getTailPortInst().getNodeInst() == s1:
        print("Before: arc %s: head=%s, tail=%s" % (ai.getName(), ai.getHeadLocation(), ai.getTailLocation()))

# Let's inspect modify method parameters
for m in ArcInst.getDeclaredMethods():
    if m.getName() == "modify":
        print("modify param types:", [p.getName() for p in m.getParameterTypes()])
