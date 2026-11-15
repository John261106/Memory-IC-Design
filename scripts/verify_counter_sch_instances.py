# scripts/verify_counter_sch_instances.py
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
nit = sch.getNodes()
while nit.hasNext():
    n = nit.next()
    pname = n.getProto().getName()
    if "D_flipflop" in pname:
        print("Instance: %s of %s" % (n.getName(), pname))
        # let's list connections
        for pi in n.getPortInstList():
            c_arcs = []
            it = pi.getArcs() if hasattr(pi, 'getArcs') else []
            # In electric, pi is PortInst, let's see its methods
            print("  PortInst: %s" % pi.getPort().getName())
