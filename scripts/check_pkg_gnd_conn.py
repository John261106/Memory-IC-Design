from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell = lib.findNodeProto("Top_package{sch}")

# Check which pins and exports are on net@24
print("--- Arcs on net@24 in Top_package{sch} ---")
for ai in cell.getArcs():
    h = ai.getHeadPortInst()
    t = ai.getTailPortInst()
    # Check if either head or tail is connected to package PCB_GND
    h_pkg = "PCB_GND" in h.getPortProto().getName()
    t_pkg = "PCB_GND" in t.getPortProto().getName()
    if h_pkg or t_pkg:
        print("Arc %s: %s[%s] -> %s[%s]" % (ai.getName(), h.getNodeInst().getName(), h.getPortProto().getName(), t.getNodeInst().getName(), t.getPortProto().getName()))
