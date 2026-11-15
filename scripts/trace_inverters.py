# scripts/trace_inverters.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def trace_inv():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    # For every transistor, let's trace where its gate and drain go
    # by traversing through pins to find other transistor gates/drains/exports
    def find_connected_terminals(node, port_name):
        pi = node.findPortInst(port_name)
        if not pi:
            return []
        visited_pins = set()
        results = []
        queue = []
        cit = pi.getConnections()
        while cit.hasNext():
            conn = cit.next()
            arc = conn.getArc()
            other_pi = arc.getHeadPortInst() if arc.getTailPortInst() == pi else arc.getTailPortInst()
            queue.append(other_pi)

        while queue:
            curr_pi = queue.pop(0)
            cnode = curr_pi.getNodeInst()
            cproto = cnode.getProto().getName() if cnode.getProto() else ""
            cport = curr_pi.getPortProto().getName()
            
            # Check if export
            for exp in sch.getExports():
                if exp.getOriginalPort() == curr_pi:
                    results.append("EXPORT:" + exp.getName())

            if "Transistor" in cproto:
                results.append("%s.%s" % (cnode.getName(), cport))
            elif "pin" in cnode.getName():
                if cnode not in visited_pins:
                    visited_pins.add(cnode)
                    # explore connections from other ports of this pin
                    for pinst in cnode.getPortInsts():
                        cit2 = pinst.getConnections()
                        while cit2.hasNext():
                            c2 = cit2.next()
                            a2 = c2.getArc()
                            opi = a2.getHeadPortInst() if a2.getTailPortInst() == pinst else a2.getTailPortInst()
                            if opi.getNodeInst() not in visited_pins:
                                queue.append(opi)
        return list(set(results))

    print("--- INVERTER CHAIN TRACING ---")
    tx_names = ["nmos@0", "nmos@2", "nmos@3", "nmos@4", "nmos@5", "nmos@6", "nmos@7", "nmos@8", "nmos@9", "nmos@10", "nmos@11", "nmos@12", "nmos@13",
                "nmos@14", "nmos@15", "nmos@16", "nmos@17", "nmos@18", "nmos@19", "nmos@20", "nmos@21"]
    for tname in tx_names:
        node = sch.findNode(tname)
        g_conns = find_connected_terminals(node, "g")
        d_conns = find_connected_terminals(node, "d")
        s_conns = find_connected_terminals(node, "s")
        print("%s: G -> %s | D -> %s | S -> %s" % (tname, g_conns, d_conns, s_conns))

if __name__ == "__main__":
    trace_inv()
