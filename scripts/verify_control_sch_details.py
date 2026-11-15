# scripts/verify_control_sch_details.py
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

    # Build graph of all connections in schematic
    # Map each port instance of each transistor to its connected net name or other terminals
    adj = {}
    ait = sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        p1 = a.getHeadPortInst()
        p2 = a.getTailPortInst()
        adj.setdefault(p1, []).append(p2)
        adj.setdefault(p2, []).append(p1)

    # Exports
    exp_port_map = {}
    eit = sch.getExports()
    while eit.hasNext():
        e = eit.next()
        exp_port_map[e.getOriginalPort()] = e.getName()

    # Find connected component for any port instance
    def get_net_name(pi):
        visited = set([pi])
        q = [pi]
        exps = []
        tx_ports = []
        while q:
            curr = q.pop(0)
            if curr in exp_port_map:
                exps.append(exp_port_map[curr])
            node = curr.getNodeInst()
            if "Transistor" in (node.getProto().getName() if node.getProto() else ""):
                tx_ports.append("%s.%s" % (node.getName(), curr.getPortProto().getName()))
            for neigh in adj.get(curr, []):
                if neigh not in visited:
                    visited.add(neigh)
                    q.append(neigh)
        if exps:
            return exps[0]
        # otherwise return first tx_port as net identifier
        tx_ports.sort()
        return "net_" + tx_ports[0]

    print("--- ALL 21 PAIRS CONNECTIVITY ---")
    pairs = [
        ("CLK_inv", "pmos@0", "nmos@0"),
        ("CLK_buf", "pmos@2", "nmos@2"),
        ("PCB_buf", "pmos@3", "nmos@3"),
        ("CTRL_inv", "pmos@4", "nmos@4"),
        ("WL_NAND_A", "pmos@11", "nmos@11"),
        ("WL_NAND_B", "pmos@12", "nmos@12"),
        ("WL_buf", "pmos@13", "nmos@13"),
        ("WR_NAND_A", "pmos@5", "nmos@5"),
        ("WR_NAND_B", "pmos@6", "nmos@6"),
        ("WR_buf", "pmos@7", "nmos@7"),
        ("RD_NAND_A", "pmos@8", "nmos@8"),
        ("RD_NAND_B", "pmos@9", "nmos@9"),
        ("RD_inv_0", "pmos@10", "nmos@10"),
        ("RD_d1", "pmos@14", "nmos@14"),
        ("RD_d2", "pmos@15", "nmos@15"),
        ("RD_d3", "pmos@16", "nmos@16"),
        ("RD_d4", "pmos@17", "nmos@17"),
        ("RD_d5", "pmos@18", "nmos@18"),
        ("RD_d6", "pmos@19", "nmos@19"),
        ("RD_d7", "pmos@20", "nmos@20"),
        ("RD_buf", "pmos@21", "nmos@21"),
    ]

    for label, pname, nname in pairs:
        pn = sch.findNode(pname)
        nn = sch.findNode(nname)
        
        pw = float(pn.getVariables().next().getObject()) # we'll inspect vars
        nw = float(nn.getVariables().next().getObject())

        # PMOS ports: d, g, s
        p_g = get_net_name(pn.findPortInst("g"))
        p_d = get_net_name(pn.findPortInst("d"))
        p_s = get_net_name(pn.findPortInst("s"))

        # NMOS ports: d, g, s
        n_g = get_net_name(nn.findPortInst("g"))
        n_d = get_net_name(nn.findPortInst("d"))
        n_s = get_net_name(nn.findPortInst("s"))

        print("[%s] %s: G=%s, D=%s, S=%s" % (label, pname, p_g, p_d, p_s))
        print("          %s: G=%s, D=%s, S=%s" % (nname, n_g, n_d, n_s))

if __name__ == "__main__":
    analyze()
