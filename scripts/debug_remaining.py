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

import sys
sys.path.append("scripts")
from test_top_generator import test_build

# Inspect DRC errors in Top{lay}
top_lay = lib.findNodeProto("Top{lay}")
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, top_lay, None, None, None, None, prefs, mode, False])
        break

lit = logger.getLogs()
while lit.hasNext():
    log = lit.next()
    msg = log.getMessageString()
    if "Spacing (layer 'Metal-3')" in msg or "Spacing (layer 'Metal-5')" in msg:
        print("MATCH:", msg)
        # Find the objects
        for geom in [log.findGeometries(None, None, None, None)]:
            pass
