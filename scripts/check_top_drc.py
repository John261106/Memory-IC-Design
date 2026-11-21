# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.util import ArrayList
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top = lib.findNodeProto("Top{lay}")
print("=== Checking DRC on Top{lay} ===")
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

logger = ErrorLogger()
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, top, None, None, None, None, prefs, mode, False])
        break
print("Quick DRC: errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))

errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top, errs, None, mode, False)
print("Hierarchical DRC: errors=%d" % len(errs))
for i in range(min(15, len(errs))):
    print("  Hier DRC Error %d: %s" % (i+1, errs.get(i)))

java.lang.System.exit(0)
