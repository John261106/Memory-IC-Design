# scripts/inspect_control_logic.py
import java.lang.Double
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def inspect():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")
    if not sch:
        print("Control_logic{sch} NOT found!")
        return

    print("Found Control_logic{sch}:")
    print("Exports:")
    eit = sch.getExports()
    while eit.hasNext():
        exp = eit.next()
        print("  Export: %s (characteristic: %s)" % (exp.getName(), exp.getCharacteristic()))

    print("\nNodes / Instances in Control_logic{sch}:")
    nit = sch.getNodes()
    nodes = []
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto()
        name = n.getName()
        proto_name = proto.getName() if proto else "None"
        nodes.append((name, proto_name, n))
    
    print("Total nodes: %d" % len(nodes))
    for name, p_name, n in nodes:
        print("  Node: %s, Proto: %s" % (name, p_name))

    print("\nArcs / Connections:")
    ait = sch.getArcs()
    arcs = []
    while ait.hasNext():
        a = ait.next()
        arcs.append(a)
    print("Total arcs: %d" % len(arcs))

    # Also check if Control_logic{lay} already exists
    lay = lib.findNodeProto("Control_logic{lay}")
    if lay:
        print("\nControl_logic{lay} ALREADY EXISTS! Total nodes: %d, Total arcs: %d" % (lay.getNumNodes(), lay.getNumArcs()))
    else:
        print("\nControl_logic{lay} does NOT exist yet.")

if __name__ == "__main__":
    inspect()
