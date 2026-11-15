# scripts/print_all_gates.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def print_gates():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    def trace_net_label(pi):
        visited_pins = set()
        queue = [pi]
        found_exps = []
        found_tx_ports = []
        while queue:
            curr_pi = queue.pop(0)
            cnode = curr_pi.getNodeInst()
            cproto = cnode.getProto().getName() if cnode.getProto() else ""
            cport = curr_pi.getPortProto().getName()
            
            for exp in sch.getExports():
                if exp.getOriginalPort() == curr_pi:
                    found_exps.append(exp.getName())

            if "Transistor" in cproto:
                found_tx_ports.append("%s.%s" % (cnode.getName(), cport))
            elif "pin" in cnode.getName():
                if cnode not in visited_pins:
                    visited_pins.add(cnode)
                    for pinst in cnode.getPortInsts():
                        cit2 = pinst.getConnections()
                        while cit2.hasNext():
                            c2 = cit2.next()
                            a2 = c2.getArc()
                            opi = a2.getHeadPortInst() if a2.getTailPortInst() == pinst else a2.getTailPortInst()
                            if opi.getNodeInst() not in visited_pins:
                                queue.append(opi)
        if found_exps:
            return "/".join(set(found_exps))
        return ",".join(set(found_tx_ports))

    # All transistors
    nit = sch.getNodes()
    tx_names = []
    while nit.hasNext():
        n = nit.next()
        if "Transistor" in (n.getProto().getName() if n.getProto() else ""):
            tx_names.append(n.getName())

    tx_names.sort(key=lambda x: (int(x.split('@')[1]), x))
    print("Total transistors: %d" % len(tx_names))
    for tname in tx_names:
        n = sch.findNode(tname)
        w_val = 0.0
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            if "ATTR_width" in str(v.getKey()):
                w_val = float(v.getObject())
        g_net = trace_net_label(n.findPortInst("g"))
        d_net = trace_net_label(n.findPortInst("d"))
        s_net = trace_net_label(n.findPortInst("s"))
        print("%s (W=%.1f): G=[%s] D=[%s] S=[%s]" % (tname, w_val, g_net, d_net, s_net))

if __name__ == "__main__":
    print_gates()
