# scripts/dump_counter_sch.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch = lib.findNodeProto("3Bit_counter{sch}")

print("=== EXPORTS ===")
eit = sch.getExports()
while eit.hasNext():
    e = eit.next()
    pi = e.getOriginalPort()
    ni = pi.getNodeInst() if pi else None
    print("Export: %s (%s) on node %s port %s" % (e.getName(), e.getCharacteristic(), ni.getName() if ni else "None", pi.getPortProto().getName() if pi else "None"))

print("\n=== NODES ===")
nit = sch.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto()
    pname = proto.getName()
    if "Transistor" in pname:
        print("Transistor %s (%s)" % (n.getName(), pname))
        pit = n.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            c_list = [c.getArc().getName() for c in pi.getConnections()]
            print("   Port %s: %s" % (pi.getPortProto().getName(), str(c_list)))
    elif "D_flipflop" in pname:
        print("Subcell %s of %s" % (n.getName(), pname))
        pit = n.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            c_list = [c.getArc().getName() for c in pi.getConnections()]
            print("   Port %s: %s" % (pi.getPortProto().getName(), str(c_list)))

print("\n=== ARCS ===")
ait = sch.getArcs()
while ait.hasNext():
    a = ait.next()
    hp = a.getHeadPortInst()
    tp = a.getTailPortInst()
    hn = hp.getNodeInst()
    tn = tp.getNodeInst()
    # Check if arc or either node has a name or text
    print("Arc %s: %s[%s] <--> %s[%s]" % (a.getName(), hn.getName(), hp.getPortProto().getName(), tn.getName(), tp.getPortProto().getName()))
