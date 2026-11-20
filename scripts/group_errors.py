from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger
import java.lang.Double

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")
top_lay = lib.findNodeProto("Top{lay}")

drc_proto = Technology.findTechnology("generic").findNodeProto("DRC-Node")
to_delete = []
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getProto() == drc_proto:
        to_delete.append(n)
for n in to_delete:
    n.kill()

logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, top_lay, None, None, None, None, prefs, mode, False])
        break

lit = logger.getLogs()
groups = {}
while lit.hasNext():
    log = lit.next()
    msg = log.getMessageString()
    # simplify key
    key = msg.split(":")[0] + " - " + msg.split("[rule")[0][-30:]
    groups.setdefault(key, []).append(msg)

for k, v in sorted(groups.items()):
    print("%d errors: %s" % (len(v), k))
    for m in v[:3]:
        print("    ", m)
