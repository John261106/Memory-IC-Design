from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

pkg = lib.findNodeProto("package{sch}")
print("=== PACKAGE{SCH} EXPORTS ===")
eit = pkg.getExports()
while eit.hasNext():
    exp = eit.next()
    print("Export:", exp.getName(), "on port:", exp.getOriginalPort().getNodeInst().getName(), exp.getOriginalPort().getPortProto().getName())

print("\n=== PACKAGE{SCH} NODES AND COMPONENTS ===")
for ni in pkg.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else "Primitive"
    if pname in ["Resistor", "Inductor", "Capacitor"]:
        # print component and its ports
        val = None
        vit = ni.getVariables()
        while vit.hasNext():
            v = vit.next()
            val = "%s=%s" % (v.getKey().getName(), v.getObject())
        print("Component %s: %s, val=%s" % (ni.getName(), pname, val))

print("\n=== PACKAGE{SCH} NETS ===")
# build net connectivity
# find all connected components per net
visited_arcs = set()
for ai in pkg.getArcs():
    h = ai.getHeadPortInst()
    t = ai.getTailPortInst()
    print("Net %s: %s[%s] <--> %s[%s]" % (ai.getName(), h.getNodeInst().getName(), h.getPortProto().getName(), t.getNodeInst().getName(), t.getPortProto().getName()))
