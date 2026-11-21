from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

buf = lib.findNodeProto("buffer{sch}")
print("=== buffer{sch} Arcs ===")
ait = buf.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst()
    t = a.getTailPortInst()
    print("  Arc %s: (%s.%s) -> (%s.%s)" % (
        a.getName(),
        h.getNodeInst().getName(), h.getPortProto().getName(),
        t.getNodeInst().getName(), t.getPortProto().getName()))

java.lang.System.exit(0)
