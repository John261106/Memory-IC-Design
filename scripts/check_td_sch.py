from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# Check TextDescriptors on NodeInst
print("--- NodeInst TextDescriptors in Top{sch} ---")
node_td_count = 0
for ni in cell_sch.getNodes():
    td = ni.getTextDescriptor(NodeInst.NODE_NAME)
    if td is not None and td.isDisplay():
        node_td_count += 1
print("Nodes with displayed NODE_NAME td:", node_td_count)

# Check TextDescriptors on ArcInst
print("--- ArcInst TextDescriptors in Top{sch} ---")
for f in ArcInst.getDeclaredFields():
    print("ArcInst field:", f.getName())

arc_td_count = 0
for ai in cell_sch.getArcs():
    td = ai.getTextDescriptor(ArcInst.ARC_NAME)
    if td is not None and td.isDisplay():
        arc_td_count += 1
print("Arcs with displayed ARC_NAME td:", arc_td_count)
