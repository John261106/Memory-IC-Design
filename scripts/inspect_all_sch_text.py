from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cit = lib.getCells()
while cit.hasNext():
    cell = cit.next()
    if str(cell.getView()) != "View schematic":
        continue
    cname = cell.getName()
    
    export_ports = set()
    eit = cell.getExports()
    while eit.hasNext():
        export_ports.add(eit.next().getOriginalPort())
        
    # Check node names and variables
    named_nodes = []
    for ni in cell.getNodes():
        proto = ni.getProto()
        pname = proto.getName() if proto else ""
        nname = ni.getName()
        
        has_export = False
        pit = ni.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            if pi in export_ports:
                has_export = True
                break
        
        vars_list = []
        vit = ni.getVariables()
        while vit.hasNext():
            v = vit.next()
            vars_list.append("%s=%s" % (v.getKey().getName(), v.getObject()))
        
        if (vars_list or nname) and not has_export:
            named_nodes.append((pname, nname, vars_list))
            
    # Check arcs
    named_arcs = []
    for ai in cell.getArcs():
        aname = ai.getName()
        vars_list = []
        vit = ai.getVariables()
        while vit.hasNext():
            v = vit.next()
            vars_list.append("%s=%s" % (v.getKey().getName(), v.getObject()))
        if aname or vars_list:
            named_arcs.append((aname, vars_list))
            
    print("Cell %s{sch}: %d internal nodes (named/vars), %d named/var arcs" % (cname, len(named_nodes), len(named_arcs)))
    if named_arcs:
        print("  sample arcs:", named_arcs[:3])
