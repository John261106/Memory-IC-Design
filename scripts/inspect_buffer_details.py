# scripts/inspect_buffer_details.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

for cname in ["input_buffer", "output_buffer"]:
    print("\n==============================================")
    print("DETAILS FOR: " + cname)
    print("==============================================")
    lay = lib.findNodeProto(cname + "{lay}")
    sch = lib.findNodeProto(cname + "{sch}")
    ic  = lib.findNodeProto(cname + "{ic}")
    
    print("\n--- %s{sch} Nodes & Transistors ---" % cname)
    nit = sch.getNodes()
    tx_count = 0
    while nit.hasNext():
        n = nit.next()
        pname = n.getProto().getName()
        if "transistor" in pname.lower():
            tx_count += 1
            w = None
            vit = n.getVariables()
            while vit.hasNext():
                v = vit.next()
                if "width" in v.getKey().getName().lower():
                    w = v.getObject()
            print("  %s ['%s']: width=%s" % (pname, n.getName(), str(w)))
    print("  Total transistors: %d" % tx_count)
    
    print("\n--- %s{lay} Ports & Locations ---" % cname)
    eit = lay.getExports()
    while eit.hasNext():
        e = eit.next()
        op = e.getOriginalPort()
        node = op.getNodeInst()
        print("  Export '%s' (%s): on %s['%s'] at (%.1f, %.1f), layer/proto: %s" % (
            e.getName(), e.getCharacteristic(),
            node.getProto().getName(), node.getName(),
            op.getCenter().getX(), op.getCenter().getY(),
            node.getProto().getName()
        ))
        
    print("\n--- %s{ic} Ports & Locations ---" % cname)
    eit = ic.getExports()
    while eit.hasNext():
        e = eit.next()
        op = e.getOriginalPort()
        node = op.getNodeInst()
        print("  Export '%s' (%s): at (%.1f, %.1f)" % (
            e.getName(), e.getCharacteristic(),
            op.getCenter().getX(), op.getCenter().getY()
        ))
