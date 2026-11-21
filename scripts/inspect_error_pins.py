from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# Map each node name to its connected arcs
node_arcs = {}
for ai in cell_sch.getArcs():
    h = ai.getHeadPortInst().getNodeInst().getName()
    t = ai.getTailPortInst().getNodeInst().getName()
    node_arcs.setdefault(h, []).append((ai.getName(), "head", ai.getHeadLocation(), ai.getTailLocation()))
    node_arcs.setdefault(t, []).append((ai.getName(), "tail", ai.getTailLocation(), ai.getHeadLocation()))

for p_name in ["pin@2", "pin@16", "pin@75", "pin@79", "pin@80", "pin@84"]:
    found = None
    for ni in cell_sch.getNodes():
        if ni.getName() == p_name:
            found = ni
            break
    if found:
        arcs = node_arcs.get(p_name, [])
        print("Pin %s at (%s, %s): %d arcs -> %s" % (p_name, found.getTrueCenterX(), found.getTrueCenterY(), len(arcs), arcs))

print("\nCLK_int arcs:")
for ai in cell_sch.getArcs():
    if ai.getName() == "CLK_int":
        print("CLK_int: from %s (%s) to %s (%s)" % (ai.getHeadPortInst().getNodeInst().getName(), ai.getHeadLocation(), ai.getTailPortInst().getNodeInst().getName(), ai.getTailLocation()))
