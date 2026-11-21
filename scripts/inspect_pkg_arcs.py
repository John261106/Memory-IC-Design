from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

pkg = lib.findNodeProto("package{sch}")
print("=== package{sch} Exports ===")
eit = pkg.getExports()
while eit.hasNext():
    exp = eit.next()
    print("  Export: '%s', port=%s, char=%s" % (exp.getName(), exp.getOriginalPort().getPortProto().getName(), exp.getCharacteristic()))

print("\n=== package{sch} Arcs ===")
ait = pkg.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst()
    t = a.getTailPortInst()
    print("  Arc %s: (%s.%s) -> (%s.%s)" % (
        a.getName(),
        h.getNodeInst().getName(), h.getPortProto().getName(),
        t.getNodeInst().getName(), t.getPortProto().getName()))

pkg_ic = lib.findNodeProto("package{ic}")
if pkg_ic:
    print("\n=== package{ic} Exports ===")
    eit = pkg_ic.getExports()
    while eit.hasNext():
        exp = eit.next()
        print("  Export: '%s', port=%s" % (exp.getName(), exp.getOriginalPort().getPortProto().getName()))

java.lang.System.exit(0)
