# scripts/inspect_counter_details.py
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

f = open("counter_sch_dump.txt", "w")
f.write("=== EXPORTS ===\n")
eit = counter_sch.getExports()
while eit.hasNext():
    exp = eit.next()
    pi = exp.getOriginalPort()
    ni = pi.getNodeInst() if pi else None
    f.write("Export: %s, Char: %s, on node %s\n" % (exp.getName(), exp.getCharacteristic(), ni.getName() if ni else "None"))

f.write("\n=== INSTANCES / NODES ===\n")
nit = counter_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto()
    pname = proto.getName()
    if "Transistor" in pname:
        w = n.getVar("ATTR_width")
        l = n.getVar("ATTR_length")
        f.write("Transistor %s (%s): W=%s, L=%s\n" % (n.getName(), pname, w, l))
    elif "D_flipflop" in pname:
        f.write("Subcell Instance %s of %s\n" % (n.getName(), pname))
        pit = n.getPortInsts()
        pnames = []
        while pit.hasNext():
            pi = pit.next()
            pnames.append(str(dir(pi)))
            break
        f.write("   Methods: %s\n" % str(pnames))
    elif "Facet-Center" in pname or "Pin" in pname or "Wire_Pin" in pname:
        pass
    else:
        f.write("Other Node: %s of %s\n" % (n.getName(), pname))

f.write("\n=== ARCS & CONNECTIONS ===\n")
ait = counter_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    hp = a.getHeadPortInst()
    tp = a.getTailPortInst()
    hn = hp.getNodeInst()
    tn = tp.getNodeInst()
    a_name = a.getName()
    f.write("Arc %s: %s <--> %s\n" % (a_name, hn.getName(), tn.getName()))
f.close()
print("Wrote counter_sch_dump.txt")
