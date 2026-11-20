# Test building Top{lay} without DRC exclusion boxes using the patched jar
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
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

top_lay = lib.findNodeProto("Top{lay}")

# Remove any DRC-Node instances in Top{lay}
drc_proto = Technology.findTechnology("generic").findNodeProto("DRC-Node")
to_delete = []
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getProto() == drc_proto:
        to_delete.append(n)

print("Found %d DRC-Node instances to delete" % len(to_delete))
for n in to_delete:
    n.kill()

# Now run DRC
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, top_lay, None, None, None, None, prefs, mode, False])
        break

print("WITHOUT DRC-Node: Quick DRC errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))
lit = logger.getLogs()
while lit.hasNext():
    print("  DRC Log: %s" % lit.next().getMessageString())

from java.util import ArrayList
errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, errs, None, mode, False)
print("WITHOUT DRC-Node: Full Hierarchical DRC errors=%d" % len(errs))
for e in errs:
    print("  Hier DRC Error: %s" % e)
