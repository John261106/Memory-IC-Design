from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch = lib.findNodeProto("WL_driver{sch}")
lay = lib.findNodeProto("WL_driver{lay}")
icon = lib.findNodeProto("WL_driver{ic}")

print("WL_driver{sch}:", sch)
print("WL_driver{lay}:", lay)
print("WL_driver{ic}:", icon)

if sch:
    print("\n--- SCHEMATIC EXPORTS ---")
    eit = sch.getExports()
    while eit.hasNext():
        e = eit.next()
        pi = e.getOriginalPort()
        ni = pi.getNodeInst() if pi else None
        print("Export: %s, char: %s, node: %s, port: %s" % (e.getName(), e.getCharacteristic(), ni.getName() if ni else None, pi.getPortProto().getName() if pi else None))

    print("\n--- SCHEMATIC NODES ---")
    nit = sch.getNodes()
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto().getName()
        vars_dict = {}
        vit = n.getVariables()
        while vit.hasNext():
            var = vit.next()
            vars_dict[var.getKey().getName()] = var.getObject()
        pt = n.getTrueCenter()
        print("Node %s [%s]: vars=%s, center=(%s,%s)" % (n.getName(), proto, vars_dict, pt.getX(), pt.getY()))
        for p in n.getPortInsts():
            ait = p.getConnections()
            conns = []
            while ait.hasNext():
                conn = ait.next()
                conns.append(conn.getArc().getName())
            print("   Port %s connected to arcs: %s" % (p.getPortProto().getName(), conns))

    print("\n--- SCHEMATIC ARCS ---")
    ait = sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        h = a.getHeadPortInst()
        t = a.getTailPortInst()
        print("Arc %s: %s:%s -> %s:%s" % (a.getName(), h.getNodeInst().getName(), h.getPortProto().getName(), t.getNodeInst().getName(), t.getPortProto().getName()))
