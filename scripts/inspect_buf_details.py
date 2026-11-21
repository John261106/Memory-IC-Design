from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.variable import Variable
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

buf = lib.findNodeProto("buffer{sch}")
print("=== buffer{sch} Transistors ===")
nit = buf.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getProto().getName() == "Transistor":
        w = n.getVar(Variable.newKey("ATTR_width"))
        l = n.getVar(Variable.newKey("ATTR_length"))
        model = n.getVar(Variable.newKey("SIM_spice_model"))
        print("Transistor: '%s' model=%s, W=%s, L=%s" % (
            n.getName(),
            model.getObject() if model else None,
            w.getObject() if w else None,
            l.getObject() if l else None))
        for pname in ["g", "s", "d"]:
            p = n.findPortInst(pname)
            if not p: continue
            connected_arcs = []
            ait = p.getArcs()
            while ait.hasNext():
                a = ait.next()
                other = a.getHeadPortInst() if a.getTailPortInst() == p else a.getTailPortInst()
                connected_arcs.append("%s.%s" % (other.getNodeInst().getName(), other.getPortProto().getName()))
            print("  Port %s -> %s" % (pname, ", ".join(connected_arcs)))

print("\n=== Exports ===")
eit = buf.getExports()
while eit.hasNext():
    exp = eit.next()
    p = exp.getOriginalPort()
    print("Export '%s' on %s.%s" % (exp.getName(), p.getNodeInst().getName(), p.getPortProto().getName()))

java.lang.System.exit(0)
