from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell = lib.findNodeProto("Top_package{sch}")
print("Cell:", cell)

print("\n--- Exports in Top_package{sch} ---")
eit = cell.getExports()
while eit.hasNext():
    exp = eit.next()
    print("Export: %s (char: %s, port: %s)" % (exp.getName(), exp.getCharacteristic(), exp.getOriginalPort()))

print("\n--- Instances in Top_package{sch} ---")
for ni in cell.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else "Primitive"
    if pname != "Wire_Pin" and pname != "Primitive":
        print("Instance: %s (proto: %s, pos: (%.1f, %.1f))" % (ni.getName(), pname, ni.getTrueCenterX(), ni.getTrueCenterY()))
        pit = ni.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            # print connected arcs
            conns = []
            ait = pi.getConnectedArcs() if hasattr(pi, 'getConnectedArcs') else []
            # we can check cell arcs
