from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

def inspect_cell(name):
    c = lib.findNodeProto(name)
    if not c:
        print("Cell %s not found!" % name)
        return
    print("\n================== Cell: %s ==================" % name)
    print("Num nodes: %d, Num arcs: %d" % (c.getNumNodes(), c.getNumArcs()))
    print("--- Exports ---")
    eit = c.getExports()
    while eit.hasNext():
        exp = eit.next()
        p = exp.getOriginalPort()
        print("  Export: '%s', port=%s on node=%s (proto=%s), char=%s" % (
            exp.getName(), p.getPortProto().getName(), p.getNodeInst().getName(), p.getNodeInst().getProto().getName(), exp.getCharacteristic()))
    print("--- Nodes ---")
    nit = c.getNodes()
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto()
        vars_str = []
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            vars_str.append("%s=%s" % (v.getKey().getName(), v.getObject()))
        print("  Node '%s' proto='%s' (isCellInstance=%s) vars=[%s]" % (
            n.getName(), proto.getName(), n.isCellInstance(), ", ".join(vars_str)))

inspect_cell("buffer{sch}")
inspect_cell("buffer{ic}")
inspect_cell("package{sch}")
inspect_cell("package{ic}")
inspect_cell("Top{sch}")

java.lang.System.exit(0)
