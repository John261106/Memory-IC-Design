# scripts/verify_control_sch_graph.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def verify_graph():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    # Build adjacency across all Wire arcs
    adj = {}
    ait = sch.getArcs()
    while ait.hasNext():
        a = ait.next()
        p1 = a.getHeadPortInst()
        p2 = a.getTailPortInst()
        n1 = p1.getNodeInst()
        n2 = p2.getNodeInst()
        adj.setdefault(n1, []).append(n2)
        adj.setdefault(n2, []).append(n1)

    # Connected components
    visited = set()
    nets = []
    nit = sch.getNodes()
    while nit.hasNext():
        node = nit.next()
        if node in visited:
            continue
        # BFS
        comp = []
        queue = [node]
        visited.add(node)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for neigh in adj.get(curr, []):
                if neigh not in visited:
                    visited.add(neigh)
                    queue.append(neigh)
        nets.append(comp)

    # Map exports to their connected component
    exp_names = {}
    eit = sch.getExports()
    while eit.hasNext():
        e = eit.next()
        exp_names[e.getOriginalPort().getNodeInst()] = e.getName()

    print("Found %d connected nets in Control_logic{sch}:" % len(nets))
    for i, comp in enumerate(nets):
        # find if any node is an export
        exps = [exp_names[n] for n in comp if n in exp_names]
        txs = [n.getName() for n in comp if "Transistor" in (n.getProto().getName() if n.getProto() else "")]
        pins = [n.getName() for n in comp if "pin" in n.getName()]
        net_label = exps[0] if exps else ("net_%d" % i)
        if len(txs) > 0 or len(exps) > 0:
            print("Net [%s] (exps=%s): txs=%s" % (net_label, exps, txs))

if __name__ == "__main__":
    verify_graph()
