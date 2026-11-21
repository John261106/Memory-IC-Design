from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.technology import Technology

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")
sch_tech = Technology.findTechnology("schematic")
wire_arc = sch_tech.findArcProto("wire")

s1 = cell_sch.findNode("pin_clk_s1")
print("Before move: s1 at (%.1f, %.1f)" % (s1.getTrueCenterX(), s1.getTrueCenterY()))
s1.move(0.0, -6.0)
print("After move: s1 at (%.1f, %.1f)" % (s1.getTrueCenterX(), s1.getTrueCenterY()))

# Reconnect arcs
arcs_to_reconnect = []
for ai in cell_sch.getArcs():
    h = ai.getHeadPortInst().getNodeInst()
    t = ai.getTailPortInst().getNodeInst()
    if h == s1 or t == s1:
        arcs_to_reconnect.append((ai, ai.getHeadPortInst(), ai.getTailPortInst(), ai.getName()))

for ai, p1, p2, name in arcs_to_reconnect:
    ai.kill()
    new_ai = ArcInst.makeInstance(wire_arc, p1, p2)
    if name:
        new_ai.setName(name)
    print("Recreated arc %s: head=%s, tail=%s" % (name, new_ai.getHeadLocation(), new_ai.getTailLocation()))
