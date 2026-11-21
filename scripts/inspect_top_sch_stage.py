# scripts/inspect_top_sch_stage.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
print("=== Inspecting Top{sch} ===")

nit = top_sch.getNodes()
relevant_nodes = []
while nit.hasNext():
    n = nit.next()
    proto_name = n.getProto().getName()
    name = n.getName()
    if any(k in proto_name.lower() or k in name.lower() for k in ["sense", "not", "flipflop", "dff", "out", "dout"]):
        relevant_nodes.append(n)
        print("Node: '%s' (proto: %s) at (%.1f, %.1f), size: (%.1f, %.1f)" % (
            name, proto_name, n.getAnchorCenterX(), n.getAnchorCenterY(), n.getXSize(), n.getYSize()))

print("\n=== Arcs connected to these nodes ===")
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst()
    t = a.getTailPortInst()
    hn = h.getNodeInst()
    tn = t.getNodeInst()
    if hn in relevant_nodes or tn in relevant_nodes:
        print("Arc '%s' (%s): %s['%s'] port %s (%.1f, %.1f) <---> %s['%s'] port %s (%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(),
            hn.getProto().getName(), hn.getName(), h.getPortProto().getName(), h.getCenter().getX(), h.getCenter().getY(),
            tn.getProto().getName(), tn.getName(), t.getPortProto().getName(), t.getCenter().getX(), t.getCenter().getY()
        ))


