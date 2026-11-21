from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

pkg = lib.findNodeProto("package{sch}")
print("--- package{sch} exports ---")
eit = pkg.getExports()
while eit.hasNext():
    exp = eit.next()
    print("Export:", exp.getName(), exp.getCharacteristic())

print("\n--- package{sch} instances ---")
for ni in pkg.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else "Primitive"
    if pname != "Wire_Pin" and pname != "Primitive":
        print("Instance:", ni.getName(), pname)

print("\n--- package{sch} arcs ---")
for ai in pkg.getArcs():
    h = ai.getHeadPortInst().getNodeInst().getName()
    t = ai.getTailPortInst().getNodeInst().getName()
    print("Arc:", ai.getName(), "%s -> %s" % (h, t))

top_pkg = lib.findNodeProto("Top_package{sch}")
print("\n--- Top_package{sch} arcs ---")
for ai in top_pkg.getArcs():
    h = ai.getHeadPortInst().getNodeInst().getName()
    t = ai.getTailPortInst().getNodeInst().getName()
    print("Arc:", ai.getName(), "%s -> %s" % (h, t))
