# scripts/inspect_counter.py
import java.lang.Double
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

counter_sch = lib.findNodeProto("3Bit_counter{sch}")
if counter_sch is None:
    print("3Bit_counter{sch} NOT found!")
    # list all cells matching counter
    cit = lib.getCells()
    while cit.hasNext():
        c = cit.next()
        if "counter" in c.getName().lower():
            print("Found cell: " + c.getName())
else:
    print("Found 3Bit_counter{sch}:")
    print("Exports:")
    eit = counter_sch.getExports()
    while eit.hasNext():
        exp = eit.next()
        print("  %s : %s" % (exp.getName(), exp.getCharacteristic()))

    print("Nodes / Instances:")
    nit = counter_sch.getNodes()
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto()
        pos_str = str(n.getAnchorPoint()) if hasattr(n, 'getAnchorPoint') else ""
        print("  Node: %s, Proto: %s, Pos: %s" % (n.getName(), proto.getName(), pos_str))

    print("Arcs / Nets:")
    ait = counter_sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        proto = a.getProto()
        head = a.getHeadPortInst()
        tail = a.getTailPortInst()
        print("  Arc: %s, Net: %s, From: %s:%s to %s:%s" % (
            a.getName(), 
            a.getNet().getName() if a.getNet() else "None",
            head.getNodeInst().getName(), head.getPort().getName(),
            tail.getNodeInst().getName(), tail.getPort().getName()
        ))
