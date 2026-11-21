from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# Check isUsernamed on NodeInst in Top{sch}
sch_nodes_user = 0
for ni in cell_sch.getNodes():
    if ni.isUsernamed():
        sch_nodes_user += 1
print("Top{sch} usernamed nodes:", sch_nodes_user)

# Check isUsernamed on ArcInst in Top{sch}
for m in ArcInst.getDeclaredMethods():
    if "user" in m.getName().lower() or "name" in m.getName().lower():
        print("ArcInst method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])

sch_arcs_user = 0
for ai in cell_sch.getArcs():
    if ai.isUsernamed():
        sch_arcs_user += 1
print("Top{sch} usernamed arcs:", sch_arcs_user)
