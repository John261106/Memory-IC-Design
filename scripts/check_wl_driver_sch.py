# scripts/check_wl_driver_sch.py
from com.sun.electric.database.hierarchy import Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def check():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
    sch = lib.findNodeProto("WL_driver{sch}")
    for nname in ["nmos@0", "nmos@1"]:
        n = sch.findNode(nname)
        conns = {}
        for pi in n.getPortInsts():
            pname = pi.getPortProto().getName()
            cit = pi.getConnections()
            arc_names = []
            while cit.hasNext():
                arc_names.append(cit.next().getArc().getName())
            conns[pname] = arc_names
        print("%s: %s" % (nname, conns))

if __name__ == "__main__":
    check()
