# scripts/inspect_control_logic_netlist.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def analyze():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    # Inspect all transistors
    print("--- TRANSISTORS IN Control_logic{sch} ---")
    nit = sch.getNodes()
    tx_list = []
    while nit.hasNext():
        n = nit.next()
        pname = n.getProto().getName() if n.getProto() else ""
        if "Transistor" in pname:
            w_str, l_str = "?", "?"
            vit = n.getVariables()
            while vit.hasNext():
                var = vit.next()
                k = str(var.getKey())
                if "ATTR_W" in k or k == "W":
                    w_str = str(var.getObject())
                elif "ATTR_L" in k or k == "L":
                    l_str = str(var.getObject())

            conns = {}
            for pi in n.getPortInsts():
                pname = pi.getPortProto().getName()
                arc_names = []
                ait = pi.getConnections()
                while ait.hasNext():
                    conn = ait.next()
                    arc = conn.getArc()
                    arc_names.append(arc.getName())
                conns[pname] = arc_names
            tx_list.append((n.getName(), pname, w_str, l_str, conns))

    tx_list.sort(key=lambda x: (int(x[0].split('@')[1]) if '@' in x[0] else 0, x[0]))
    for name, pproto, w, l, conns in tx_list:
        print("%s (%s, W=%s, L=%s): %s" % (name, pproto, w, l, conns))

if __name__ == "__main__":
    analyze()
