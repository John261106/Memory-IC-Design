from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

top_pkg = lib.findNodeProto("Top_package{sch}")

# Find all exports
exp_map = {}
eit = top_pkg.getExports()
while eit.hasNext():
    exp = eit.next()
    exp_map[exp.getOriginalPort().getNodeInst()] = exp.getName()

print("--- Exports mapping ---")
for node, exp_name in exp_map.items():
    print("Export %s on node %s" % (exp_name, node.getName()))

top_inst = top_pkg.findNode("Top@0")
print("\n--- Ports of Top@0 and what they connect to ---")
for ai in top_pkg.getArcs():
    h = ai.getHeadPortInst()
    t = ai.getTailPortInst()
    if h.getNodeInst() == top_inst or t.getNodeInst() == top_inst:
        top_port = h.getPortProto().getName() if h.getNodeInst() == top_inst else t.getPortProto().getName()
        other = t if h.getNodeInst() == top_inst else h
        print("Top port %s connects to %s [%s]" % (top_port, other.getNodeInst().getName(), other.getPortProto().getName()))

print("\n--- Ports of package@0..6 and what they connect to ---")
for i in range(7):
    pkg_inst = top_pkg.findNode("package@%d" % i)
    if not pkg_inst: continue
    print("package@%d:" % i)
    for ai in top_pkg.getArcs():
        h = ai.getHeadPortInst()
        t = ai.getTailPortInst()
        if h.getNodeInst() == pkg_inst or t.getNodeInst() == pkg_inst:
            pkg_port = h.getPortProto().getName() if h.getNodeInst() == pkg_inst else t.getPortProto().getName()
            other = t if h.getNodeInst() == pkg_inst else h
            other_node = other.getNodeInst()
            other_name = other_node.getName()
            exp_str = " (EXPORT: %s)" % exp_map[other_node] if other_node in exp_map else ""
            print("   port %s -> %s [%s]%s" % (pkg_port, other_name, other.getPortProto().getName(), exp_str))
