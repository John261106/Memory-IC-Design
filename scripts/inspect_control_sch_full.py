# scripts/inspect_control_sch_full.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def inspect_sch():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    print("Exports in Control_logic{sch}:")
    eit = sch.getExports()
    while eit.hasNext():
        e = eit.next()
        orig = e.getOriginalPort()
        print("  Export: %s, Char: %s, OrigPort: %s of Node %s" % (
            e.getName(), e.getCharacteristic(),
            (orig.getPortProto().getName() if orig else "None"),
            (orig.getNodeInst().getName() if orig else "None")
        ))

    print("\nTransistors in Control_logic{sch}:")
    nit = sch.getNodes()
    txs = []
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto()
        pname = proto.getName() if proto else ""
        if "Transistor" in pname:
            w = 0.0
            l = 0.0
            model = ""
            vit = n.getVariables()
            while vit.hasNext():
                var = vit.next()
                k = str(var.getKey())
                if "ATTR_width" in k:
                    w = float(var.getObject())
                elif "ATTR_length" in k:
                    l = float(var.getObject())
                elif "SIM_spice_model" in k:
                    model = str(var.getObject())
            
            # For each port (d, g, s), find connected nodes
            conns = {}
            for pi in n.getPortInsts():
                pname = pi.getPortProto().getName()
                conn_list = []
                cit = pi.getConnections()
                while cit.hasNext():
                    conn = cit.next()
                    arc = conn.getArc()
                    other_pi = arc.getHeadPortInst() if arc.getTailPortInst() == pi else arc.getTailPortInst()
                    other_node = other_pi.getNodeInst()
                    conn_list.append((other_node.getName(), other_pi.getPortProto().getName()))
                conns[pname] = conn_list
            txs.append((n.getName(), pname, model, w, l, conns))

    txs.sort(key=lambda x: (int(x[0].split('@')[1]) if '@' in x[0] else 0, x[0]))
    for name, proto, model, w, l, conns in txs:
        print("%s (%s, model=%s, W=%.1f, L=%.1f):" % (name, proto, model, w, l))
        for p, clist in conns.items():
            print("    %s -> %s" % (p, clist))

if __name__ == "__main__":
    inspect_sch()
